"""The read-only queries behind the case review pack (SPEC §7.2).

Each query takes %(cvs)s, the list of case version ids (LEAKS takes %(cv)s, one id),
and returns its columns in the order of the matching *_COLUMNS tuple. A ledger row
is live while its review status is pending, approved or edited.
"""

LIVE = "review_status in ('pending', 'approved', 'edited')"

CASES = """
select v.id, v.status, s.pmcid, s.licence, s.production_ok, s.public_release_ok
from casevault.case_version v
join casevault."case" c on c.id = v.case_id
left join casevault.source_article s on s.id = c.source_id
where v.id = any(%(cvs)s)
"""

ORIGIN_COUNTS = f"""
select case_version_id, origin, count(*)::int
from casevault.fact where case_version_id = any(%(cvs)s) group by 1, 2
union all
select case_version_id, tier, count(*)::int
from casevault.synthetic_ledger where case_version_id = any(%(cvs)s) and {LIVE} group by 1, 2
"""  # noqa: S608 - LIVE is a constant

LEDGER_COLUMNS = (
    "key",
    "case",
    "target",
    "item",
    "tier",
    "day",
    "release_text",
    "rationale",
    "confidence",
    "priority",
    "judgement_call",
)
LEDGER = f"""
select 'synthetic_ledger:' || l.id, l.case_version_id, l.target,
       coalesce(i.name, cmp.name, l.target), l.tier, l.day_bucket, l.release_text,
       l.rationale, l.confidence, l.priority, case when l.judgement_call then 'yes' else '' end,
       l.value, rr.low, rr.high, rr.unit
from casevault.synthetic_ledger l
join casevault.case_version v on v.id = l.case_version_id
join casevault."case" c on c.id = v.case_id
left join casevault.catalogue_item i on i.id = l.target
left join casevault.component cmp on cmp.id = l.target
left join lateral casevault.reference_range(coalesce(c.lab_profile, '{{}}'), l.target) rr
  on true
where l.case_version_id = any(%(cvs)s) and l.tier in ('affected', 'reviewer') and l.{LIVE}
order by l.case_version_id, l.target, l.day_bucket nulls first
"""  # noqa: S608 - LIVE is a constant

NORMAL_LIST_COLUMNS = ("key", "case", "target", "item", "tier", "days")
NORMAL_LIST = f"""
select 'synthetic_ledger:' || l.case_version_id || '/' || l.target, l.case_version_id,
       l.target, coalesce(i.name, cmp.name, l.target),
       string_agg(distinct l.tier, ', '), count(*)::int
from casevault.synthetic_ledger l
left join casevault.catalogue_item i on i.id = l.target
left join casevault.component cmp on cmp.id = l.target
where l.case_version_id = any(%(cvs)s) and l.tier in ('normal', 'rule') and l.{LIVE}
group by l.case_version_id, l.target, i.name, cmp.name
order by l.case_version_id, 4, l.target
"""  # noqa: S608 - LIVE is a constant

ARTICLE_FACT_COLUMNS = (
    "key",
    "case",
    "id",
    "category",
    "item",
    "catalogue_ref",
    "day",
    "value",
    "unit",
    "ref_range",
    "flag",
    "release_text",
    "source_locator",
)
ARTICLE_FACTS = """
select 'fact:' || case_version_id || '/' || id, case_version_id, id, category, item,
       catalogue_ref, day, coalesce(value, value_num::text), unit, ref_range, flag,
       release_text, source_locator
from casevault.fact
where case_version_id = any(%(cvs)s) and origin = 'article'
order by case_version_id, id
"""

PATIENT_WORDS_COLUMNS = ("key", "case", "item", "release_text", "lay_text")
PATIENT_WORDS = f"""
select 'fact:' || case_version_id || '/' || id, case_version_id, item, release_text, lay_text
from casevault.fact
where case_version_id = any(%(cvs)s) and (category = 'history' or lay_text is not null)
union all
select 'synthetic_ledger:' || l.id, l.case_version_id, coalesce(i.name, l.target),
       l.release_text, l.lay_text
from casevault.synthetic_ledger l
left join casevault.catalogue_item i on i.id = l.target
where l.case_version_id = any(%(cvs)s) and l.lay_text is not null and l.{LIVE}
order by 2, 1
"""  # noqa: S608 - LIVE is a constant

REPORT_COLUMNS = (
    "key",
    "case",
    "kind",
    "subject",
    "variant",
    "status",
    "status_line",
    "condition",
    "origin",
    "text",
    "findings",
    "rationale",
    "confidence",
)
REPORTS_CONSULTS = f"""
select 'report:' || case_version_id || '/' || id, case_version_id, 'report', test_item_id,
       variant, status, status_line, null::jsonb, array_to_string(origins, ', '),
       concat_ws(E'\\n\\n', report_text, 'Impression: ' || impression),
       array_to_string(findings, ', '), rationale, confidence
from casevault.report
where case_version_id = any(%(cvs)s) and {LIVE}
union all
select 'consult_note:' || case_version_id || '/' || id, case_version_id, 'consult', specialty,
       variant::text, null, null, condition, origin,
       concat_ws(E'\\n\\n', note_text,
                 'Recommendations: ' || nullif(array_to_string(recommendations, '; '), '')),
       null, rationale, confidence
from casevault.consult_note
where case_version_id = any(%(cvs)s) and {LIVE}
order by 2, 3 desc, 1
"""  # noqa: S608 - LIVE is a constant

GROUND_TRUTH = """
select case_version_id,
       jsonb_build_object('final_dx', final_dx, 'rubric', rubric,
                          'must_do', must_do, 'must_not_do', must_not_do)
from casevault.ground_truth
where case_version_id = any(%(cvs)s)
order by case_version_id
"""

LEAKS = "select location, row_id, term from casevault.leak_scan(%(cv)s)"
