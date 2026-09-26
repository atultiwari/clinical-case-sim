-- Case Vault: conditions leave in the bundle schema's shape (SPEC §10.4; PLAN L1.7).
--
-- Schema 0.3 writes a finding condition as a list of finding ids, with from_tests beside it:
--   {"finding_released": ["FND.X"], "from_tests": ["LAB.Y"]}
-- Seven cases were curated with an object instead, which the schema does not allow:
--   {"finding_released": {"findings": ["FND.X"], "from_tests": ["LAB.Y"]}}
-- Their versions are frozen, so their rows cannot change. The export rewrites every
-- condition (consult note conditions, rubric anchors, must-do and must-not-do) into the
-- schema's shape instead. The meaning is unchanged; the frozen rows keep what was reviewed,
-- and bundle_rows is left as it was.

create function casevault.bundle_condition(p_condition jsonb)
returns jsonb
language plpgsql
immutable
set search_path = ''
as $$
declare
  v_out jsonb := p_condition;
  v_found jsonb := p_condition -> 'finding_released';
begin
  if p_condition is null or jsonb_typeof(p_condition) <> 'object' then
    return p_condition;
  end if;
  if jsonb_typeof(v_found) = 'object' then
    v_out := (v_out - 'finding_released')
             || jsonb_build_object('finding_released', v_found -> 'findings');
    if v_found ? 'from_tests' then
      v_out := v_out || jsonb_build_object('from_tests', v_found -> 'from_tests');
    end if;
  end if;
  if jsonb_typeof(v_out -> 'not') = 'object' then
    v_out := jsonb_set(v_out, '{not}', casevault.bundle_condition(v_out -> 'not'));
  end if;
  if jsonb_typeof(v_out -> 'all') = 'array' then
    v_out := jsonb_set(v_out, '{all}', casevault.bundle_conditions(v_out -> 'all'));
  end if;
  if jsonb_typeof(v_out -> 'any') = 'array' then
    v_out := jsonb_set(v_out, '{any}', casevault.bundle_conditions(v_out -> 'any'));
  end if;
  return v_out;
end
$$;

-- An array of conditions (the members of all and any), each rewritten.
create function casevault.bundle_conditions(p_conditions jsonb)
returns jsonb
language sql
immutable
set search_path = ''
as $$
  select coalesce(jsonb_agg(casevault.bundle_condition(c) order by n), '[]'::jsonb)
  from jsonb_array_elements(p_conditions) with ordinality as e(c, n)
$$;

-- Scored items ({text, if}) with their conditions rewritten; plain strings pass through.
create function casevault.bundle_scored(p_items jsonb)
returns jsonb
language sql
immutable
set search_path = ''
as $$
  select case when p_items is null or jsonb_typeof(p_items) <> 'array' then p_items else (
    select coalesce(jsonb_agg(
             case when jsonb_typeof(i -> 'if') = 'object'
                  then jsonb_set(i, '{if}', casevault.bundle_condition(i -> 'if'))
                  else i end
             order by n), '[]'::jsonb)
    from jsonb_array_elements(p_items) with ordinality as e(i, n)) end
$$;

create function casevault.bundle_ground_truth(p_gt jsonb)
returns jsonb
language sql
immutable
set search_path = ''
as $$
  select p_gt
    || case when p_gt ? 'must_do'
            then jsonb_build_object('must_do', casevault.bundle_scored(p_gt -> 'must_do'))
            else '{}'::jsonb end
    || case when p_gt ? 'must_not_do'
            then jsonb_build_object('must_not_do', casevault.bundle_scored(p_gt -> 'must_not_do'))
            else '{}'::jsonb end
    || case when jsonb_typeof(p_gt #> '{rubric,rubric}') = 'array'
            then jsonb_build_object('rubric', jsonb_set(p_gt -> 'rubric', '{rubric}',
                   casevault.bundle_scored(p_gt #> '{rubric,rubric}')))
            else '{}'::jsonb end
$$;

-- The bundle rows with every condition rewritten. bundle_rows itself is unchanged, so each
-- frozen version's frozen_hash (SHA-256 of bundle_rows(id)::text) still reproduces.
create function casevault.bundle_shape(p_rows jsonb)
returns jsonb
language sql
immutable
set search_path = ''
as $$
  select p_rows || jsonb_build_object(
    'consult_notes', coalesce((
      select jsonb_agg(
               case when jsonb_typeof(n -> 'condition') = 'object'
                    then jsonb_set(n, '{condition}', casevault.bundle_condition(n -> 'condition'))
                    else n end
               order by k)
      from jsonb_array_elements(p_rows -> 'consult_notes') with ordinality as e(n, k)), '[]'),
    'ground_truth', casevault.bundle_ground_truth(p_rows -> 'ground_truth'))
$$;

-- As in 20260925112550_casevault_export.sql, with the bundle rows passed through bundle_shape.
create or replace function casevault.export_bundle(
  p_cv text, p_revision int, p_catalogue_version int)
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

  return v_head || casevault.bundle_shape(casevault.bundle_rows(p_cv));
end
$$;

revoke all on function
  casevault.bundle_condition(jsonb),
  casevault.bundle_conditions(jsonb),
  casevault.bundle_scored(jsonb),
  casevault.bundle_ground_truth(jsonb),
  casevault.bundle_shape(jsonb)
from anon, authenticated, public;

grant execute on function
  casevault.bundle_condition(jsonb),
  casevault.bundle_conditions(jsonb),
  casevault.bundle_scored(jsonb),
  casevault.bundle_ground_truth(jsonb),
  casevault.bundle_shape(jsonb)
to casevault_reader;
