"""casevault.load_catalogue: loading the built catalogue document (PLAN L0.4)."""

import json
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts import catalogue as cat

pytestmark = pytest.mark.integration

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "catalogue"
REAL = Path(__file__).resolve().parents[2] / "catalogue"


def _doc(version: int = 0) -> dict[str, Any]:
    return cat.build_document(cat.read_catalogue(FIXTURE), version=version)


def _load(db: psycopg.Connection, doc: dict[str, Any]) -> dict[str, int]:
    row = db.execute("select casevault.load_catalogue(%s::jsonb)", (json.dumps(doc),)).fetchone()
    assert row is not None
    return dict(row[0])


def _scalar(db: psycopg.Connection, query: str, params: tuple[Any, ...] = ()) -> Any:
    row = db.execute(query, params).fetchone()
    assert row is not None
    return row[0]


def test_load_writes_every_table(db: psycopg.Connection) -> None:
    counts = _load(db, _doc())
    assert counts == {
        "items": 12,
        "deactivated": 0,
        "tests": 4,
        "components": 6,
        "test_components": 6,
        "normal_templates": 4,
        "diagnoses": 1,
        "value_rules": 1,
    }
    active, since = db.execute(
        "select bool_and(active), max(since_version) from casevault.catalogue_item"
    ).fetchone() or (None, None)
    assert active is True
    assert since == 0
    positions = db.execute(
        "select component_id from casevault.test_component where test_item_id = 'LAB.HAEM.CBC'"
        " order by position"
    ).fetchall()
    assert [p[0] for p in positions] == ["CMP.HB", "CMP.RBC", "CMP.MCH"]
    ranges = _scalar(db, "select ref_ranges from casevault.component where id = 'CMP.HB'")
    assert ranges[0] == {
        "sex": "F",
        "age_min": 18,
        "low": 115,
        "high": 165,
        "source": "Dacie and Lewis Practical Haematology, 12th ed. (2017)",
    }
    assert (
        _scalar(
            db, "select review_status from casevault.normal_template where item_id = 'EX.ORAL.GUMS'"
        )
        == "pending"
    )


def test_the_generator_reads_the_loaded_ranges(db: psycopg.Connection) -> None:
    _load(db, _doc())
    low, high = db.execute(
        'select low, high from casevault.reference_range(\'{"sex": "M", "age_years": 40}\','
        " 'CMP.HB')"
    ).fetchone() or (None, None)
    assert (low, high) == (130, 180)


def test_loading_twice_changes_nothing(db: psycopg.Connection) -> None:
    _load(db, _doc())
    db.execute("update casevault.normal_template set review_status = 'approved'")
    before = db.execute("select * from casevault.catalogue_item order by id").fetchall()
    _load(db, _doc(version=1))
    after = db.execute("select * from casevault.catalogue_item order by id").fetchall()
    assert before == after  # since_version stays at the version an item joined in
    assert (
        _scalar(
            db, "select count(*) from casevault.normal_template where review_status = 'approved'"
        )
        == 4
    )


def test_a_changed_template_goes_back_to_review(db: psycopg.Connection) -> None:
    _load(db, _doc())
    db.execute("update casevault.normal_template set review_status = 'approved'")
    doc = _doc(version=1)
    doc["normal_templates"] = [
        {**t, "template": "Gums healthy."} if t["item_id"] == "EX.ORAL.GUMS" else t
        for t in doc["normal_templates"]
    ]
    _load(db, doc)
    assert (
        _scalar(
            db, "select review_status from casevault.normal_template where item_id = 'EX.ORAL.GUMS'"
        )
        == "pending"
    )


def test_an_item_left_out_is_deactivated_not_deleted(db: psycopg.Connection) -> None:
    _load(db, _doc())
    doc = _doc(version=1)
    doc["items"] = [i for i in doc["items"] if i["id"] != "HX.EXPOSURE.OCCUPATION"]
    doc["normal_templates"] = [
        t for t in doc["normal_templates"] if t["item_id"] != "HX.EXPOSURE.OCCUPATION"
    ]
    counts = _load(db, doc)
    assert counts["deactivated"] == 1
    assert (
        _scalar(
            db, "select active from casevault.catalogue_item where id = 'HX.EXPOSURE.OCCUPATION'"
        )
        is False
    )


def test_a_new_item_records_the_version_it_joined_in(db: psycopg.Connection) -> None:
    _load(db, _doc())
    doc = _doc(version=2)
    doc["items"] = [
        *doc["items"],
        {
            "id": "HX.SOCIAL.SMOKING",
            "kind": "history",
            "name": "Smoking",
            "category": "social",
            "synonyms": ["tobacco", "cigarettes"],
            "specialty_scope": ["attending"],
        },
    ]
    _load(db, doc)
    assert (
        _scalar(
            db, "select since_version from casevault.catalogue_item where id = 'HX.SOCIAL.SMOKING'"
        )
        == 2
    )


def test_a_test_component_list_is_replaced(db: psycopg.Connection) -> None:
    _load(db, _doc())
    doc = _doc(version=1)
    doc["tests"] = [
        {**t, "components": ["CMP.RBC", "CMP.HB"]} if t["item_id"] == "LAB.HAEM.CBC" else t
        for t in doc["tests"]
    ]
    _load(db, doc)
    rows = db.execute(
        "select component_id from casevault.test_component where test_item_id = 'LAB.HAEM.CBC'"
        " order by position"
    ).fetchall()
    assert [r[0] for r in rows] == ["CMP.RBC", "CMP.HB"]


def test_a_document_without_a_version_is_refused(db: psycopg.Connection) -> None:
    doc = _doc()
    del doc["version"]
    with pytest.raises(psycopg.errors.RaiseException, match="version"):
        _load(db, doc)


def test_the_real_catalogue_loads(db: psycopg.Connection) -> None:
    catalogue = cat.read_catalogue(REAL)
    assert cat.check(catalogue) == []
    counts = _load(db, cat.build_document(catalogue, version=0))
    assert counts["items"] == len(catalogue.items())
    assert counts["components"] == len(catalogue.rows("components.csv"))
