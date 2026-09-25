"""The pilot resolves completely, following the case-curate skill (PLAN L0.9).

Every step runs on the local database, in a rolled-back transaction, from the
snippets in .claude/skills/case-curate/sql/ and the files in
cases/PMC12949993/curation/. The same files and snippets go through the MCP to
the Case Vault once the catalogue is loaded there.

Normal templates count as approved here; on the Case Vault they need Atul's
approval first (catalogue review, L0.5).
"""

import json
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts import catalogue as cat
from scripts import curate_plan as plan

pytestmark = pytest.mark.integration

CASE_DIR = Path(__file__).resolve().parents[2] / "cases" / "PMC12949993"
CURATION = CASE_DIR / "curation"
CV = "PMC12949993@v1"
GENERATOR = "claude-opus-5-5 via case-curate v0.1"

# snippet -> (parameter, file in curation/). Missing files are skipped, so the
# test reports whatever is still open.
STEPS: tuple[tuple[str, str, str], ...] = (
    ("07_path_analysis.sql", "paths", "paths.json"),
    ("08b_affected.sql", "rows", "affected.json"),
    ("08d_rules.sql", "rows", "rules.json"),
    ("09a_reports.sql", "reports", "reports.json"),
    ("09b_consult_notes.sql", "notes", "consult_notes.json"),
    ("09c_lay_text.sql", "lay", "lay_text.json"),
    ("09d_test_utility.sql", "utility", "test_utility.json"),
    ("06_ground_truth.sql", "ground_truth", "ground_truth.json"),
)


def _run(db: psycopg.Connection, name: str, params: dict[str, Any]) -> None:
    snippet = next(s for s in plan.load_snippets() if s.name == name)
    with db.cursor() as cur:
        cur.execute(plan.render(snippet.sql, params))


def _load(file: str) -> Any:
    return json.loads((CURATION / file).read_text(encoding="utf-8"))


@pytest.fixture
def resolved(db: psycopg.Connection) -> psycopg.Connection:
    document = cat.build_document(cat.read_catalogue(cat.DEFAULT_DIR), version=0)
    for template in document["normal_templates"]:
        template["review_status"] = "approved"
    db.execute("select casevault.load_catalogue(%s::jsonb)", (json.dumps(document),))
    base = {"cv": CV, "generator": GENERATOR, "skill_version": "v0.1"}
    gold = json.loads((CASE_DIR / "gold-case-file.draft.json").read_text(encoding="utf-8"))
    _run(db, "04_import.sql", {**base, "doc": gold})
    _run(db, "08a_derived.sql", base)
    for snippet, param, file in STEPS[:3]:
        if (CURATION / file).exists():
            _run(db, snippet, {**base, param: _load(file)})
    _run(db, "08c_normals.sql", base)
    for snippet, param, file in STEPS[3:]:
        if (CURATION / file).exists():
            _run(db, snippet, {**base, param: _load(file)})
    return db


def test_coverage_is_complete(resolved: psycopg.Connection) -> None:
    gaps = resolved.execute(
        "select kind, item_id, component_id, day from casevault.coverage_gaps(%s)", (CV,)
    ).fetchall()
    assert gaps == []


def test_consistency_checks_pass(resolved: psycopg.Connection) -> None:
    problems = resolved.execute(
        "select check_name, rule_id, target, day, detail from casevault.check_consistency(%s)",
        (CV,),
    ).fetchall()
    assert problems == []


def test_nothing_a_player_sees_leaks_the_diagnosis(resolved: psycopg.Connection) -> None:
    assert resolved.execute("select * from casevault.leak_scan(%s)", (CV,)).fetchall() == []


def test_every_affected_row_has_a_rationale_and_confidence(resolved: psycopg.Connection) -> None:
    rows = resolved.execute(
        "select target from casevault.synthetic_ledger where case_version_id = %s"
        " and tier = 'affected' and (rationale is null or confidence is null)",
        (CV,),
    ).fetchall()
    assert rows == []


def test_every_history_fact_has_the_patients_words(resolved: psycopg.Connection) -> None:
    missing = resolved.execute(
        "select id from casevault.fact where case_version_id = %s and category = 'history'"
        " and release <> 'vignette' and lay_text is null",
        (CV,),
    ).fetchall()
    assert missing == []


def test_the_case_hands_over_to_review(resolved: psycopg.Connection) -> None:
    _run(resolved, "11_handover.sql", {"cv": CV, "generator": GENERATOR, "skill_version": "v0.1"})
    status = resolved.execute(
        "select status from casevault.case_version where id = %s", (CV,)
    ).fetchone()
    assert status == ("in_review",)
