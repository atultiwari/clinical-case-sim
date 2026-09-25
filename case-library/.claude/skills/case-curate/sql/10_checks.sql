-- step: 10 Check
-- writes: nothing
-- params: cv
-- All five must be empty (coverage: every kind fully resolved) before step 11.
select 'consistency' as check_name, c.check_name || ' ' || coalesce(c.rule_id, '') || ' ' ||
       c.target || ' day ' || coalesce(c.day::text, 'all') || ': ' || c.detail as problem
from casevault.check_consistency({{cv}}) c
union all
select 'leak', l.location || ' ' || l.row_id || ': ' || l.term from casevault.leak_scan({{cv}}) l
union all
select 'placeholder', p.location || ' ' || p.row_id || ': ' || p.snippet
from casevault.placeholder_scan({{cv}}) p
union all
select 'coverage', r.kind || ' ' || r.resolved || '/' || r.total || ' missing ' || array_to_string(r.missing, ', ')
from casevault.coverage_report({{cv}}) r where r.resolved < r.total
union all
select 'export', b from casevault.export_blockers({{cv}}) b
where b = 'ground truth is missing' or b like 'case version % does not exist';
