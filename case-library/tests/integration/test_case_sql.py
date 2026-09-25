"""A rendered case file lands whole in `in_review`, or not at all (PLAN L1.3)."""

import json
import shutil
from pathlib import Path

import psycopg
import pytest

from scripts.case_replay import catalogue_document
from scripts.case_sql import render_case, render_case_body

pytestmark = pytest.mark.integration

PILOT = Path(__file__).resolve().parents[2] / "cases" / "PMC12949993"


def _load_catalogue(db: psycopg.Connection) -> None:
    db.execute("select casevault.load_catalogue(%s::jsonb)", (json.dumps(catalogue_document([])),))


def test_the_rendered_pilot_hands_over_with_nothing_open(db: psycopg.Connection) -> None:
    _load_catalogue(db)
    db.execute(render_case_body(PILOT))
    status = db.execute(
        "select status from casevault.case_version where id = 'PMC12949993@v1'"
    ).fetchone()
    assert status == ("in_review",)


def test_the_rendered_file_is_one_ascii_transaction() -> None:
    sql = render_case(PILOT)
    assert sql.startswith("begin;\n")
    assert sql.endswith("commit;\n")
    json_literals = [line for line in sql.splitlines() if "::jsonb" in line]
    assert json_literals
    assert all(line.isascii() for line in json_literals)


def test_an_open_problem_stops_the_hand_over(db: psycopg.Connection, tmp_path: Path) -> None:
    case = tmp_path / "PMC12949993"
    shutil.copytree(PILOT, case)
    (case / "curation" / "consult_notes.json").unlink()  # every referral is left uncovered
    _load_catalogue(db)
    with pytest.raises(psycopg.errors.RaiseException, match="not handed over"):
        db.execute(render_case_body(case))
