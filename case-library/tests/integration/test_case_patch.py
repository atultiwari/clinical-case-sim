"""A patch turns the case as loaded into the corrected case exactly (PLAN L1.3)."""

import json
import shutil
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts.case_patch import (
    CONTENT,
    LEDGER_CONTENT,
    PatchError,
    patch_sql,
    render_patch,
    same,
    snapshot,
)
from scripts.case_replay import catalogue_document, replay_one
from scripts.case_sql import render_case_body

pytestmark = pytest.mark.integration

PILOT = Path(__file__).resolve().parents[2] / "cases" / "PMC12949993"
CV, CASE_ID = "PMC12949993@v1", "PMC12949993"


def _corrected_copy(tmp_path: Path) -> Path:
    """The pilot with one value changed and one affected history row replaced by a fact."""
    case = tmp_path / "PMC12949993"
    shutil.copytree(PILOT, case)
    affected_file = case / "curation" / "affected.json"
    affected: list[dict[str, Any]] = json.loads(affected_file.read_text(encoding="utf-8"))
    affected[0]["release_text"] = (affected[0].get("release_text") or "") + " (corrected)"
    replaced = next(
        r
        for r in affected[1:]
        if r["target"].startswith("HX.") and r["day_bucket"] is None and r["tier"] == "affected"
    )
    affected.remove(replaced)
    affected_file.write_text(json.dumps(affected), encoding="utf-8")
    gold_file = case / "gold-case-file.draft.json"
    gold = json.loads(gold_file.read_text(encoding="utf-8"))
    gold["facts"].append(
        {
            **gold["facts"][-1],
            "id": "H99",
            "item": "Answer now taken from the article",
            "released_by": [replaced["target"]],
        }
    )
    gold_file.write_text(json.dumps(gold), encoding="utf-8")
    return case


def _body(sql: str) -> str:
    return sql[len("begin;\n") : sql.rstrip().rfind("commit;")]


def test_the_patch_reproduces_the_corrected_case(db: psycopg.Connection, tmp_path: Path) -> None:
    corrected = _corrected_copy(tmp_path)
    db.execute("select casevault.load_catalogue(%s::jsonb)", (json.dumps(catalogue_document([])),))
    with db.transaction(force_rollback=True):
        replay_one(db, PILOT)
        old = snapshot(db, CV, CASE_ID)
    with db.transaction(force_rollback=True):
        replay_one(db, corrected)
        new = snapshot(db, CV, CASE_ID)
    patch = patch_sql(old, new, CV, "atul", "test correction")
    assert patch.counts.get("ledger rejected", 0) >= 1
    assert patch.counts.get("ledger superseded", 0) >= 1
    assert patch.counts.get("fact inserted") == 1

    db.execute(render_case_body(PILOT))  # as loaded, handed over to review
    db.execute(_body(render_patch(patch)))
    got = snapshot(db, CV, CASE_ID)
    for table in CONTENT:
        assert got[table].keys() == new[table].keys(), table
        assert all(same(got[table][k], new[table][k]) for k in new[table]), table
    assert got["ledger"].keys() == new["ledger"].keys()
    assert all(same(got["ledger"][k], new["ledger"][k], LEDGER_CONTENT) for k in new["ledger"])
    rejected = db.execute(
        "select reviewed_by, review_note from casevault.synthetic_ledger"
        " where case_version_id = %s and review_status = 'rejected'",
        (CV,),
    ).fetchall()
    assert rejected
    assert set(rejected) == {("atul", "test correction")}


# --- Corrections after review ------------------------------------------------

REVIEWED = ("fact", "report", "consult_note")


def _approve_everything(db: psycopg.Connection) -> None:
    """What a blanket approval leaves: every pending row reviewed by Atul."""
    for table, status in (*((t, "approved") for t in REVIEWED[1:]), ("fact", "verified")):
        db.execute(
            f"update casevault.{table} set review_status = %s, reviewed_by = 'atul',"  # noqa: S608
            " reviewed_at = now(), review_note = 'blanket' where case_version_id = %s"
            " and review_status = 'pending'",
            (status, CV),
        )
    db.execute(
        "update casevault.synthetic_ledger set review_status = 'approved', reviewed_by = 'atul',"
        " reviewed_at = now(), review_note = 'blanket' where case_version_id = %s"
        " and review_status = 'pending'",
        (CV,),
    )


def _reviewed_correction(tmp_path: Path) -> tuple[Path, str, str]:
    """The pilot with one ledger value and one report text changed; nothing removed."""
    case = tmp_path / "PMC12949993"
    shutil.copytree(PILOT, case)
    affected_file = case / "curation" / "affected.json"
    affected: list[dict[str, Any]] = json.loads(affected_file.read_text(encoding="utf-8"))
    affected[0]["release_text"] = (affected[0].get("release_text") or "") + " (corrected)"
    affected_file.write_text(json.dumps(affected), encoding="utf-8")
    reports_file = case / "curation" / "reports.json"
    reports: list[dict[str, Any]] = json.loads(reports_file.read_text(encoding="utf-8"))
    reports[0]["report_text"] = reports[0]["report_text"] + " Corrected after review."
    reports_file.write_text(json.dumps(reports), encoding="utf-8")
    return case, affected[0]["target"], reports[0]["id"]


def _snapshots(db: psycopg.Connection, corrected: Path) -> tuple[Any, Any]:
    db.execute("select casevault.load_catalogue(%s::jsonb)", (json.dumps(catalogue_document([])),))
    with db.transaction(force_rollback=True):
        replay_one(db, PILOT)
        old = snapshot(db, CV, CASE_ID)
    with db.transaction(force_rollback=True):
        replay_one(db, corrected)
        new = snapshot(db, CV, CASE_ID)
    return old, new


def test_a_correction_after_review_reopens_only_what_it_changes(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    corrected, target, report_id = _reviewed_correction(tmp_path)
    old, new = _snapshots(db, corrected)
    patch = patch_sql(old, new, CV, "atul", "second review", after_review=True)
    db.execute(render_case_body(PILOT))
    _approve_everything(db)

    db.execute(_body(render_patch(patch)))

    ledger: dict[str, int] = dict(
        db.execute(
            "select review_status, count(*) from casevault.synthetic_ledger"
            " where case_version_id = %s group by 1",
            (CV,),
        ).fetchall()
    )
    assert ledger["superseded"] == patch.counts["ledger superseded"] >= 1
    assert ledger["pending"] == patch.counts["ledger superseded"]
    assert "rejected" not in ledger
    live = db.execute(
        "select review_status, supersedes is not null from casevault.synthetic_ledger"
        " where case_version_id = %s and target = %s and casevault.is_live(review_status)",
        (CV, target),
    ).fetchall()
    assert ("pending", True) in live
    report = db.execute(
        "select review_status, reviewed_by, reviewed_at, review_note from casevault.report"
        " where case_version_id = %s and id = %s",
        (CV, report_id),
    ).fetchone()
    assert report == ("pending", None, None, None)
    untouched = db.execute(
        "select count(*) from casevault.report where case_version_id = %s"
        " and id <> %s and review_status <> 'approved'",
        (CV, report_id),
    ).fetchone()
    assert untouched == (0,)


def test_a_correction_after_review_cannot_withdraw_a_ledger_value(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    old, new = _snapshots(db, _corrected_copy(tmp_path))

    with pytest.raises(PatchError, match="replace"):
        patch_sql(old, new, CV, "atul", "second review", after_review=True)
