-- Case Vault schema 0.3: resolving a case and checking it (SPEC §6.5, §6.6; PLAN L0.3).
--
--   compute_derived   derived facts from value_rule formulas over article values
--   resolve_normals   deterministic `normal` ledger rows for everything still open
--   check_consistency formula, physiology, range and contradiction findings (empty = pass)
--   coverage_gaps     every (item, component, day) that does not resolve
--   coverage_report   the same, summarised per catalogue kind
--   leak_scan         player-visible text that names the diagnosis (empty = pass)
--
-- The case's patient and laboratory, in casevault."case".lab_profile:
--   {"sex": "F", "age_years": 49,
--    "components": {"CMP.HB": {"low": 115, "high": 165, "unit": "g/L"}}}
-- Days the engine can request run from 0 to the last article day of the case.

-- ---------------------------------------------------------------------------
-- Shared views of a case
-- ---------------------------------------------------------------------------

create function casevault.case_days(p_cv text)
returns setof int
language sql
stable
set search_path = ''
as $$
  select generate_series(0, coalesce(max(day) filter (where day >= 0), 0))
  from casevault.fact
  where case_version_id = p_cv
$$;

create function casevault.is_live(p_review_status text)
returns boolean
language sql
immutable
set search_path = ''
as $$
  select p_review_status in ('pending', 'approved', 'edited')
$$;

-- Every numeric value the case holds for a catalogue target, article or synthetic.
create function casevault.known_values(p_cv text)
returns table (target text, day int, value_num numeric, origin text, row_id text)
language sql
stable
set search_path = ''
as $$
  select f.catalogue_ref, f.day, f.value_num, f.origin, f.id
  from casevault.fact f
  where f.case_version_id = p_cv and f.catalogue_ref is not null
  union all
  select l.target, l.day_bucket, casevault.json_num(l.value -> 'value'), l.tier, l.id::text
  from casevault.synthetic_ledger l
  where l.case_version_id = p_cv and casevault.is_live(l.review_status)
$$;

create function casevault.path_items(p_cv text)
returns setof text
language sql
stable
set search_path = ''
as $$
  select distinct unnest(items) from casevault.path_analysis where case_version_id = p_cv
$$;

-- Apply a ratio or difference rule to its inputs, in input order.
create function casevault.apply_rule(p_kind text, p_factor numeric, p_values numeric[])
returns numeric
language sql
immutable
set search_path = ''
as $$
  select case p_kind
    when 'ratio' then p_factor * p_values[1] / nullif(p_values[2], 0)
    when 'difference' then p_values[1] - (select sum(v) from unnest(p_values[2:]) v)
  end
$$;

-- ---------------------------------------------------------------------------
-- Derived values
-- ---------------------------------------------------------------------------

create function casevault.compute_derived(p_cv text, p_generator text, p_skill_version text)
returns int
language sql
set search_path = ''
as $$
  with per_day as (
    select r.id, r.kind, r.target, r.factor, r.formula, f.day,
           array_agg(f.value_num order by array_position(r.inputs, f.catalogue_ref)) as vals
    from casevault.value_rule r
    join casevault.fact f
      on f.case_version_id = p_cv and f.catalogue_ref = any (r.inputs) and f.value_num is not null
    where r.kind in ('ratio', 'difference')
    group by r.id, r.kind, r.target, r.factor, r.formula, r.inputs, f.day
    having count(*) = cardinality(r.inputs)
       and count(distinct f.catalogue_ref) = cardinality(r.inputs)
  ),
  computed as (
    select p.*, round(casevault.apply_rule(p.kind, p.factor, p.vals), coalesce(c.decimals, 1)) as v,
           coalesce(c.name, p.target) as item, c.unit_si
    from per_day p
    left join casevault.component c on c.id = p.target
    where not exists (
      select 1 from casevault.fact t
      where t.case_version_id = p_cv and t.catalogue_ref = p.target
        and t.day is not distinct from p.day)
  ),
  ins as (
    insert into casevault.fact
      (case_version_id, id, category, item, catalogue_ref, value, value_num, unit, day,
       origin, formula, release, generator, skill_version)
    select p_cv, 'D.' || replace(target, 'CMP.', '') || '.d' || coalesce(day::text, 'all'),
           'lab', item, target, v::text, v, unit_si, day, 'derived', formula, 'chart',
           p_generator, p_skill_version
    from computed
    where v is not null
    returning 1
  )
  select count(*)::int from ins
$$;

-- ---------------------------------------------------------------------------
-- The normal generator
-- ---------------------------------------------------------------------------

-- The range for this patient: the case's own laboratory first, then the
-- catalogue's ranges for the patient's sex and age.
create function casevault.reference_range(p_profile jsonb, p_component text)
returns table (low numeric, high numeric, unit text)
language sql
stable
set search_path = ''
as $$
  select (o ->> 'low')::numeric, (o ->> 'high')::numeric, coalesce(o ->> 'unit', c.unit_si)
  from casevault.component c,
       lateral (select p_profile -> 'components' -> p_component as o) own
  where c.id = p_component and o ? 'low' and o ? 'high'
  union all
  select * from (
    select (r ->> 'low')::numeric, (r ->> 'high')::numeric, c.unit_si
    from casevault.component c, jsonb_array_elements(coalesce(c.ref_ranges, '[]')) r
    where c.id = p_component
      and not coalesce(p_profile -> 'components' -> p_component ? 'low', false)
      and coalesce(r ->> 'sex', 'any') in ('any', p_profile ->> 'sex')
      and coalesce((p_profile ->> 'age_years')::numeric, 40)
          between coalesce((r ->> 'age_min')::numeric, 0) and coalesce((r ->> 'age_max')::numeric, 200)
    order by (r ->> 'sex') is not distinct from (p_profile ->> 'sex') desc
    limit 1
  ) catalogue
  limit 1
$$;

-- A value inside the range, bell-shaped around its middle, seeded by
-- (case id, component id, day bucket) so it is the same on every run.
create function casevault.normal_value(
  p_case_id text, p_component text, p_day int, p_low numeric, p_high numeric, p_decimals int)
returns numeric
language sql
immutable
set search_path = ''
as $$
  select round(p_low + (0.1 + 0.8 * avg(u)) * (p_high - p_low), coalesce(p_decimals, 1))
  from (
    select abs(hashtextextended(
             p_case_id || '|' || p_component || '|' || coalesce(p_day::text, 'all') || '|' || k, 0)
           % 1000000) / 1000000.0 as u
    from generate_series(1, 3) k
  ) draws
$$;

create function casevault.resolve_normal_components(
  p_cv text, p_generator text, p_skill_version text)
returns int
language sql
set search_path = ''
as $$
  with cv as (
    select v.case_id, c.lab_profile
    from casevault.case_version v join casevault."case" c on c.id = v.case_id
    where v.id = p_cv
  ),
  open_components as (
    select distinct tc.component_id
    from casevault.catalogue_item i
    join casevault.test_component tc on tc.test_item_id = i.id
    where i.active and i.kind = 'test'
      and i.id not in (select casevault.path_items(p_cv))
      and tc.component_id not in (select casevault.path_items(p_cv))
      and tc.component_id not in (
        select target from casevault.value_rule where kind in ('ratio', 'difference'))
  ),
  wanted as (
    select oc.component_id, c.decimals, c.normal_text, rr.low, rr.high, rr.unit,
           case when rr.low is null then null else d.day end as day
    from open_components oc
    join casevault.component c on c.id = oc.component_id
    cross join cv
    left join lateral casevault.reference_range(cv.lab_profile, oc.component_id) rr on true
    cross join lateral (select casevault.case_days(p_cv) as day) d
    where rr.low is not null or c.normal_text is not null
  ),
  todo as (
    select distinct w.* from wanted w
    where not exists (
      select 1 from casevault.known_values(p_cv) k
      where k.target = w.component_id
        and (k.day is not distinct from w.day or k.day is null or w.day is null))
  ),
  ins as (
    insert into casevault.synthetic_ledger
      (case_version_id, target, day_bucket, tier, value, priority, generator, skill_version)
    select p_cv, t.component_id, t.day, 'normal',
           case when t.low is null then jsonb_build_object('text', t.normal_text)
                else jsonb_build_object(
                  'value', casevault.normal_value(cv.case_id, t.component_id, t.day, t.low, t.high, t.decimals),
                  'unit', t.unit, 'ref_range', t.low || '-' || t.high) end,
           'low', p_generator, p_skill_version
    from todo t cross join cv
    returning 1
  )
  select count(*)::int from ins
$$;

create function casevault.resolve_normal_templates(
  p_cv text, p_generator text, p_skill_version text)
returns int
language sql
set search_path = ''
as $$
  with ins as (
    insert into casevault.synthetic_ledger
      (case_version_id, target, day_bucket, tier, value, release_text, priority, generator, skill_version)
    select p_cv, i.id, null, 'normal', jsonb_build_object('text', t.template), t.template, 'low',
           p_generator, p_skill_version
    from casevault.catalogue_item i
    join casevault.normal_template t on t.item_id = i.id and t.review_status = 'approved'
    where i.active and i.kind in ('history', 'exam')
      and i.id not in (select casevault.path_items(p_cv))
      and not exists (
        select 1 from casevault.fact f
        where f.case_version_id = p_cv and (f.catalogue_ref = i.id or i.id = any (f.released_by)))
      and not exists (
        select 1 from casevault.synthetic_ledger l
        where l.case_version_id = p_cv and l.target = i.id and casevault.is_live(l.review_status))
    returning 1
  )
  select count(*)::int from ins
$$;

-- Synthetic values that a formula produces are calculated from the day's other
-- values (article or synthetic), so the generator never breaks its own formulas.
-- A value calculated from any affected or reviewer input is itself affected,
-- with the formula as its rationale; otherwise it is normal.
create function casevault.resolve_normal_derived(
  p_cv text, p_generator text, p_skill_version text)
returns int
language sql
set search_path = ''
as $$
  with cv as (
    select v.case_id, c.lab_profile
    from casevault.case_version v join casevault."case" c on c.id = v.case_id
    where v.id = p_cv
  ),
  kv as (select * from casevault.known_values(p_cv) where value_num is not null),
  per_day as (
    select r.id, r.kind, r.target, r.factor, r.formula, d.day,
           array_agg(k.value_num order by array_position(r.inputs, k.target)) as vals,
           bool_or(k.origin in ('affected', 'reviewer')) as from_affected
    from casevault.value_rule r
    cross join lateral (select casevault.case_days(p_cv) as day) d
    join kv k on k.target = any (r.inputs) and (k.day = d.day or k.day is null)
    where r.kind in ('ratio', 'difference')
      and r.target not in (select casevault.path_items(p_cv))
      and r.target in (
        select tc.component_id
        from casevault.test_component tc
        join casevault.catalogue_item i on i.id = tc.test_item_id and i.active)
      and not exists (
        select 1 from kv t where t.target = r.target and (t.day = d.day or t.day is null))
    group by r.id, r.kind, r.target, r.factor, r.formula, r.inputs, d.day
    having count(*) = cardinality(r.inputs)
       and count(distinct k.target) = cardinality(r.inputs)
  ),
  ins as (
    insert into casevault.synthetic_ledger
      (case_version_id, target, day_bucket, tier, value, priority, rationale, confidence, checks,
       generator, skill_version)
    select p_cv, p.target, p.day, case when p.from_affected then 'affected' else 'normal' end,
           jsonb_strip_nulls(jsonb_build_object(
             'value', round(casevault.apply_rule(p.kind, p.factor, p.vals), coalesce(c.decimals, 1)),
             'unit', coalesce(rr.unit, c.unit_si),
             'ref_range', rr.low || '-' || rr.high)),
           case when p.from_affected then 'medium' else 'low' end,
           case when p.from_affected then 'Calculated: ' || p.formula end,
           case when p.from_affected then 1 end,
           jsonb_build_object('formula', p.formula), p_generator, p_skill_version
    from per_day p
    cross join cv
    left join casevault.component c on c.id = p.target
    left join lateral casevault.reference_range(cv.lab_profile, p.target) rr on true
    where casevault.apply_rule(p.kind, p.factor, p.vals) is not null
    returning 1
  )
  select count(*)::int from ins
$$;

-- Items on the case's paths are never filled here: they are `affected` (SPEC §6.3).
create function casevault.resolve_normals(
  p_cv text, p_generator text default 'normal-generator v1', p_skill_version text default 'v0.1')
returns int
language sql
set search_path = ''
as $$
  -- Components first, so the derived pass can read them.
  select casevault.resolve_normal_components(p_cv, p_generator, p_skill_version)
       + casevault.resolve_normal_templates(p_cv, p_generator, p_skill_version)
       + casevault.resolve_normal_derived(p_cv, p_generator, p_skill_version)
$$;

-- ---------------------------------------------------------------------------
-- Checks
-- ---------------------------------------------------------------------------

create function casevault.check_consistency(p_cv text)
returns table (check_name text, rule_id text, target text, day int, detail text)
language sql
stable
set search_path = ''
as $$
  with kv as (select * from casevault.known_values(p_cv) where value_num is not null),
  inputs as (
    select r.id, r.kind, r.target, r.factor, r.tolerance_pct, kv.day,
           array_agg(kv.value_num order by array_position(r.inputs, kv.target)) as vals
    from casevault.value_rule r
    join kv on kv.target = any (r.inputs)
    group by r.id, r.kind, r.target, r.factor, r.tolerance_pct, r.inputs, kv.day
    having count(*) = cardinality(r.inputs)
  ),
  paired as (
    select i.*, t.value_num as actual, coalesce(c.decimals, 1) as decimals
    from inputs i
    join kv t on t.target = i.target and t.day is not distinct from i.day
    left join casevault.component c on c.id = i.target
  )
  select 'formula', id, target, day,
         format('%s = %s, expected %s from its inputs', target, actual,
                round(casevault.apply_rule(kind, factor, vals), decimals))
  from paired
  where kind in ('ratio', 'difference')
    and abs(actual - casevault.apply_rule(kind, factor, vals))
        > greatest(abs(casevault.apply_rule(kind, factor, vals)) * tolerance_pct / 100,
                   power(10::numeric, -decimals))
  union all
  select 'physiology', id, target, day, format('%s = %s is above %s', target, actual, vals[1])
  from paired
  where kind = 'not_above' and actual > vals[1]
  union all
  select 'physiology', id, target, day,
         format('parts sum to %s but %s = %s', (select sum(v) from unnest(vals) v), target, actual)
  from paired
  where kind = 'sum_equals'
    and abs((select sum(v) from unnest(vals) v) - actual) > abs(actual) * tolerance_pct / 100
  union all
  select 'range', null, l.target, l.day_bucket,
         format('normal value %s is outside %s-%s; it belongs on a path as affected',
                casevault.json_num(l.value -> 'value'), rr.low, rr.high)
  from casevault.synthetic_ledger l
  join casevault.case_version v on v.id = l.case_version_id
  join casevault."case" c on c.id = v.case_id
  cross join lateral casevault.reference_range(c.lab_profile, l.target) rr
  where l.case_version_id = p_cv and l.tier = 'normal' and casevault.is_live(l.review_status)
    and casevault.json_num(l.value -> 'value') not between rr.low and rr.high
  union all
  select 'contradiction', null, l.target, l.day_bucket,
         format('synthetic row %s overlaps article fact %s', l.id, f.id)
  from casevault.synthetic_ledger l
  join casevault.fact f
    on f.case_version_id = l.case_version_id
   and (f.catalogue_ref = l.target or l.target = any (f.released_by))
   and (f.day is not distinct from l.day_bucket or f.day is null or l.day_bucket is null)
  where l.case_version_id = p_cv and casevault.is_live(l.review_status)
  order by 1, 3, 4
$$;

create function casevault.item_resolves(p_cv text, p_item text, p_kind text)
returns boolean
language sql
stable
set search_path = ''
as $$
  select exists (
      select 1 from casevault.synthetic_ledger l
      where l.case_version_id = p_cv and l.target = p_item and casevault.is_live(l.review_status))
    or (p_kind in ('history', 'exam') and exists (
      select 1 from casevault.fact f
      where f.case_version_id = p_cv and (f.catalogue_ref = p_item or p_item = any (f.released_by))))
    or (p_kind = 'referral' and exists (
      select 1 from casevault.consult_note n
      where n.case_version_id = p_cv and n.specialty = p_item and casevault.is_live(n.review_status)))
    or (p_kind = 'test' and exists (
      select 1 from casevault.report r
      where r.case_version_id = p_cv and r.test_item_id = p_item and casevault.is_live(r.review_status)))
$$;

-- Actions, diagnoses and findings need no resolution (SPEC §6.6).
create function casevault.coverage_gaps(p_cv text)
returns table (kind text, item_id text, component_id text, day int)
language sql
stable
set search_path = ''
as $$
  with items as (
    select i.id, i.kind from casevault.catalogue_item i
    where i.active and i.kind in ('history', 'exam', 'test', 'referral')
      and not casevault.item_resolves(p_cv, i.id, i.kind)
  ),
  kv as (select * from casevault.known_values(p_cv))
  select i.kind, i.id, null::text, null::int
  from items i
  where i.kind <> 'test'
     or not exists (select 1 from casevault.test_component tc where tc.test_item_id = i.id)
  union all
  select i.kind, i.id, tc.component_id, d.day
  from items i
  join casevault.test_component tc on tc.test_item_id = i.id
  cross join lateral (select casevault.case_days(p_cv) as day) d
  where not exists (
    select 1 from kv
    where kv.target = tc.component_id and (kv.day = d.day or kv.day is null))
  order by 1, 2, 3, 4
$$;

create function casevault.coverage_report(p_cv text)
returns table (kind text, total int, resolved int, missing text[])
language sql
stable
set search_path = ''
as $$
  with gaps as (select distinct kind, item_id from casevault.coverage_gaps(p_cv))
  select i.kind, count(*)::int, (count(*) - count(g.item_id))::int,
         coalesce(array_agg(g.item_id order by g.item_id) filter (where g.item_id is not null), '{}')
  from casevault.catalogue_item i
  left join gaps g on g.item_id = i.id
  where i.active and i.kind in ('history', 'exam', 'test', 'referral')
  group by i.kind
  order by i.kind
$$;

-- ---------------------------------------------------------------------------
-- Leak scan
-- ---------------------------------------------------------------------------

create function casevault.regex_escape(p text)
returns text
language sql
immutable
set search_path = ''
as $$
  select regexp_replace(p, '([!$()*+.:<=>?[\\\]^{|}-])', '\\\1', 'g')
$$;

-- Lower-case the text and blank out allowed phrases, longest first.
create function casevault.strip_phrases(p_text text, p_phrases text[])
returns text
language plpgsql
immutable
set search_path = ''
as $$
declare
  v_out text := lower(coalesce(p_text, ''));
  v_phrase text;
begin
  foreach v_phrase in array (
    select coalesce(array_agg(x order by length(x) desc), '{}') from unnest(p_phrases) x) loop
    v_out := replace(v_out, v_phrase, ' ');
  end loop;
  return v_out;
end
$$;

-- Terms come from the ground truth (synonyms, leak terms, pathognomonic phrases)
-- and from the catalogue diagnosis it names. Test names, and any phrases the
-- ground truth allows, are blanked out first ("blood lead" is allowed).
-- Facts flagged reveals_dx are the confirmatory results and are not scanned.
create function casevault.leak_scan(p_cv text)
returns table (location text, row_id text, term text)
language sql
stable
set search_path = ''
as $$
  with gt as (select final_dx as dx from casevault.ground_truth where case_version_id = p_cv),
  dx_ids as (
    select dx ->> 'id' as id from gt
    union select jsonb_array_elements_text(coalesce(dx -> 'ids', '[]')) from gt
  ),
  terms as (
    select distinct lower(t) as term from (
      select jsonb_array_elements_text(coalesce(dx -> k, '[]')) as t
      from gt, unnest(array['accepted_synonyms', 'leak_terms', 'pathognomonic_phrases']) k
      union all
      select i.name from casevault.catalogue_item i join dx_ids d on d.id = i.id
      union all
      select unnest(i.synonyms) from casevault.catalogue_item i join dx_ids d on d.id = i.id
    ) raw
    where length(t) >= 3
  ),
  allowed as (
    select coalesce(array_agg(distinct lower(a)), '{}') as phrases from (
      select jsonb_array_elements_text(coalesce(dx -> 'allowed_phrases', '[]')) as a from gt
      union all select name from casevault.catalogue_item where kind = 'test'
      union all select unnest(synonyms) from casevault.catalogue_item where kind = 'test'
    ) a
  ),
  texts as (
    select 'case.display_title' as location, c.id as row_id, c.display_title as body
    from casevault.case_version v join casevault."case" c on c.id = v.case_id where v.id = p_cv
    union all
    select 'case.display_tags', c.id, array_to_string(c.display_tags, ' | ')
    from casevault.case_version v join casevault."case" c on c.id = v.case_id where v.id = p_cv
    union all
    select 'case_version.vignette', id, vignette from casevault.case_version where id = p_cv
    union all
    select 'case_version.opening_statement_lay', id, opening_statement_lay
    from casevault.case_version where id = p_cv
    union all
    select 'fact', id, concat_ws(' | ', value, release_text, lay_text)
    from casevault.fact where case_version_id = p_cv and release <> 'never' and not reveals_dx
    union all
    select 'synthetic_ledger', id::text, concat_ws(' | ', value::text, release_text, lay_text)
    from casevault.synthetic_ledger where case_version_id = p_cv and casevault.is_live(review_status)
    union all
    select 'report', id, concat_ws(' | ', report_text, impression, status_line)
    from casevault.report where case_version_id = p_cv and casevault.is_live(review_status)
    union all
    select 'consult_note', id, concat_ws(' | ', note_text, array_to_string(recommendations, ' | '))
    from casevault.consult_note where case_version_id = p_cv and casevault.is_live(review_status)
    union all
    select 'media', id, redacted_caption from casevault.media where case_version_id = p_cv
    union all
    select 'raw_material', id, findings from casevault.raw_material where case_version_id = p_cv
  )
  select t.location, t.row_id, terms.term
  from texts t
  cross join allowed
  join terms
    on casevault.strip_phrases(t.body, allowed.phrases) ~ ('\m' || casevault.regex_escape(terms.term) || '\M')
  order by 1, 2, 3
$$;

revoke all on all functions in schema casevault from anon, authenticated, public;
