"""Every case-curate SQL snippet runs, in protocol order, on the local Case Vault (PLAN L0.6).

The fixture catalogue and case stand in for a real article; each snippet is
rendered by scripts.curate_plan.render exactly as a real run renders it for the MCP.
"""

import json
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts import curate_plan as plan

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
CV = "PMC0000001@v1"
GENERATOR = "claude-test via case-curate v0.1"

PARAMS: dict[str, Any] = {
    "cv": CV,
    "pmcid": "PMC0000001",
    "doc": json.loads((FIXTURES / "mini_case.json").read_text(encoding="utf-8")),
    "generator": GENERATOR,
    "skill_version": "v0.1",
    "links": [{"fact": "H02", "released_by": ["HX.SUPPLEMENTS"]}],
    "fulltext_format": "jats",
    "fulltext": "<article>fixture</article>",
    "content_hash": "0" * 64,
    "vignette": "A 49-year-old woman with abdominal pain and tiredness.",
    "opening_statement_lay": "I've had tummy pains and I'm exhausted.",
    "display_title": "Tired with abdominal pain",
    "display_tags": ["haematology", "abdominal pain"],
    "slug": "c-ab12c",
    "ground_truth": {
        "final_dx": {"id": "DX.LEAD_POISONING", "name": "Lead poisoning"},
        "must_do": [],
        "must_not_do": [],
    },
    "paths": [
        {
            "path_id": "P1",
            "kind": "efficient",
            "name": "Find the source",
            "rationale": "Remedy history and a blood lead",
            "items": ["HX.SUPPLEMENTS", "LAB.BLOOD_LEAD", "LAB.FILM", "REF.TOXICOLOGY"],
        }
    ],
    "rows": [
        {
            "target": "HX.OCCUPATION",
            "tier": "affected",
            "value": {"text": "Office work."},
            "release_text": "Works in an office.",
            "lay_text": "I work in an office.",
            "priority": "medium",
            "rationale": "Article silent; neutral job.",
            "confidence": 0.6,
        }
    ],
    "reports": [
        {
            "id": "RP01",
            "test_item_id": "LAB.FILM",
            "variant": "only",
            "status": "final",
            "findings": [],
            "report_text": "Coarse stippling in some red cells.",
            "based_on": ["R01"],
            "origins": ["article"],
        }
    ],
    "notes": [
        {
            "id": "CN01",
            "specialty": "REF.TOXICOLOGY",
            "note_text": "Happy to review.",
            "origin": "rule",
        }
    ],
    "lay": [{"fact": "H02", "lay_text": "A friend gave me a herbal remedy."}],
    "utility": [{"test_item_id": "LAB.BLOOD_LEAD", "utility": "essential", "rationale": "Key"}],
}


def _run(db: psycopg.Connection, name: str, params: dict[str, Any]) -> list[tuple[Any, ...]]:
    snippet = next(s for s in plan.load_snippets() if s.name == name)
    rows: list[tuple[Any, ...]] = []
    with db.cursor() as cur:
        cur.execute(plan.render(snippet.sql, params))
        while True:
            if cur.description is not None:
                rows = cur.fetchall()
            if not cur.nextset():
                break
    return rows


def test_every_snippet_runs_in_protocol_order(db: psycopg.Connection) -> None:
    db.execute((FIXTURES / "mini_catalogue.sql").read_text(encoding="utf-8"))
    assert _run(db, "01_identify.sql", PARAMS) == []
    order = [s.name for s in plan.load_snippets() if s.name != "01_identify.sql"]
    rule_rows = {
        "rows": [
            {
                "target": "LAB.UA",
                "value": {"text": "Not applicable"},
                "release_text": "Not applicable.",
            }
        ]
    }
    for name in order:
        _run(db, name, {**PARAMS, **rule_rows} if name == "08d_rules.sql" else PARAMS)

    status = db.execute(
        "select status, skill_version from casevault.case_version where id = %s", (CV,)
    ).fetchone()
    assert status == ("in_review", "v0.1")
    released = db.execute(
        "select released_by, lay_text from casevault.fact"
        " where case_version_id = %s and id = 'H02'",
        (CV,),
    ).fetchone()
    assert released == (["HX.SUPPLEMENTS"], "A friend gave me a herbal remedy.")
    slug, hash_ = db.execute(
        'select c.slug, s.content_hash from casevault."case" c'
        " join casevault.source_article s on s.id = c.source_id where c.id = 'PMC0000001'"
    ).fetchone() or (None, None)
    assert (slug, hash_) == ("c-fx001", "0" * 64)  # an existing slug is never replaced
    tiers: dict[str, int] = dict(
        db.execute(
            "select tier, count(*) from casevault.synthetic_ledger where case_version_id = %s"
            " group by tier",
            (CV,),
        ).fetchall()
    )
    assert tiers["affected"] == 1
    assert tiers["rule"] == 1
    assert tiers["normal"] > 0


def test_the_ground_truth_step_can_run_twice_on_a_draft(db: psycopg.Connection) -> None:
    db.execute((FIXTURES / "mini_catalogue.sql").read_text(encoding="utf-8"))
    _run(db, "04_import.sql", PARAMS)
    _run(db, "06_ground_truth.sql", PARAMS)
    _run(db, "06_ground_truth.sql", PARAMS)
    count = db.execute(
        "select count(*) from casevault.ground_truth where case_version_id = %s", (CV,)
    ).fetchone()
    assert count == (1,)


def test_checks_report_problems_before_resolution(db: psycopg.Connection) -> None:
    db.execute((FIXTURES / "mini_catalogue.sql").read_text(encoding="utf-8"))
    _run(db, "04_import.sql", PARAMS)
    problems = _run(db, "10_checks.sql", PARAMS)
    assert any(kind == "coverage" for kind, _ in problems)
