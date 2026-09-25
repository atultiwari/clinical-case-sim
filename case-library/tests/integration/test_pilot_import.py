"""The pilot, PMC12949993@v1, imports cleanly on top of catalogue v0 (PLAN L0.8).

Runs on the local database inside a rolled-back transaction, exactly as the
case-curate skill's step 4 and step 8a run through the MCP on the Case Vault.
"""

import json
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts import catalogue as cat
from scripts import curate_plan as plan

pytestmark = pytest.mark.integration

CASE_LIBRARY = Path(__file__).resolve().parents[2]
GOLD = CASE_LIBRARY / "cases" / "PMC12949993" / "gold-case-file.draft.json"
CV = "PMC12949993@v1"
GENERATOR = "claude-opus-5-5 via case-curate v0.1"


def _snippet(db: psycopg.Connection, name: str, params: dict[str, Any]) -> Any:
    snippet = next(s for s in plan.load_snippets() if s.name == name)
    row = db.execute(plan.render(snippet.sql, params)).fetchone()
    return None if row is None else row[0]


@pytest.fixture
def pilot(db: psycopg.Connection) -> psycopg.Connection:
    """Catalogue v0 and the pilot, imported and derived, as the skill does it."""
    document = cat.build_document(cat.read_catalogue(cat.DEFAULT_DIR), version=0)
    db.execute("select casevault.load_catalogue(%s::jsonb)", (json.dumps(document),))
    params = {
        "doc": json.loads(GOLD.read_text(encoding="utf-8")),
        "generator": GENERATOR,
        "skill_version": "v0.1",
        "cv": CV,
    }
    assert _snippet(db, "04_import.sql", params) == CV
    _snippet(db, "08a_derived.sql", params)
    return db


def _count(db: psycopg.Connection, query: str) -> int:
    row = db.execute(query, (CV,)).fetchone()
    assert row is not None
    return int(row[0])


def test_the_article_facts_and_raw_material_import(pilot: psycopg.Connection) -> None:
    by_category: dict[str, int] = dict(
        pilot.execute(
            "select category, count(*) from casevault.fact where case_version_id = %s"
            " and origin = 'article' group by category",
            (CV,),
        ).fetchall()
    )
    assert by_category.pop("history") == 10
    # 125 series values and 35 single results: the 26 in the draft, with composite
    # results (DAT, blood group, electrophoresis, immunoglobulins, light chains, EBV)
    # split into one fact per catalogue component.
    assert sum(by_category.values()) == 125 + 35
    assert (
        _count(pilot, "select count(*) from casevault.raw_material where case_version_id = %s") == 3
    )


def test_derived_rows_follow_the_formulas(pilot: psycopg.Connection) -> None:
    derived: dict[str, int] = dict(
        pilot.execute(
            "select catalogue_ref, count(*) from casevault.fact where case_version_id = %s"
            " and origin = 'derived' group by catalogue_ref",
            (CV,),
        ).fetchall()
    )
    assert derived.get("CMP.MCH", 0) >= 7
    assert derived.get("CMP.MCHC", 0) >= 7
    mch = pilot.execute(
        "select value_num from casevault.fact where case_version_id = %s"
        " and catalogue_ref = 'CMP.MCH' and day = 0",
        (CV,),
    ).fetchone()
    assert mch is not None
    assert 29 <= float(mch[0]) <= 31  # Hb 72 g/L / RBC 2.4 = 30 pg (ANALYSIS.md §6)


def test_every_linked_result_names_a_real_component(pilot: psycopg.Connection) -> None:
    unknown = pilot.execute(
        "select f.id, f.catalogue_ref from casevault.fact f where f.case_version_id = %s"
        " and f.catalogue_ref is not null and f.category <> 'history'"
        " and not exists (select 1 from casevault.component c where c.id = f.catalogue_ref)",
        (CV,),
    ).fetchall()
    assert unknown == []
    unlinked = pilot.execute(
        "select distinct f.item from casevault.fact f where f.case_version_id = %s"
        " and f.origin = 'article' and f.category <> 'history' and f.catalogue_ref is null",
        (CV,),
    ).fetchall()
    assert unlinked == [("Haemolysis index (sample)",)]  # a sample-quality flag, not a result


def test_figures_carry_their_licence_and_annotation_flag(pilot: psycopg.Connection) -> None:
    rows = pilot.execute(
        "select id, licence, production_ok, public_release_ok, has_annotations, file_path,"
        " production_decision from casevault.media where case_version_id = %s order by id",
        (CV,),
    ).fetchall()
    assert [r[0] for r in rows] == ["M01", "M02", "M03", "M04"]
    for _, licence, prod, public, annotated, _, decision in rows:
        # Atul set the figures' own flags on 2026-09-25 (CC BY 4.0, no separate credit).
        assert (licence, prod, public, annotated, decision) == (
            "CC BY 4.0",
            True,
            True,
            True,
            "pending",
        )
    # One file per published figure: Figure 2 holds panels A (M02) and B (M03).
    assert [r[5] for r in rows] == [
        "PMC12949993/F1.jpg",
        "PMC12949993/F2.jpg",
        "PMC12949993/F2.jpg",
        "PMC12949993/F3.jpg",
    ]


def test_ground_truth_and_gaps_import(pilot: psycopg.Connection) -> None:
    assert (
        _count(pilot, "select count(*) from casevault.ground_truth where case_version_id = %s") == 1
    )
    assert _count(pilot, "select count(*) from casevault.gap where case_version_id = %s") == 20


@pytest.mark.parametrize(
    ("item", "facts"),
    [
        ("HX.MEDS.CURRENT", ["H03", "H04"]),
        ("HX.EXPOSURE.TOXINS", ["H09"]),
        ("HX.MEDS.SUPPLEMENTS", ["H10"]),
        ("HX.MEDS.SUPPLEMENT_DETAILS", ["H10"]),
    ],
)
def test_history_questions_release_exactly_their_facts(
    pilot: psycopg.Connection, item: str, facts: list[str]
) -> None:
    rows = pilot.execute(
        "select id from casevault.fact where case_version_id = %s and %s = any (released_by)"
        " order by id",
        (CV, item),
    ).fetchall()
    assert [r[0] for r in rows] == facts


def test_the_pilot_has_no_leaks_after_import(pilot: psycopg.Connection) -> None:
    assert pilot.execute("select * from casevault.leak_scan(%s)", (CV,)).fetchall() == []
