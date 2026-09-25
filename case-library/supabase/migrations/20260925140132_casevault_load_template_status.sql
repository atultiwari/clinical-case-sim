-- Case Vault: the catalogue loader takes each normal template's review status
-- from the document (catalogue/normal_templates.csv, PLAN L0.5), so templates
-- Atul approves in a catalogue review load as approved. A document without the
-- status keeps the earlier rule: a changed text goes back to review.
--
-- A document with "partial": true (one of several calls that together load a
-- catalogue too large for one MCP call) deactivates nothing; the last call, or a
-- complete document, deactivates items of its kinds that it leaves out.

create or replace function casevault.load_catalogue(p_doc jsonb)
returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_version int := (p_doc ->> 'version')::int;
  v_items int;
  v_deactivated int;
  v_tests int;
  v_components int;
  v_test_components int;
  v_templates int;
  v_diagnoses int;
  v_rules int := 0;
begin
  if v_version is null or v_version < 0 then
    raise exception 'casevault.load_catalogue needs a document with a catalogue version of 0 or more'
      using errcode = 'P0001';
  end if;

  insert into casevault.catalogue_item
    (id, kind, name, category, synonyms, specialty_scope, active, since_version)
  select i ->> 'id', i ->> 'kind', i ->> 'name', i ->> 'category',
         casevault.json_text_array(i -> 'synonyms'), casevault.json_text_array(i -> 'specialty_scope'),
         true, v_version
  from jsonb_array_elements(coalesce(p_doc -> 'items', '[]')) i
  on conflict (id) do update
    set kind = excluded.kind, name = excluded.name, category = excluded.category,
        synonyms = excluded.synonyms, specialty_scope = excluded.specialty_scope, active = true;
  get diagnostics v_items = row_count;

  update casevault.catalogue_item c
  set active = false
  where c.active
    and not coalesce((p_doc ->> 'partial')::boolean, false)
    and c.kind in (select distinct i ->> 'kind' from jsonb_array_elements(coalesce(p_doc -> 'items', '[]')) i)
    and c.id not in (select i ->> 'id' from jsonb_array_elements(coalesce(p_doc -> 'items', '[]')) i);
  get diagnostics v_deactivated = row_count;

  insert into casevault.component
    (id, name, loinc, unit_si, unit_conv, conv_factor, decimals, ref_ranges, normal_text)
  select c ->> 'id', c ->> 'name', c ->> 'loinc', c ->> 'unit_si', c ->> 'unit_conv',
         (c ->> 'conv_factor')::numeric, (c ->> 'decimals')::int,
         coalesce(c -> 'ref_ranges', '[]'), c ->> 'normal_text'
  from jsonb_array_elements(coalesce(p_doc -> 'components', '[]')) c
  on conflict (id) do update
    set name = excluded.name, loinc = excluded.loinc, unit_si = excluded.unit_si,
        unit_conv = excluded.unit_conv, conv_factor = excluded.conv_factor,
        decimals = excluded.decimals, ref_ranges = excluded.ref_ranges,
        normal_text = excluded.normal_text;
  get diagnostics v_components = row_count;

  insert into casevault.test_def
    (item_id, route, specimen, price_inr, price_source, tat_minutes, invasive, loinc)
  select t ->> 'item_id', t ->> 'route', t ->> 'specimen', (t ->> 'price_inr')::numeric,
         t ->> 'price_source', (t ->> 'tat_minutes')::int, coalesce((t ->> 'invasive')::boolean, false),
         t ->> 'loinc'
  from jsonb_array_elements(coalesce(p_doc -> 'tests', '[]')) t
  on conflict (item_id) do update
    set route = excluded.route, specimen = excluded.specimen, price_inr = excluded.price_inr,
        price_source = excluded.price_source, tat_minutes = excluded.tat_minutes,
        invasive = excluded.invasive, loinc = excluded.loinc;
  get diagnostics v_tests = row_count;

  delete from casevault.test_component tc
  where tc.test_item_id in (
    select t ->> 'item_id' from jsonb_array_elements(coalesce(p_doc -> 'tests', '[]')) t);
  insert into casevault.test_component (test_item_id, component_id, position)
  select t ->> 'item_id', c.component_id, c.position::int
  from jsonb_array_elements(coalesce(p_doc -> 'tests', '[]')) t,
       jsonb_array_elements_text(t -> 'components') with ordinality c (component_id, position);
  get diagnostics v_test_components = row_count;

  -- The CSV's review_status wins when the document carries it (Atul approves
  -- templates in a catalogue review); otherwise a changed text goes back to review.
  insert into casevault.normal_template (item_id, template, review_status)
  select n ->> 'item_id', n ->> 'template', coalesce(n ->> 'review_status', 'pending')
  from jsonb_array_elements(coalesce(p_doc -> 'normal_templates', '[]')) n
  on conflict (item_id) do update
    set template = excluded.template,
        review_status = case
          when (select n ? 'review_status'
                from jsonb_array_elements(p_doc -> 'normal_templates') n
                where n ->> 'item_id' = excluded.item_id limit 1)
            then excluded.review_status
          when casevault.normal_template.template = excluded.template
            then casevault.normal_template.review_status
          else 'pending' end;
  get diagnostics v_templates = row_count;

  insert into casevault.diagnosis_def (item_id, icd11, icd10)
  select d ->> 'item_id', d ->> 'icd11', d ->> 'icd10'
  from jsonb_array_elements(coalesce(p_doc -> 'diagnoses', '[]')) d
  on conflict (item_id) do update set icd11 = excluded.icd11, icd10 = excluded.icd10;
  get diagnostics v_diagnoses = row_count;

  if p_doc ? 'value_rules' then
    delete from casevault.value_rule;
    insert into casevault.value_rule (id, kind, target, inputs, factor, tolerance_pct, formula)
    select r ->> 'id', r ->> 'kind', r ->> 'target', casevault.json_text_array(r -> 'inputs'),
           coalesce((r ->> 'factor')::numeric, 1), coalesce((r ->> 'tolerance_pct')::numeric, 2),
           r ->> 'formula'
    from jsonb_array_elements(p_doc -> 'value_rules') r;
    get diagnostics v_rules = row_count;
  end if;

  return jsonb_build_object(
    'items', v_items, 'deactivated', v_deactivated, 'tests', v_tests,
    'components', v_components, 'test_components', v_test_components,
    'normal_templates', v_templates, 'diagnoses', v_diagnoses, 'value_rules', v_rules);
end
$$;

comment on function casevault.load_catalogue(jsonb) is
  'Upserts the catalogue document built from catalogue/*.csv (scripts/catalogue.py). '
  'Items left out are deactivated, never deleted. Returns rows written per table.';

revoke all on function casevault.load_catalogue(jsonb) from anon, authenticated, public;
