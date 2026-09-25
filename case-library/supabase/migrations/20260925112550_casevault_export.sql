-- Case Vault schema 0.3: bundle export (SPEC §7.5, §10.5, invariant 2; PLAN L0.3).
--
-- export_blockers(case version) lists every reason the version cannot be
-- exported yet; export_bundle refuses while any remains. A bundle holds reviewed
-- rows only, without the curation provenance, in a fixed order, so the same
-- case, revision and catalogue version always give the same JSON. The file
-- itself is written by scripts/export_bundle.py with an RFC 8785 serializer.

create function casevault.export_blockers(p_cv text)
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
  select 'ground truth is missing'
  where not exists (select 1 from casevault.ground_truth where case_version_id = p_cv)
$$;

-- A row as the bundle carries it: curation provenance and internal columns removed.
create function casevault.bundle_row(p_row jsonb)
returns jsonb
language sql
immutable
set search_path = ''
as $$
  select p_row - array[
    'case_version_id', 'generator', 'skill_version', 'rationale', 'confidence', 'checks',
    'review_status', 'reviewed_by', 'reviewed_at', 'review_note', 'priority', 'judgement_call',
    'supersedes', 'created_at', 'decided_by', 'decided_at']
$$;

create function casevault.bundle_rows(p_cv text)
returns jsonb
language sql
stable
set search_path = ''
as $$
  select jsonb_build_object(
    'facts', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(f)) order by f.id)
      from casevault.fact f
      where f.case_version_id = p_cv and f.review_status in ('verified', 'corrected')), '[]'),
    'ledger', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(l))
                       order by l.target, l.day_bucket nulls first, l.id)
      from casevault.synthetic_ledger l
      where l.case_version_id = p_cv and l.review_status in ('approved', 'edited')), '[]'),
    'reports', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(r)) order by r.id)
      from casevault.report r
      where r.case_version_id = p_cv and r.review_status in ('approved', 'edited')), '[]'),
    'consult_notes', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(n)) order by n.id)
      from casevault.consult_note n
      where n.case_version_id = p_cv and n.review_status in ('approved', 'edited')), '[]'),
    'raw_material', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(m)) order by m.id)
      from casevault.raw_material m where m.case_version_id = p_cv), '[]'),
    'media', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(m)) order by m.id)
      from casevault.media m where m.case_version_id = p_cv), '[]'),
    'gaps', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(g)) order by g.id)
      from casevault.gap g where g.case_version_id = p_cv), '[]'),
    'test_utility', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(u)) order by u.test_item_id)
      from casevault.test_utility u where u.case_version_id = p_cv), '[]'),
    'path_analysis', coalesce((
      select jsonb_agg(casevault.bundle_row(to_jsonb(p)) order by p.path_id)
      from casevault.path_analysis p where p.case_version_id = p_cv), '[]'),
    'ground_truth', coalesce((
      select casevault.bundle_row(to_jsonb(g))
      from casevault.ground_truth g where g.case_version_id = p_cv), '{}'))
$$;

create function casevault.export_bundle(p_cv text, p_revision int, p_catalogue_version int)
returns jsonb
language plpgsql
stable
set search_path = ''
as $$
declare
  v_blockers text[] := array(select casevault.export_blockers(p_cv));
  v_head jsonb;
begin
  if cardinality(v_blockers) > 0 then
    raise exception 'casevault.export_bundle: % cannot be exported yet', p_cv
      using errcode = 'object_not_in_prerequisite_state',
            detail = array_to_string(v_blockers, E'\n');
  end if;
  if p_revision is null or p_revision < 1 or p_catalogue_version is null or p_catalogue_version < 0 then
    raise exception 'casevault.export_bundle needs a revision of 1 or more and a catalogue version'
      using errcode = 'invalid_parameter_value';
  end if;

  select jsonb_build_object(
    'bundle_id', v.id || '.r' || p_revision,
    'schema_version', v.schema_version,
    'catalogue_version', p_catalogue_version,
    'case', jsonb_strip_nulls(jsonb_build_object(
      'slug', c.slug, 'display_title', c.display_title, 'display_tags', to_jsonb(c.display_tags),
      'specialty', c.specialty, 'difficulty', c.difficulty, 'est_minutes', c.est_minutes,
      'lab_profile', c.lab_profile)),
    'source', case when s.id is null then null else jsonb_strip_nulls(jsonb_build_object(
      'citation', concat_ws('. ', s.title, s.journal, extract(year from s.published)::text),
      'doi', s.doi, 'pmcid', s.pmcid, 'url', s.url, 'licence', s.licence,
      'attribution', s.attribution,
      'production_ok', s.production_ok, 'public_release_ok', s.public_release_ok)) end,
    'clock', jsonb_strip_nulls(jsonb_build_object(
      'day_0', v.day0_date, 'day_0_label', v.day0_label)),
    'vignette', v.vignette,
    'opening_statement_lay', v.opening_statement_lay)
  into v_head
  from casevault.case_version v
  join casevault."case" c on c.id = v.case_id
  left join casevault.source_article s on s.id = c.source_id
  where v.id = p_cv;

  return v_head || casevault.bundle_rows(p_cv);
end
$$;

revoke all on all functions in schema casevault from anon, authenticated, public;
