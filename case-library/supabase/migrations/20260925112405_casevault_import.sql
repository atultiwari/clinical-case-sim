-- Case Vault schema 0.3: rule table and case import (SPEC §4.4, §6.5, §6.6; PLAN L0.3).
--
-- casevault.value_rule holds the formulas and physiology checks. Rows are loaded
-- with the catalogue (L0.4), because they name component ids.
--
-- casevault.import_case_json(doc, generator, skill_version) loads a gold case
-- file (the pilot's draft format) as a new draft case version. Series are
-- expanded to one fact per day, with ids '<series id>.d<day>'.

create table casevault.value_rule (
  id text primary key,
  kind text not null check (kind in ('ratio','difference','not_above','sum_equals')),
  target text not null,
  inputs text[] not null check (cardinality(inputs) >= 1),
  factor numeric not null default 1,
  tolerance_pct numeric not null default 2 check (tolerance_pct >= 0),
  formula text not null,
  check (kind not in ('ratio','not_above') or cardinality(inputs) = case kind when 'ratio' then 2 else 1 end)
);
comment on table casevault.value_rule is
  'ratio: target = factor * inputs[1] / inputs[2]. difference: target = inputs[1] - sum(inputs[2:]). '
  'Both are derivable (compute_derived) and checked (check_consistency). '
  'not_above: target <= inputs[1]. sum_equals: sum(inputs) = target within tolerance_pct.';

alter table casevault.value_rule enable row level security;
revoke all on casevault.value_rule from anon, authenticated;

-- ---------------------------------------------------------------------------
-- Small helpers
-- ---------------------------------------------------------------------------

-- A JSON scalar as text: strings unquoted, numbers and booleans as written.
create function casevault.json_text(p jsonb)
returns text
language sql
immutable
set search_path = ''
as $$
  select case jsonb_typeof(p) when 'null' then null when 'string' then p #>> '{}' else p::text end
$$;

create function casevault.json_num(p jsonb)
returns numeric
language sql
immutable
set search_path = ''
as $$
  select case when jsonb_typeof(p) = 'number' then (p #>> '{}')::numeric end
$$;

create function casevault.json_text_array(p jsonb)
returns text[]
language sql
immutable
set search_path = ''
as $$
  select case when jsonb_typeof(p) = 'array'
              then array(select jsonb_array_elements_text(p))
              else '{}'::text[] end
$$;

-- ---------------------------------------------------------------------------
-- Import, one section per function
-- ---------------------------------------------------------------------------

create function casevault.import_source(p_source jsonb)
returns uuid
language plpgsql
set search_path = ''
as $$
declare
  v_id uuid;
begin
  if p_source is null then
    return null;
  end if;
  insert into casevault.source_article
    (pmcid, doi, title, journal, published, licence, url, attribution,
     production_ok, public_release_ok)
  values
    (p_source ->> 'pmcid', p_source ->> 'doi', p_source ->> 'title', p_source ->> 'journal',
     (p_source ->> 'published')::date, p_source ->> 'licence', p_source ->> 'url',
     p_source ->> 'attribution',
     coalesce((p_source ->> 'production_ok')::boolean, false),
     coalesce((p_source ->> 'public_release_ok')::boolean, false))
  returning id into v_id;
  return v_id;
end
$$;

create function casevault.import_history_facts(
  p_cv text, p_facts jsonb, p_generator text, p_skill_version text)
returns int
language sql
set search_path = ''
as $$
  with ins as (
    insert into casevault.fact
      (case_version_id, id, category, item, catalogue_ref, released_by, value, value_num, unit,
       ref_range, flag, day, kind, origin, reveals_dx, pivotal, release, release_condition,
       release_text, lay_text, source_locator, generator, skill_version)
    select p_cv, f ->> 'id', f ->> 'category', f ->> 'item', f ->> 'catalogue_ref',
           casevault.json_text_array(f -> 'released_by'),
           casevault.json_text(f -> 'value'), casevault.json_num(f -> 'value'),
           nullif(f ->> 'unit', ''), f ->> 'ref_range', f ->> 'flag', (f ->> 'day')::int,
           coalesce(f ->> 'kind', 'raw'), 'article',
           coalesce((f ->> 'reveals_dx')::boolean, false), coalesce((f ->> 'pivotal')::boolean, false),
           f ->> 'release', f -> 'release_condition', f ->> 'release_text', f ->> 'lay_text',
           f ->> 'source_locator', p_generator, p_skill_version
    from jsonb_array_elements(coalesce(p_facts, '[]')) f
    returning 1
  )
  select count(*)::int from ins
$$;

-- Lab results: single results as they are, series expanded to one row per point.
create function casevault.import_lab_facts(
  p_cv text, p_single jsonb, p_series jsonb, p_generator text, p_skill_version text)
returns int
language sql
set search_path = ''
as $$
  with rows as (
    select r ->> 'id' as id, r as meta, r -> 'value' as value, (r ->> 'day')::int as day,
           r ->> 'flag' as flag
    from jsonb_array_elements(coalesce(p_single, '[]')) r
    union all
    select s ->> 'id' || '.d' || (p ->> 'day'), s, p -> 'value', (p ->> 'day')::int, p ->> 'flag'
    from jsonb_array_elements(coalesce(p_series, '[]')) s,
         jsonb_array_elements(s -> 'points') p
  ),
  ins as (
    insert into casevault.fact
      (case_version_id, id, category, item, catalogue_ref, released_by, code_system, code,
       value, value_num, unit, ref_range, flag, day, kind, origin, reveals_dx, pivotal,
       release, release_text, source_locator, generator, skill_version)
    select p_cv, r.id, coalesce(r.meta ->> 'category', 'lab'), r.meta ->> 'item',
           r.meta ->> 'catalogue_ref', casevault.json_text_array(r.meta -> 'released_by'),
           r.meta -> 'code' ->> 'system', r.meta -> 'code' ->> 'code',
           casevault.json_text(r.value), casevault.json_num(r.value),
           nullif(r.meta ->> 'unit', ''), r.meta ->> 'ref_range', r.flag, r.day,
           coalesce(r.meta ->> 'kind', 'raw'), 'article',
           coalesce((r.meta ->> 'reveals_dx')::boolean, false),
           coalesce((r.meta ->> 'pivotal')::boolean, false),
           coalesce(r.meta ->> 'release', 'chart'), r.meta ->> 'release_text',
           r.meta ->> 'source_locator', p_generator, p_skill_version
    from rows r
    returning 1
  )
  select count(*)::int from ins
$$;

create function casevault.import_materials(p_cv text, p_doc jsonb)
returns void
language plpgsql
set search_path = ''
as $$
begin
  insert into casevault.raw_material
    (case_version_id, id, test, test_item_id, release, day, findings, media, note, source_locator)
  select p_cv, r ->> 'id', r ->> 'test', r ->> 'test_item_id', r ->> 'release',
         (r ->> 'day')::int, r ->> 'findings', casevault.json_text_array(r -> 'media'),
         r ->> 'note', r ->> 'source_locator'
  from jsonb_array_elements(coalesce(p_doc -> 'raw_material', '[]')) r;

  -- Figures start with their own flags off until Atul sets them (SPEC §9).
  insert into casevault.media
    (case_version_id, id, figure, specimen, stain, file_path, redacted_caption, licence,
     production_ok, public_release_ok, has_annotations, raw_fact_id)
  select p_cv, m ->> 'id', m ->> 'figure', m ->> 'specimen', m ->> 'stain', m ->> 'file_path',
         m ->> 'redacted_caption', m ->> 'licence',
         coalesce((m ->> 'production_ok')::boolean, false),
         coalesce((m ->> 'public_release_ok')::boolean, false),
         coalesce((m ->> 'has_annotations')::boolean, false), m ->> 'raw_fact_id'
  from jsonb_array_elements(coalesce(p_doc -> 'media', '[]')) m;

  insert into casevault.gap (case_version_id, id, item, guidance, review_required, auto_generate)
  select p_cv, g ->> 'id', g ->> 'item', g ->> 'guidance',
         coalesce((g ->> 'review_required')::boolean, false),
         coalesce((g ->> 'auto_generate')::boolean, true)
  from jsonb_array_elements(coalesce(p_doc -> 'gaps', '[]')) g;
end
$$;

-- Accepts the schema 0.2 key names used by the pilot draft and the 0.3 names.
create function casevault.import_ground_truth(p_cv text, p_gt jsonb)
returns void
language sql
set search_path = ''
as $$
  insert into casevault.ground_truth
    (case_version_id, final_dx, accepted_differential, red_herrings, key_discriminators, rubric,
     must_do, must_not_do, efficient_path, teaching_points, treatment_given, outcome)
  select p_cv,
         coalesce(p_gt -> 'final_dx', p_gt -> 'final_diagnosis')
           || jsonb_strip_nulls(jsonb_build_object('secondary_findings', p_gt -> 'secondary_findings')),
         p_gt -> 'accepted_differential', p_gt -> 'red_herrings', p_gt -> 'key_discriminators',
         coalesce(p_gt -> 'rubric', p_gt -> 'diagnosis_rubric_anchors'),
         p_gt -> 'must_do', p_gt -> 'must_not_do', p_gt -> 'efficient_path',
         p_gt -> 'teaching_points', p_gt ->> 'treatment_given', p_gt ->> 'outcome'
  where p_gt is not null
$$;

create function casevault.import_case_json(p_doc jsonb, p_generator text, p_skill_version text)
returns text
language plpgsql
set search_path = ''
as $$
declare
  v_case_id text := p_doc ->> 'case_id';
  v_version int := coalesce((p_doc ->> 'version')::int, 1);
  v_cv text := v_case_id || '@v' || v_version;
  v_source uuid;
  v_case jsonb := coalesce(p_doc -> 'case', '{}');
begin
  if v_case_id is null or p_generator is null or p_skill_version is null then
    raise exception 'import_case_json needs case_id, a generator and a skill version'
      using errcode = 'invalid_parameter_value';
  end if;

  if not exists (select 1 from casevault."case" where id = v_case_id) then
    v_source := casevault.import_source(p_doc -> 'source');
    insert into casevault."case"
      (id, source_id, source_type, slug, display_title, display_tags, specialty, difficulty,
       est_minutes, lab_profile)
    values
      (v_case_id, v_source, case when v_source is null then 'de_novo' else 'case_report' end,
       v_case ->> 'slug', v_case ->> 'display_title', casevault.json_text_array(v_case -> 'display_tags'),
       v_case ->> 'specialty', v_case ->> 'difficulty', (v_case ->> 'est_minutes')::int,
       v_case -> 'lab_profile');
  end if;

  -- Always a new draft, whatever status the file claims.
  insert into casevault.case_version
    (id, case_id, version, vignette, opening_statement_lay, day0_date, day0_label,
     curated_by, skill_version, curated_at)
  values
    (v_cv, v_case_id, v_version, p_doc ->> 'vignette', p_doc ->> 'opening_statement_lay',
     (p_doc -> 'clock' ->> 'day_0')::date, p_doc -> 'clock' ->> 'day_0_label',
     'curator', p_skill_version, now());

  perform casevault.import_history_facts(v_cv, p_doc -> 'facts', p_generator, p_skill_version);
  perform casevault.import_lab_facts(
    v_cv, p_doc -> 'single_results', p_doc -> 'series', p_generator, p_skill_version);
  perform casevault.import_materials(v_cv, p_doc);
  perform casevault.import_ground_truth(v_cv, p_doc -> 'ground_truth');
  return v_cv;
end
$$;

revoke all on all functions in schema casevault from anon, authenticated, public;
