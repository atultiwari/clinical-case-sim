-- Case Vault: placeholder_scan (PLAN L0.10).
--
-- The pilot reached review with "[to be set by the reviewer]" in three marrow
-- reports; leak_scan looks only for diagnosis terms. placeholder_scan looks at
-- the text a player can see for reviewer placeholders and authoring notes:
--   "to be set", "set by the reviewer", TBD, TODO, placeholder;
--   square-bracketed instructions ("[insert MCV]", "[to be confirmed]");
--   authoring notes ("(Generator ...", "(Better: ...", "(Keep for ...").
-- Ledger rows of tier 'reviewer' are placeholders by design until the review
-- fills them, and are not scanned. export_blockers now lists what it finds.

-- The first placeholder in a text with up to 40 characters either side, or null.
create function casevault.placeholder_snippet(p_text text)
returns text
language plpgsql
immutable
set search_path = ''
as $$
declare
  v_pattern constant text :=
    'to be set|set by the reviewer|\mTBD\M|\mTODO\M|\mplaceholders?\M'
    || '|\[[^]]*\m(to be|tbd|todo|fill|add|insert|enter|replace|confirm|reviewer|curator)\M[^]]*\]'
    || '|\((generator\M|better\s*:|keep for\M)';
  v_pos int := regexp_instr(coalesce(p_text, ''), v_pattern, 1, 1, 0, 'i');
  v_len int;
begin
  if v_pos = 0 then
    return null;
  end if;
  v_len := regexp_instr(p_text, v_pattern, 1, 1, 1, 'i') - v_pos;
  return btrim(substr(p_text, greatest(1, v_pos - 40), least(v_len, 40) + 80));
end
$$;

create function casevault.placeholder_scan(p_case_version_id text)
returns table (location text, row_id text, snippet text)
language sql
stable
set search_path = ''
as $$
  with texts (location, row_id, body) as (
    select 'case.display_title', c.id, c.display_title
    from casevault.case_version v join casevault."case" c on c.id = v.case_id
    where v.id = p_case_version_id
    union all
    select 'case_version.vignette', id, vignette
    from casevault.case_version where id = p_case_version_id
    union all
    select 'case_version.opening_statement_lay', id, opening_statement_lay
    from casevault.case_version where id = p_case_version_id
    union all
    select 'fact.lay_text', id, lay_text
    from casevault.fact where case_version_id = p_case_version_id and release <> 'never'
    union all
    select 'synthetic_ledger.' || col, id::text, body
    from casevault.synthetic_ledger l,
         lateral (values ('value', l.value::text), ('release_text', l.release_text),
                         ('lay_text', l.lay_text)) t (col, body)
    where l.case_version_id = p_case_version_id and l.tier <> 'reviewer'
      and casevault.is_live(l.review_status)
    union all
    select 'report.' || col, id, body
    from casevault.report r,
         lateral (values ('report_text', r.report_text), ('impression', r.impression),
                         ('status_line', r.status_line),
                         ('findings', array_to_string(r.findings, ' | '))) t (col, body)
    where r.case_version_id = p_case_version_id and casevault.is_live(r.review_status)
    union all
    select 'consult_note.' || col, id, body
    from casevault.consult_note n,
         lateral (values ('note_text', n.note_text),
                         ('recommendations', array_to_string(n.recommendations, ' | ')))
           t (col, body)
    where n.case_version_id = p_case_version_id and casevault.is_live(n.review_status)
  )
  select location, row_id, snippet
  from texts, lateral (select casevault.placeholder_snippet(body) as snippet) s
  where snippet is not null
  order by location collate "C", row_id collate "C"
$$;

-- As in 20260925112550_casevault_export.sql, with the placeholder line added.
create or replace function casevault.export_blockers(p_cv text)
returns setof text
language sql
stable
set search_path = ''
as $$
  select format('case version %s does not exist', p_cv)
  where not exists (select 1 from casevault.case_version where id = p_cv)
  union all
  select format('case version is %s, not frozen', status)
  from casevault.case_version where id = p_cv and status <> 'frozen'
  union all
  select format('coverage: %s open (%s)', count(*),
                string_agg(concat_ws('/', item_id, component_id, 'd' || day), ', '))
  from (select * from casevault.coverage_gaps(p_cv) limit 20) g
  having count(*) > 0
  union all
  select format('%s: %s rows still pending review', t, n)
  from (
    select 'fact' as t, count(*) as n from casevault.fact
    where case_version_id = p_cv and review_status = 'pending'
    union all
    select 'synthetic_ledger', count(*) from casevault.synthetic_ledger
    where case_version_id = p_cv and review_status = 'pending'
    union all
    select 'report', count(*) from casevault.report
    where case_version_id = p_cv and review_status = 'pending'
    union all
    select 'consult_note', count(*) from casevault.consult_note
    where case_version_id = p_cv and review_status = 'pending'
  ) pending
  where n > 0
  union all
  select format('check %s: %s', check_name, detail) from casevault.check_consistency(p_cv)
  union all
  select format('leak: "%s" in %s %s', term, location, row_id) from casevault.leak_scan(p_cv)
  union all
  select format('placeholder: %s %s: "%s"', location, row_id, snippet)
  from casevault.placeholder_scan(p_cv)
  union all
  select 'ground truth is missing'
  where not exists (select 1 from casevault.ground_truth where case_version_id = p_cv)
$$;

revoke all on function casevault.placeholder_snippet(text) from anon, authenticated, public;
revoke all on function casevault.placeholder_scan(text) from anon, authenticated, public;
grant execute on function
  casevault.placeholder_snippet(text),
  casevault.placeholder_scan(text)
to casevault_reader;
