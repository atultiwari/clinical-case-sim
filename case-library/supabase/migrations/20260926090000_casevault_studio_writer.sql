-- Case Vault: the Case Studio's writer role (SPEC §8, PLAN L1.5).
--
-- Case Studio v2 records Atul's own review decisions and per-figure production
-- decisions. It writes through a second connection whose login role is a member
-- of casevault_studio_writer, and each write switches to this role inside its
-- own transaction. The role can do exactly this and nothing else:
--
--   * read the rows it validates against (the case version, its facts, ledger,
--     reports, consult notes and figures, and the review tables);
--   * insert a Studio review batch ('studio-<YYYY-MM-DD>-<username>[-n]'), and add a
--     case version to the list of an open Studio batch (applied_at is null);
--   * insert review decisions into an open Studio batch;
--   * set a figure's production decision: production_decision, masked_path,
--     decided_by and decided_at on casevault.media, and no other column.
--
-- It cannot delete anything, cannot touch any other table or column, and can run
-- only casevault.case_version_status (which the frozen-content trigger on media
-- and the policies below call) and casevault.review_target_case_version. Claude still applies review decisions to the content through the MCP
-- (SPEC §7.3); the Studio only records them.
--
-- The role has no login. Atul creates a login role that is a member of it, with a
-- password that never enters a migration or a chat (case-library/studio/README.md).

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'casevault_studio_writer') then
    create role casevault_studio_writer nologin noinherit;
  end if;
end
$$;

-- postgres (the owner, and the connector's user) may act as the writer, e.g. in
-- tests; since Postgres 16 creating a role does not grant this.
grant casevault_studio_writer to postgres;

grant usage on schema casevault to casevault_studio_writer;

-- Reads, for validation inside the write transaction.
grant select on
  casevault.case_version,
  casevault.fact,
  casevault.report,
  casevault.consult_note,
  casevault.synthetic_ledger,
  casevault.media,
  casevault.review_batch,
  casevault.review_decision
to casevault_studio_writer;

-- Writes: column-level, so nothing else can be set.
grant insert (id, case_version_ids) on casevault.review_batch to casevault_studio_writer;
grant update (case_version_ids) on casevault.review_batch to casevault_studio_writer;
grant insert (batch_id, target_table, target_id, decision, edited, note, decided_by)
  on casevault.review_decision to casevault_studio_writer;
grant usage on sequence casevault.review_decision_id_seq to casevault_studio_writer;
grant update (production_decision, masked_path, decided_by, decided_at)
  on casevault.media to casevault_studio_writer;

-- The case version a review decision's target row belongs to, or null when the
-- row does not exist. target_id is the ledger row's uuid, or
-- '<case version>/<row id>' for the other reviewable tables (studio/src/lib/review-input.ts).
-- It runs as the caller, so the writer needs only its select grants.
create function casevault.review_target_case_version(p_target_table text, p_target_id text)
returns text
language sql
stable
set search_path = ''
as $$
  select case p_target_table
    when 'synthetic_ledger' then
      (select l.case_version_id from casevault.synthetic_ledger l where l.id::text = p_target_id)
    when 'fact' then
      (select f.case_version_id from casevault.fact f
        where f.case_version_id || '/' || f.id = p_target_id)
    when 'report' then
      (select r.case_version_id from casevault.report r
        where r.case_version_id || '/' || r.id = p_target_id)
    when 'consult_note' then
      (select n.case_version_id from casevault.consult_note n
        where n.case_version_id || '/' || n.id = p_target_id)
  end
$$;

-- The frozen-content trigger on media calls this (it only reads).
grant execute on function casevault.case_version_status(text) to casevault_studio_writer;
revoke execute on function casevault.review_target_case_version(text, text) from public;
grant execute on function casevault.review_target_case_version(text, text)
  to casevault_studio_writer;

-- Row-level security: every casevault table has it on with no client policies.

do $$
declare
  v_table text;
begin
  foreach v_table in array array['case_version', 'fact', 'report', 'consult_note',
                                 'synthetic_ledger', 'media', 'review_batch',
                                 'review_decision'] loop
    execute format(
      'create policy casevault_studio_writer_select on casevault.%I '
      'for select to casevault_studio_writer using (true)', v_table);
  end loop;
end
$$;

create policy casevault_studio_writer_insert on casevault.review_batch
  for insert to casevault_studio_writer
  with check (
    id ~ '^studio-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9_-]{0,31}(-[0-9]{1,4})?$'
    and cardinality(case_version_ids) >= 1
    and pack_path is null and returned_at is null and applied_at is null
  );

create policy casevault_studio_writer_update on casevault.review_batch
  for update to casevault_studio_writer
  using (starts_with(id, 'studio-') and applied_at is null)
  with check (starts_with(id, 'studio-') and applied_at is null
              and cardinality(case_version_ids) >= 1);

create policy casevault_studio_writer_insert on casevault.review_decision
  for insert to casevault_studio_writer
  with check (
    starts_with(batch_id, 'studio-')
    and exists (select 1 from casevault.review_batch b
                where b.id = batch_id and b.applied_at is null)
    and target_table in ('synthetic_ledger', 'report', 'consult_note', 'fact')
    and decision in ('approve', 'edit', 'reject')
    and (decision = 'edit') = (edited is not null)
    and length(btrim(decided_by)) > 0
    -- The target row exists, belongs to a case version listed in the batch, and
    -- that version is still open for review.
    and exists (
      select 1 from casevault.review_batch b
      where b.id = batch_id
        and casevault.review_target_case_version(target_table, target_id)
            = any (b.case_version_ids)
    )
    and casevault.case_version_status(
          casevault.review_target_case_version(target_table, target_id))
        in ('draft', 'in_review')
  );

create policy casevault_studio_writer_update on casevault.media
  for update to casevault_studio_writer
  using (true)
  with check (
    production_decision in ('use', 'mask', 'exclude')
    and (production_decision = 'mask') = (masked_path is not null)
    and decided_by is not null and length(btrim(decided_by)) > 0
    and decided_at is not null
    -- Figures of a frozen version stay decidable (SPEC §9); a retired one does not.
    and casevault.case_version_status(case_version_id) in ('draft', 'in_review', 'frozen')
  );
