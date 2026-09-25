"""casevault.import_case_json on the pilot draft (SPEC §4.4 step 4, PLAN L0.3 and L0.8)."""

from pathlib import Path

import psycopg
import psycopg.sql
import pytest

pytestmark = pytest.mark.integration

PILOT = Path(__file__).resolve().parents[2] / "cases" / "PMC12949993" / "gold-case-file.draft.json"
IMPORT = "select casevault.import_case_json(%s::jsonb, 'claude-test via case-curate v0.0', 'v0.0')"


def _import_pilot(db: psycopg.Connection) -> str:
    row = db.execute(IMPORT, (PILOT.read_text(encoding="utf-8"),)).fetchone()
    assert row is not None
    return str(row[0])


def _count(db: psycopg.Connection, table: str, cv: str) -> int:
    query = psycopg.sql.SQL("select count(*) from casevault.{} where case_version_id = %s").format(
        psycopg.sql.Identifier(table)
    )
    row = db.execute(query, (cv,)).fetchone()
    assert row is not None
    return int(row[0])


def test_pilot_imports_every_article_row(db: psycopg.Connection) -> None:
    cv = _import_pilot(db)

    assert cv == "PMC12949993@v1"
    counts = {
        t: _count(db, t, cv) for t in ("fact", "raw_material", "media", "gap", "ground_truth")
    }
    # 10 history + 125 series points + 26 single results; 3 raw material (PLAN L0.8).
    assert counts == {"fact": 161, "raw_material": 3, "media": 4, "gap": 20, "ground_truth": 1}


def test_series_expand_to_one_fact_per_day(db: psycopg.Connection) -> None:
    cv = _import_pilot(db)

    rows = db.execute(
        "select id, day, value_num, unit, flag, origin from casevault.fact"
        " where case_version_id = %s and id in ('S01.d-100', 'S01.d0') order by day",
        (cv,),
    ).fetchall()

    assert [(r[0], r[1], float(r[2]), r[3], r[4], r[5]) for r in rows] == [
        ("S01.d-100", -100, 127.0, "g/L", None, "article"),
        ("S01.d0", 0, 72.0, "g/L", "L", "article"),
    ]


def test_import_is_always_a_draft_with_provenance(db: psycopg.Connection) -> None:
    cv = _import_pilot(db)

    version = db.execute(
        "select status, schema_version, curated_by from casevault.case_version where id = %s", (cv,)
    ).fetchone()
    unrecorded = db.execute(
        "select count(*) from casevault.fact where case_version_id = %s"
        " and (generator is null or skill_version is null or review_status <> 'pending')",
        (cv,),
    ).fetchone()

    assert version == ("draft", "0.3", "curator")
    assert unrecorded == (0,)


def test_release_conditions_and_figure_flags(db: psycopg.Connection) -> None:
    cv = _import_pilot(db)

    condition = db.execute(
        "select release_condition ? 'requires_topics' from casevault.fact"
        " where case_version_id = %s and id = 'H10'",
        (cv,),
    ).fetchone()
    flagged = db.execute(
        "select count(*) from casevault.media where case_version_id = %s"
        " and (production_ok or public_release_ok)",
        (cv,),
    ).fetchone()

    assert condition == (True,)
    assert flagged == (0,)  # figures wait for Atul's own flags


def test_same_version_cannot_be_imported_twice(db: psycopg.Connection) -> None:
    _import_pilot(db)

    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        _import_pilot(db)


def test_import_needs_generator_and_skill_version(db: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.InvalidParameterValue), db.transaction():
        db.execute("select casevault.import_case_json('{\"case_id\": \"NID-9003\"}', null, 'v0')")
