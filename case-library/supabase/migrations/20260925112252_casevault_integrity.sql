-- Case Vault schema 0.3: integrity rules (SPEC §10.2 notes, invariant 4, PLAN L0.3).
--   1. Frozen case versions are immutable, except figure production decisions.
--   2. synthetic_ledger is insert-only, with one-time review and supersession.
--   3. One live ledger row per case version, target and day (nulls not distinct).

-- ---------------------------------------------------------------------------
-- 1. Frozen case versions
-- ---------------------------------------------------------------------------

create function casevault.case_version_status(p_case_version_id text)
returns text
language sql
stable
set search_path = ''
as $$
  select status from casevault.case_version where id = p_case_version_id
$$;

-- Content rows of a frozen or retired version cannot be inserted, changed or
-- deleted. Media keeps four columns open: Atul's production decision for each
-- figure, recorded before the store release (SPEC §9), which then exports a
-- new bundle revision.
create function casevault.guard_frozen_content()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  v_row record := coalesce(new, old);
  v_status text := casevault.case_version_status(v_row.case_version_id);
  v_old jsonb;
  v_new jsonb;
  c_decision_columns constant text[] :=
    array['production_decision', 'masked_path', 'decided_by', 'decided_at'];
begin
  if v_status not in ('frozen', 'retired') then
    return v_row;
  end if;

  if tg_op = 'UPDATE' and tg_table_name = 'media' then
    v_old := to_jsonb(old) - c_decision_columns;
    v_new := to_jsonb(new) - c_decision_columns;
    if v_old = v_new then
      return new;
    end if;
  end if;

  raise exception 'casevault.%: case version % is %, so its content cannot change (%)',
    tg_table_name, v_row.case_version_id, v_status, tg_op
    using errcode = 'restrict_violation',
          hint = 'Create a new case version instead.';
end
$$;

do $$
declare
  t text;
begin
  foreach t in array array['fact', 'raw_material', 'media', 'gap', 'report', 'consult_note',
                           'ground_truth', 'path_analysis', 'test_utility'] loop
    execute format(
      'create trigger guard_frozen_content before insert or update or delete on casevault.%I '
      'for each row execute function casevault.guard_frozen_content()', t);
  end loop;
end
$$;

-- The version row itself: draft and in_review move freely between each other
-- and to frozen or retired; frozen can only become retired; retired is final.
-- Once frozen, no other column changes.
create function casevault.guard_case_version()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if tg_op = 'DELETE' then
    if old.status in ('frozen', 'retired') then
      raise exception 'casevault.case_version: % is % and cannot be deleted', old.id, old.status
        using errcode = 'restrict_violation';
    end if;
    return old;
  end if;

  if old.status = 'retired' then
    raise exception 'casevault.case_version: % is retired and cannot change', old.id
      using errcode = 'restrict_violation';
  end if;

  if old.status = 'frozen' and (
       new.status <> 'retired'
       or (to_jsonb(new) - 'status') <> (to_jsonb(old) - 'status')) then
    raise exception 'casevault.case_version: % is frozen; it can only be retired', old.id
      using errcode = 'restrict_violation',
            hint = 'Create a new case version instead.';
  end if;

  return new;
end
$$;

create trigger guard_case_version
  before update or delete on casevault.case_version
  for each row execute function casevault.guard_case_version();

-- ---------------------------------------------------------------------------
-- 2. Synthetic ledger: insert-only, one-time review, supersession
-- ---------------------------------------------------------------------------

create function casevault.guard_ledger()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  c_review_columns constant text[] :=
    array['review_status', 'reviewed_by', 'reviewed_at', 'review_note'];
begin
  if tg_op = 'DELETE' then
    raise exception 'casevault.synthetic_ledger is append-only; row % cannot be deleted', old.id
      using errcode = 'restrict_violation',
            hint = 'Insert a superseding row instead.';
  end if;

  if tg_op = 'INSERT' then
    if new.review_status in ('rejected', 'superseded') then
      raise exception 'casevault.synthetic_ledger: a new row cannot start as %', new.review_status
        using errcode = 'check_violation';
    end if;
    if new.review_status = 'edited' and new.supersedes is null then
      raise exception 'casevault.synthetic_ledger: an edited row must supersede the row it edits'
        using errcode = 'check_violation';
    end if;
    return new;
  end if;

  -- UPDATE: only the review columns may change.
  if (to_jsonb(new) - c_review_columns) <> (to_jsonb(old) - c_review_columns) then
    raise exception 'casevault.synthetic_ledger: row % can change only its review fields', old.id
      using errcode = 'restrict_violation',
            hint = 'Insert a superseding row instead.';
  end if;

  if old.review_status = 'pending'
     and new.review_status in ('approved', 'rejected', 'superseded') then
    if new.review_status <> 'superseded'
       and (new.reviewed_by is null or new.reviewed_at is null) then
      raise exception 'casevault.synthetic_ledger: a review of row % needs reviewed_by and reviewed_at', old.id
        using errcode = 'check_violation';
    end if;
    return new;
  end if;

  if old.review_status in ('approved', 'edited')
     and new.review_status = 'superseded'
     and (new.reviewed_by, new.reviewed_at, new.review_note)
         is not distinct from (old.reviewed_by, old.reviewed_at, old.review_note) then
    return new;
  end if;

  raise exception 'casevault.synthetic_ledger: row % cannot go from % to %',
    old.id, old.review_status, new.review_status
    using errcode = 'restrict_violation';
end
$$;

create trigger guard_ledger
  before insert or update or delete on casevault.synthetic_ledger
  for each row execute function casevault.guard_ledger();

-- A row marked superseded must be replaced in the same transaction by a row
-- for the same case version, target and day that names it in `supersedes`.
-- Checked at commit, because the old row has to leave the live set before the
-- unique index lets the replacement in.
create function casevault.check_supersession()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if not exists (
    select 1
    from casevault.synthetic_ledger r
    where r.supersedes = new.id
      and r.case_version_id = new.case_version_id
      and r.target = new.target
      and r.day_bucket is not distinct from new.day_bucket
      and r.xmin = pg_current_xact_id()::xid
  ) then
    raise exception 'casevault.synthetic_ledger: row % was superseded without a replacement in the same transaction', new.id
      using errcode = 'integrity_constraint_violation';
  end if;
  return null;
end
$$;

create constraint trigger check_supersession
  after update of review_status on casevault.synthetic_ledger
  deferrable initially deferred
  for each row
  when (new.review_status = 'superseded' and old.review_status <> 'superseded')
  execute function casevault.check_supersession();

-- A replacement must point at a row of the same case version, target and day.
alter table casevault.synthetic_ledger
  add constraint ledger_supersedes_not_self check (supersedes is distinct from id);

create function casevault.check_replacement_target()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if not exists (
    select 1
    from casevault.synthetic_ledger o
    where o.id = new.supersedes
      and o.case_version_id = new.case_version_id
      and o.target = new.target
      and o.day_bucket is not distinct from new.day_bucket
  ) then
    raise exception 'casevault.synthetic_ledger: row % supersedes % , which is not the same case version, target and day', new.id, new.supersedes
      using errcode = 'foreign_key_violation';
  end if;
  return new;
end
$$;

create trigger check_replacement_target
  before insert on casevault.synthetic_ledger
  for each row
  when (new.supersedes is not null)
  execute function casevault.check_replacement_target();

-- ---------------------------------------------------------------------------
-- 3. One live row per case version, target and day
-- ---------------------------------------------------------------------------

create unique index ledger_live on casevault.synthetic_ledger (case_version_id, target, day_bucket)
  nulls not distinct
  where review_status in ('pending', 'approved', 'edited');

revoke all on all functions in schema casevault from anon, authenticated, public;
