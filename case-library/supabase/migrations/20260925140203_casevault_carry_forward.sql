-- Case Vault: a day with no result returns the latest earlier result (PLAN L0.9;
-- Atul's decision of 2026-09-25, a shared-contract change in docs/CHANGELOG.md).
--
-- coverage_gaps: a component is covered on a day when the case has a value for it
-- on that day or any earlier day, or one valid throughout the admission. Only days
-- before its first value stay open.
-- resolve_normal_components: the normal generator no longer fills a component the
-- case already has any value for.

create or replace function casevault.resolve_normal_components(
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
      -- A component the case already has a value for (article, derived or ledger) is
      -- never filled here: later days carry that value forward, and earlier days are
      -- resolved by hand, so a normal value never contradicts a measured one.
      and tc.component_id not in (select k.target from casevault.known_values(p_cv) k)
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

create or replace function casevault.coverage_gaps(p_cv text)
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
    where kv.target = tc.component_id and (kv.day <= d.day or kv.day is null))
  order by 1, 2, 3, 4
$$;

revoke all on all functions in schema casevault from anon, authenticated, public;
