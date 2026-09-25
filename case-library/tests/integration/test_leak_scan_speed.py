"""leak_scan is fast and finds exactly what the first version found.

On 2026-09-25 leak_scan over the ten Case Vault cases hit the statement timeout:
strip_phrases ran once for every pair of text row and term, sorting and looping
over some 1,600 allowed phrases each time. The first version is kept in
tests/fixtures/leak_scan_v0.sql and loaded into pg_temp, so each test compares
the two on the same replayed case, in a rolled-back transaction.

The real cases have no leaks, so the comparison also plants probe terms in the
ground truth: common words that sit inside test names ("blood", "culture") and
so exercise the stripping of allowed phrases on every kind of text row.
"""

import json
import time
from pathlib import Path

import psycopg
import pytest

from scripts import case_replay as cr
from tests.integration.conftest import FIXTURES, seed_mini_case

pytestmark = pytest.mark.integration

CASES = Path(__file__).resolve().parents[2] / "cases"
PILOT = CASES / "PMC12949993"
LARGEST = CASES / "PMC11890614"  # 4,101 ledger rows
SECONDS_PER_CASE = 1.0
PROBE_TERMS = (
    "blood",
    "blood culture",
    "count",
    "culture",
    "day",
    "level",
    "normal",
    "platelet",
    "serum",
    "white cell",
)
NEW = "select location, row_id, term from casevault.leak_scan(%s)"
OLD = "select location, row_id, term from pg_temp.leak_scan_v0(%s)"


def _load(db: psycopg.Connection, case_dir: Path) -> str:
    db.execute((FIXTURES / "leak_scan_v0.sql").read_text(encoding="utf-8"))
    db.execute(
        "select casevault.load_catalogue(%s::jsonb)",
        (json.dumps(cr.catalogue_document([case_dir])),),
    )
    return cr.load_case(db, case_dir)


def _plant_probe_terms(db: psycopg.Connection, cv: str) -> None:
    db.execute(
        "update casevault.ground_truth"
        " set final_dx = jsonb_set(final_dx, '{leak_terms}',"
        "   coalesce(final_dx -> 'leak_terms', '[]') || %s::jsonb)"
        " where case_version_id = %s",
        (json.dumps(PROBE_TERMS), cv),
    )


def _timed(db: psycopg.Connection, query: str, cv: str) -> tuple[list[tuple[str, ...]], float]:
    start = time.perf_counter()
    rows = db.execute(query, (cv,)).fetchall()
    return rows, time.perf_counter() - start


@pytest.mark.parametrize("case_dir", [PILOT, LARGEST], ids=lambda p: p.name)
def test_the_scan_is_fast_on_a_real_case(db: psycopg.Connection, case_dir: Path) -> None:
    cv = _load(db, case_dir)

    new, seconds = _timed(db, NEW, cv)

    assert seconds < SECONDS_PER_CASE
    assert new == []  # as the Case Vault recorded for every case of batch 1


@pytest.mark.parametrize("case_dir", [PILOT, LARGEST], ids=lambda p: p.name)
def test_the_scan_is_unchanged_when_many_terms_match(
    db: psycopg.Connection, case_dir: Path
) -> None:
    cv = _load(db, case_dir)
    _plant_probe_terms(db, cv)

    new, seconds = _timed(db, NEW, cv)

    assert seconds < SECONDS_PER_CASE
    assert len(new) > 100
    assert {r[0] for r in new} >= {"synthetic_ledger", "report"}
    assert new == db.execute(OLD, (cv,)).fetchall()


def test_stripping_an_allowed_phrase_can_open_a_word_boundary(db: psycopg.Connection) -> None:
    """'blood lead level' glued between two words leaves them as separate words."""
    db.execute((FIXTURES / "leak_scan_v0.sql").read_text(encoding="utf-8"))
    cv = seed_mini_case(db)
    db.execute(
        "update casevault.case_version set vignette = 'Pallorblood lead levelplumbism.'"
        " where id = %s",
        (cv,),
    )

    new = db.execute(NEW, (cv,)).fetchall()

    assert new == [("case_version.vignette", cv, "plumbism")]
    assert new == db.execute(OLD, (cv,)).fetchall()


def test_strip_phrases_blanks_the_longest_phrase_first(db: psycopg.Connection) -> None:
    row = db.execute(
        "select casevault.strip_phrases('Blood Lead Level and lead level',"
        " '{lead level,blood lead level}')"
    ).fetchone()

    assert row == ("  and  ",)
