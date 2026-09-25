"""Every gold case file in cases/ imports cleanly on the current catalogue (SPEC §4.4 step 4).

Each file is imported in a rolled-back transaction, as the skill's step 4 does
through the MCP: every catalogue link names a real item or component, history
facts name the questions that release them, and nothing a player sees leaks
the diagnosis.
"""

import json
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts import catalogue as cat

pytestmark = pytest.mark.integration

CASES = Path(__file__).resolve().parents[2] / "cases"
GOLD_FILES = sorted(CASES.glob("*/gold-case-file*.json"))


def _import(db: psycopg.Connection, path: Path) -> str:
    document = cat.build_document(cat.read_catalogue(cat.DEFAULT_DIR), version=0)
    db.execute("select casevault.load_catalogue(%s::jsonb)", (json.dumps(document),))
    row = db.execute(
        "select casevault.import_case_json(%s::jsonb, 'claude-test via case-curate v0.1', 'v0.1')",
        (path.read_text(encoding="utf-8"),),
    ).fetchone()
    assert row is not None
    return str(row[0])


def _rows(db: psycopg.Connection, query: str, cv: str) -> list[tuple[Any, ...]]:
    return db.execute(query, (cv,)).fetchall()


@pytest.mark.parametrize("path", GOLD_FILES, ids=lambda p: p.parent.name)
def test_the_gold_file_imports_and_links(db: psycopg.Connection, path: Path) -> None:
    cv = _import(db, path)
    bad_components = _rows(
        db,
        "select f.id, f.catalogue_ref from casevault.fact f where f.case_version_id = %s"
        " and f.category <> 'history' and f.catalogue_ref is not null"
        " and not exists (select 1 from casevault.component c where c.id = f.catalogue_ref)",
        cv,
    )
    bad_items = _rows(
        db,
        "select f.id, r from casevault.fact f, unnest(f.released_by) r"
        " where f.case_version_id = %s"
        " and not exists (select 1 from casevault.catalogue_item i where i.id = r)",
        cv,
    )
    unlinked_history = _rows(
        db,
        "select id from casevault.fact where case_version_id = %s and category = 'history'"
        " and release = 'chart' and cardinality(released_by) = 0",
        cv,
    )
    assert (bad_components, bad_items, unlinked_history) == ([], [], [])


@pytest.mark.parametrize("path", GOLD_FILES, ids=lambda p: p.parent.name)
def test_the_gold_file_has_a_laboratory_profile(path: Path) -> None:
    profile = json.loads(path.read_text(encoding="utf-8")).get("case", {}).get("lab_profile", {})
    assert profile.get("sex") in {"F", "M"}
    assert isinstance(profile.get("age_years"), int | float)


@pytest.mark.parametrize("path", GOLD_FILES, ids=lambda p: p.parent.name)
def test_nothing_a_player_sees_leaks(db: psycopg.Connection, path: Path) -> None:
    cv = _import(db, path)
    assert _rows(db, "select * from casevault.leak_scan(%s)", cv) == []
