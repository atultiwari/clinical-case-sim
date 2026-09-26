"""leak_scan is fast and does not depend on the order of the allowed phrases.

On 2026-09-25 leak_scan over the ten Case Vault cases hit the statement timeout:
strip_phrases ran once for every pair of text row and term, sorting and looping
over some 1,600 allowed phrases each time. The first version is kept in
tests/fixtures/leak_scan_v0.sql and loaded into pg_temp, so tests can compare
the two on the same replayed case, in a rolled-back transaction.

The first version blanked phrases one after another, longest first, so when two
allowed phrases of the same length overlapped ("blood lead" and "lead level" in
"blood lead level"), whichever the sort put first decided which word was left
over. strip_phrases now blanks every stretch of text that any allowed phrase
covers, in one pass. Where phrases do not overlap, that is what the first
version did; where they do, it blanks more, so the scan reports a subset of
what the first version reported, whatever the order.

The real cases have no leaks, so the comparisons also plant probe terms in the
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
ALLOWED = """
select coalesce(array_agg(distinct lower(a)), '{}') from (
  select jsonb_array_elements_text(coalesce(final_dx -> 'allowed_phrases', '[]')) as a
  from casevault.ground_truth where case_version_id = %(cv)s
  union all select name from casevault.catalogue_item where kind = 'test'
  union all select unnest(synonyms) from casevault.catalogue_item where kind = 'test'
) a
"""
PROSE = """
select concat_ws(' | ', value, release_text, lay_text) from casevault.fact
where case_version_id = %(cv)s
union all
select concat_ws(' | ', report_text, impression, status_line) from casevault.report
where case_version_id = %(cv)s
union all
select concat_ws(' | ', note_text, array_to_string(recommendations, ' | '))
from casevault.consult_note where case_version_id = %(cv)s
"""


def reference_strip(lowered: str, phrases: list[str]) -> str:
    """Blank every stretch any phrase covers; overlapping stretches become one space."""
    spans: list[tuple[int, int]] = []
    for phrase in phrases:
        if not phrase:
            continue
        at = lowered.find(phrase)
        while at >= 0:
            spans.append((at, at + len(phrase)))
            at = lowered.find(phrase, at + 1)
    out: list[str] = []
    pos = 0
    run_start, run_end = -1, -1
    for start, end in sorted(spans):
        if start < run_end:
            run_end = max(run_end, end)
            continue
        if run_end >= 0:
            out.append(lowered[pos:run_start] + " ")
            pos = run_end
        run_start, run_end = start, end
    if run_end >= 0:
        out.append(lowered[pos:run_start] + " ")
        pos = run_end
    return "".join(out) + lowered[pos:]


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


def _strip(db: psycopg.Connection, text: str, phrases: list[str]) -> str:
    row = db.execute("select casevault.strip_phrases(%s, %s)", (text, phrases)).fetchone()
    assert row is not None
    return str(row[0])


# --- Speed and the replayed cases --------------------------------------------


@pytest.mark.parametrize("case_dir", [PILOT, LARGEST], ids=lambda p: p.name)
def test_the_scan_is_fast_on_a_real_case(db: psycopg.Connection, case_dir: Path) -> None:
    cv = _load(db, case_dir)

    new, seconds = _timed(db, NEW, cv)

    assert seconds < SECONDS_PER_CASE
    assert new == []  # as the Case Vault recorded for every case of batch 1


@pytest.mark.parametrize("case_dir", [PILOT, LARGEST], ids=lambda p: p.name)
def test_the_scan_reports_what_the_first_version_did_less_the_overlaps(
    db: psycopg.Connection, case_dir: Path
) -> None:
    cv = _load(db, case_dir)
    _plant_probe_terms(db, cv)

    new, seconds = _timed(db, NEW, cv)
    old = db.execute(OLD, (cv,)).fetchall()

    assert seconds < SECONDS_PER_CASE
    assert len(new) > 100
    assert {r[0] for r in new} >= {"synthetic_ledger", "report"}
    assert set(new) <= set(old)
    assert len(old) - len(new) < 0.05 * len(old)


@pytest.mark.parametrize("case_dir", [PILOT, LARGEST], ids=lambda p: p.name)
def test_strip_phrases_matches_the_reference_on_every_prose_row(
    db: psycopg.Connection, case_dir: Path
) -> None:
    cv = _load(db, case_dir)
    row = db.execute(ALLOWED, {"cv": cv}).fetchone()
    assert row is not None
    phrases = list(row[0])
    texts = [str(r[0]) for r in db.execute(PROSE, {"cv": cv}).fetchall()]
    lowered = [str(r[0]) for r in db.execute("select lower(t) from unnest(%s::text[]) t", (texts,))]

    stripped = [
        str(r[0])
        for r in db.execute(
            "select casevault.strip_phrases(t, %s) from unnest(%s::text[]) with ordinality u(t, n)"
            " order by n",
            (phrases, texts),
        )
    ]

    assert len(texts) > 50
    assert stripped == [reference_strip(t, phrases) for t in lowered]


# --- The rules of stripping --------------------------------------------------


def test_overlapping_phrases_are_blanked_whatever_their_order(db: psycopg.Connection) -> None:
    text = "Send a blood lead level today"

    one = _strip(db, text, ["blood lead", "lead level"])
    other = _strip(db, text, ["lead level", "blood lead"])

    assert one == other == "send a   today"


def test_repeated_overlapping_occurrences_are_all_blanked(db: psycopg.Connection) -> None:
    assert _strip(db, "xaaay", ["aa"]) == "x y"


def test_strip_phrases_blanks_a_phrase_inside_a_longer_one_once(db: psycopg.Connection) -> None:
    text = "Blood Lead Level and lead level"

    assert _strip(db, text, ["lead level", "blood lead level"]) == "  and  "


def test_empty_and_null_inputs(db: psycopg.Connection) -> None:
    assert _strip(db, "Some Text", []) == "some text"
    assert _strip(db, "Some Text", ["", "text"]) == "some  "
    row = db.execute("select casevault.strip_phrases(null, '{text}')").fetchone()
    assert row == ("",)


def test_the_scan_ignores_the_order_of_overlapping_allowed_phrases(
    db: psycopg.Connection,
) -> None:
    """'serum iron' and 'iron panel' overlap and have the same length."""
    cv = seed_mini_case(db)
    db.execute(
        "update casevault.ground_truth set final_dx = final_dx || %s::jsonb"
        " where case_version_id = %s",
        (
            json.dumps(
                {"allowed_phrases": ["serum iron", "iron panel"], "leak_terms": ["serum", "panel"]}
            ),
            cv,
        ),
    )
    db.execute(
        "update casevault.case_version set vignette = 'Send a serum iron panel.' where id = %s",
        (cv,),
    )

    assert db.execute(NEW, (cv,)).fetchall() == []


def test_stripping_an_allowed_phrase_can_open_a_word_boundary(db: psycopg.Connection) -> None:
    """'blood lead level' glued between two words leaves them as separate words."""
    cv = seed_mini_case(db)
    db.execute(
        "update casevault.case_version set vignette = 'Pallorblood lead levelplumbism.'"
        " where id = %s",
        (cv,),
    )

    assert db.execute(NEW, (cv,)).fetchall() == [("case_version.vignette", cv, "plumbism")]


def test_the_reference_blanks_overlaps_as_one_space() -> None:
    assert reference_strip("send a blood lead level", ["lead level", "blood lead"]) == "send a  "
    assert reference_strip("ab cd", ["zz"]) == "ab cd"
    assert reference_strip("xaaay", ["aa", ""]) == "x y"
