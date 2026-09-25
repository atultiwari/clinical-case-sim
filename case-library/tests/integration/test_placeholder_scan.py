"""No reviewer placeholder or authoring note reaches a player (PLAN L0.10).

The pilot reached review with "[to be set by the reviewer]" in three marrow
reports; leak_scan looks only for diagnosis terms. placeholder_scan looks at the
same player-visible text for placeholders and authoring notes, and
export_blockers and step 10 of the skill report what it finds.
"""

import json
import re
from pathlib import Path
from typing import Any

import psycopg
import psycopg.sql
import pytest

from scripts import curate_plan as plan
from tests.integration.conftest import MINI_GENERATOR, seed_mini_case

pytestmark = pytest.mark.integration

PILOT_REPORTS = Path(__file__).resolve().parents[2] / "cases/PMC12949993/curation/reports.json"
# The file-level test's pattern (tests/test_curation_placeholders.py).
FILE_PATTERN = re.compile(r"to be set|set by the reviewer|\bTBD\b|\bplaceholder\b", re.IGNORECASE)


def _scan(db: psycopg.Connection, cv: str) -> list[tuple[str, str, str]]:
    return db.execute("select * from casevault.placeholder_scan(%s)", (cv,)).fetchall()


def _add_report(db: psycopg.Connection, cv: str, rid: str, **cols: Any) -> None:
    row = {"report_text": "Normal.", "impression": None, "status_line": None,
           "findings": [], "review_status": "pending", **cols}  # fmt: skip
    db.execute(
        "insert into casevault.report (case_version_id, id, test_item_id, variant, status,"
        " status_line, findings, report_text, impression, review_status, generator,"
        " skill_version) values (%(cv)s, %(id)s, 'LAB.FILM', 'only', 'final', %(status_line)s,"
        " %(findings)s, %(report_text)s, %(impression)s, %(review_status)s, %(g)s, 'v0')",
        {**row, "cv": cv, "id": rid, "g": MINI_GENERATOR},
    )


def _add_note(db: psycopg.Connection, cv: str, nid: str, note: str, recs: list[str]) -> None:
    db.execute(
        "insert into casevault.consult_note (case_version_id, id, specialty, note_text,"
        " recommendations, origin, rationale, confidence, generator, skill_version) values"
        " (%s, %s, 'REF.TOXICOLOGY', %s, %s, 'affected', 'r', 0.8, %s, 'v0')",
        (cv, nid, note, recs, MINI_GENERATOR),
    )


def _add_ledger(db: psycopg.Connection, cv: str, tier: str, **cols: Any) -> str:
    row = {"value": {"value": 75}, "release_text": None, "lay_text": None,
           "review_status": "pending", **cols}  # fmt: skip
    result = db.execute(
        "insert into casevault.synthetic_ledger (case_version_id, target, day_bucket, tier,"
        " value, release_text, lay_text, rationale, confidence, review_status, generator,"
        " skill_version) values (%(cv)s, 'CMP.HB', 1, %(tier)s, %(value)s, %(release_text)s,"
        " %(lay_text)s, 'r', 0.7, %(review_status)s, %(g)s, 'v0') returning id::text",
        {**row, "value": json.dumps(row["value"]), "cv": cv, "tier": tier, "g": MINI_GENERATOR},
    ).fetchone()
    assert result is not None
    return str(result[0])


@pytest.fixture
def cv(db: psycopg.Connection) -> str:
    """The fixture case with a clean report and consult note."""
    cv = seed_mini_case(db)
    _add_report(db, cv, "RP01", report_text="Coarse basophilic stippling [see Figure 1].",
                findings=["FND.STIPPLING"])  # fmt: skip
    _add_note(db, cv, "CN01", "Happy to see her; keep for review in clinic.", ["Repeat the film"])
    return cv


def test_a_clean_case_has_no_placeholders(db: psycopg.Connection, cv: str) -> None:
    assert _scan(db, cv) == []


@pytest.mark.parametrize(
    ("cols", "location", "match"),
    [
        ({"report_text": "Blasts [to be set by the reviewer]. Iron stain."},
         "report.report_text", "[to be set by the reviewer]"),
        ({"impression": "Marrow findings TBD."}, "report.impression", "TBD"),
        ({"status_line": "Placeholder: final report pending."}, "report.status_line",
         "Placeholder"),
        ({"findings": ["FND.STIPPLING", "value set by the reviewer"]}, "report.findings",
         "set by the reviewer"),
        ({"report_text": "Film shows [INSERT MCV] microcytes."}, "report.report_text",
         "[INSERT MCV]"),
        ({"report_text": "Stippling seen. (Generator: soften this for players)"},
         "report.report_text", "(Generator"),
    ],
)  # fmt: skip
def test_report_placeholders_are_found(
    db: psycopg.Connection, cv: str, cols: dict[str, Any], location: str, match: str
) -> None:
    _add_report(db, cv, "RP02", **cols)
    hits = _scan(db, cv)
    assert [(loc, rid) for loc, rid, _ in hits] == [(location, "RP02")]
    assert match in hits[0][2]


def test_consult_note_placeholders_are_found(db: psycopg.Connection, cv: str) -> None:
    _add_note(db, cv, "CN02", "Chelation advised. (Better: name the agent)",
              ["Dose to be set", "Repeat lead in a week"])  # fmt: skip
    assert [(loc, rid) for loc, rid, _ in _scan(db, cv)] == [
        ("consult_note.note_text", "CN02"),
        ("consult_note.recommendations", "CN02"),
    ]


@pytest.mark.parametrize(
    ("cols", "location"),
    [
        ({"value": {"text": "TBD"}}, "synthetic_ledger.value"),
        ({"release_text": "Haemoglobin [to be confirmed] g/L"}, "synthetic_ledger.release_text"),
        ({"lay_text": "My blood was low (Keep for day 2)"}, "synthetic_ledger.lay_text"),
    ],
)
def test_live_ledger_placeholders_are_found(
    db: psycopg.Connection, cv: str, cols: dict[str, Any], location: str
) -> None:
    row_id = _add_ledger(db, cv, "affected", **cols)
    assert [(loc, rid) for loc, rid, _ in _scan(db, cv)] == [(location, row_id)]


def test_reviewer_rows_are_placeholders_by_design(db: psycopg.Connection, cv: str) -> None:
    _add_ledger(db, cv, "reviewer", value={"text": "To be set by the reviewer"})
    assert _scan(db, cv) == []


@pytest.mark.parametrize("status", ["rejected", "superseded"])
def test_rows_no_longer_live_are_skipped(db: psycopg.Connection, cv: str, status: str) -> None:
    _add_report(db, cv, "RP02", report_text="Blasts TBD.")
    row_id = _add_ledger(db, cv, "affected", value={"text": "TBD"})
    db.execute(
        "update casevault.report set review_status = %s where case_version_id = %s and id = 'RP02'",
        (status, cv),
    )
    db.execute("update casevault.synthetic_ledger set review_status = %s, reviewed_by = 'reviewer',"
               " reviewed_at = now() where id = %s",
               (status, row_id))  # fmt: skip
    assert _scan(db, cv) == []


def test_fact_lay_text_is_scanned_unless_never_released(db: psycopg.Connection, cv: str) -> None:
    db.execute(
        "update casevault.fact set lay_text = 'Tired (Generator: make it warmer)'"
        " where case_version_id = %s and id in ('H01', 'H02')",
        (cv,),
    )
    db.execute(
        "update casevault.fact set release = 'never' where case_version_id = %s and id = 'H02'",
        (cv,),
    )
    assert [(loc, rid) for loc, rid, _ in _scan(db, cv)] == [("fact.lay_text", "H01")]


def test_the_case_and_version_texts_are_scanned(db: psycopg.Connection, cv: str) -> None:
    db.execute(
        "update casevault.case_version set vignette = vignette || ' [add the age]',"
        " opening_statement_lay = 'TBD' where id = %s",
        (cv,),
    )
    db.execute(
        "update casevault.\"case\" set display_title = 'Placeholder title'"
        " where id = (select case_id from casevault.case_version where id = %s)",
        (cv,),
    )
    case_id = cv.split("@")[0]
    assert [(loc, rid) for loc, rid, _ in _scan(db, cv)] == [
        ("case.display_title", case_id),
        ("case_version.opening_statement_lay", cv),
        ("case_version.vignette", cv),
    ]


@pytest.mark.parametrize(
    "text",
    [
        "Normal range [4.0-11.0] x10^9/L.",
        "Settled by the reviewer's standards",
        "TBDX is not a word; placebo given.",
        "Keep for observation overnight.",
        "Better now than yesterday.",
    ],
)
def test_clinical_text_is_not_flagged(db: psycopg.Connection, cv: str, text: str) -> None:
    _add_report(db, cv, "RP02", report_text=text)
    assert _scan(db, cv) == []


def test_the_snippet_is_short_and_shows_the_match(db: psycopg.Connection, cv: str) -> None:
    long_text = "x " * 200 + "Blasts [to be set by the reviewer]." + " y" * 200
    _add_report(db, cv, "RP02", report_text=long_text)
    ((_, _, snippet),) = _scan(db, cv)
    assert "[to be set by the reviewer]" in snippet
    assert len(snippet) <= 120


def test_another_case_versions_text_is_not_reported(db: psycopg.Connection, cv: str) -> None:
    db.execute(
        "insert into casevault.case_version (id, case_id, version, vignette)"
        " select case_id || '@v2', case_id, 2, 'TBD' from casevault.case_version where id = %s",
        (cv,),
    )
    assert _scan(db, cv) == []


def test_export_blockers_list_placeholders(db: psycopg.Connection, cv: str) -> None:
    _add_report(db, cv, "RP02", report_text="Blasts [to be set by the reviewer].")
    blockers = [r[0] for r in db.execute("select casevault.export_blockers(%s)", (cv,))]
    assert 'placeholder: report.report_text RP02: "Blasts [to be set by the reviewer]."' in (
        blockers
    )


def test_step_10_reports_placeholders(db: psycopg.Connection, cv: str) -> None:
    _add_report(db, cv, "RP02", impression="TBD")
    snippet = next(s for s in plan.load_snippets() if s.name == "10_checks.sql")
    problems = db.execute(plan.render(snippet.sql, {"cv": cv})).fetchall()
    assert ("placeholder", "report.impression RP02: TBD") in problems


def test_the_reader_can_run_the_scan(db: psycopg.Connection, cv: str) -> None:
    db.execute("set local role casevault_reader")
    assert _scan(db, cv) == []


@pytest.mark.parametrize("role", ["anon", "authenticated"])
def test_player_roles_cannot_run_the_scan(db: psycopg.Connection, cv: str, role: str) -> None:
    db.execute(psycopg.sql.SQL("set local role {}").format(psycopg.sql.Identifier(role)))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _scan(db, cv)


def test_the_pilot_scan_matches_the_curation_files(db: psycopg.Connection) -> None:
    """The database finds the same pilot reports as the file-level test would."""
    reports = json.loads(PILOT_REPORTS.read_text(encoding="utf-8"))
    expected = sorted(
        r["id"] for r in reports
        if FILE_PATTERN.search(json.dumps([r.get("report_text"), r.get("impression"),
                                           r.get("status_line"), r.get("findings")]))
    )  # fmt: skip
    cv = seed_mini_case(db)
    for r in reports:
        _add_report(db, cv, r["id"], report_text=r.get("report_text"),
                    impression=r.get("impression"), status_line=r.get("status_line"),
                    findings=r.get("findings") or [])  # fmt: skip
    assert sorted({rid for loc, rid, _ in _scan(db, cv) if loc.startswith("report.")}) == expected
