"""Conditions leave the Case Vault in the bundle schema's shape (SPEC §10.4; PLAN L1.7).

Seven frozen cases hold `finding_released` as an object, {findings, from_tests}. The export
rewrites it as the schema's list of finding ids, with `from_tests` beside it.
"""

import json
from pathlib import Path
from typing import Any

import jsonschema
import psycopg
import pytest
from psycopg.types.json import Jsonb

from scripts.export_bundle import export_bundle
from tests.integration.test_export import _prepare

pytestmark = pytest.mark.integration

SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "case-bundle.v0.3.schema.json"
OBJECT_FORM = {"finding_released": {"findings": ["FND.STIPPLING"], "from_tests": ["LAB.FILM"]}}
SCHEMA_FORM = {"finding_released": ["FND.STIPPLING"], "from_tests": ["LAB.FILM"]}


def _rewrite(db: psycopg.Connection, condition: Any) -> Any:
    row = db.execute("select casevault.bundle_condition(%s)", (Jsonb(condition),)).fetchone()
    assert row is not None
    return row[0]


def test_the_object_form_becomes_a_list_with_from_tests_beside_it(
    db: psycopg.Connection,
) -> None:
    assert _rewrite(db, OBJECT_FORM) == SCHEMA_FORM


def test_the_object_form_without_tests_becomes_a_plain_list(db: psycopg.Connection) -> None:
    condition = {"finding_released": {"findings": ["FND.A", "FND.B"]}}

    assert _rewrite(db, condition) == {"finding_released": ["FND.A", "FND.B"]}


def test_nested_conditions_are_rewritten(db: psycopg.Connection) -> None:
    condition = {
        "all": [
            {"dx_in": ["DX.A"]},
            {"any": [OBJECT_FORM, {"not": OBJECT_FORM}]},
        ]
    }

    assert _rewrite(db, condition) == {
        "all": [{"dx_in": ["DX.A"]}, {"any": [SCHEMA_FORM, {"not": SCHEMA_FORM}]}]
    }


@pytest.mark.parametrize(
    "condition",
    [SCHEMA_FORM, {"released_any": ["L26"]}, {"plan_before": ["RX.A", "LAB.B"]}, None],
)
def test_conditions_already_in_shape_are_unchanged(db: psycopg.Connection, condition: Any) -> None:
    assert _rewrite(db, condition) == condition


def _object_forms(db: psycopg.Connection, cv: str) -> None:
    db.execute(
        "update casevault.ground_truth set"
        " rubric = %(rubric)s, must_do = %(must_do)s where case_version_id = %(cv)s",
        {
            "cv": cv,
            "rubric": Jsonb(
                {
                    "default_score": 1,
                    "rubric": [
                        {
                            "score": 5,
                            "text": "Lead",
                            "if": {"all": [{"dx_in": ["DX.A"]}, OBJECT_FORM]},
                        }
                    ],
                }
            ),
            "must_do": Jsonb(
                [
                    {"text": "Measure blood lead", "if": {"ordered_any": ["LAB.BLOOD_LEAD"]}},
                    {"text": "Review the film", "if": OBJECT_FORM},
                ]
            ),
        },
    )
    db.execute(
        "update casevault.consult_note set condition = %s where case_version_id = %s",
        (Jsonb(OBJECT_FORM), cv),
    )


def test_an_exported_bundle_meets_the_whole_schema(db: psycopg.Connection, tmp_path: Path) -> None:
    cv = _prepare(db, before_freeze=_object_forms)

    bundle = json.loads(export_bundle(db, cv, 1, 0, tmp_path).path.read_bytes())

    jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(bundle)
    assert bundle["ground_truth"]["must_do"][1]["if"] == SCHEMA_FORM
    assert bundle["ground_truth"]["rubric"]["rubric"][0]["if"]["all"][1] == SCHEMA_FORM
    assert bundle["consult_notes"][0]["condition"] == SCHEMA_FORM


def test_the_frozen_rows_and_their_hash_input_are_unchanged(db: psycopg.Connection) -> None:
    cv = _prepare(db, before_freeze=_object_forms)

    stored = db.execute(
        "select condition from casevault.consult_note where case_version_id = %s", (cv,)
    ).fetchone()
    rows = db.execute("select casevault.bundle_rows(%s)", (cv,)).fetchone()

    assert stored is not None
    assert stored[0] == OBJECT_FORM
    # frozen_hash is the SHA-256 of bundle_rows(id)::text, so bundle_rows must not rewrite.
    assert rows is not None
    assert rows[0]["consult_notes"][0]["condition"] == OBJECT_FORM
    assert rows[0]["ground_truth"]["must_do"][1]["if"] == OBJECT_FORM


def test_an_empty_ground_truth_gains_no_keys(db: psycopg.Connection) -> None:
    row = db.execute("select casevault.bundle_ground_truth('{}'::jsonb)").fetchone()

    assert row is not None
    assert row[0] == {}
