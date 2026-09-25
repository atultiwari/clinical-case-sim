"""A patch turns the case as loaded into the corrected case exactly (PLAN L1.3)."""

import json
import shutil
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts.case_patch import CONTENT, LEDGER_CONTENT, patch_sql, render_patch, same, snapshot
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
