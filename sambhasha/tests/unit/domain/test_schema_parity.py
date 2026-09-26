"""P0.2: the bundle models cover the Case Library's JSON schema, field for field.

The schema is the shared contract. If the Case Library adds a field in a new schema
version, this test fails until the models follow.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from sambhasha.domain import case_file, conditions

SCHEMA = (
    Path(__file__).resolve().parents[4]
    / "case-library"
    / "schemas"
    / "case-bundle.v0.3.schema.json"
)

# JSON schema definition -> the model that implements it.
MODELS: dict[str, type[BaseModel]] = {
    "fact": case_file.Fact,
    "ledger_row": case_file.LedgerRow,
    "report": case_file.Report,
    "consult_note": case_file.ConsultNoteTemplate,
    "raw_material": case_file.RawMaterial,
    "media": case_file.Media,
    "gap": case_file.Gap,
    "ground_truth": case_file.GroundTruth,
    "condition": conditions.Condition,
    "test_utility": case_file.TestUtility,
    "path": case_file.PathAnalysis,
}


def _schema() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(SCHEMA.read_text())
    return data


def _json_names(model: type[BaseModel]) -> set[str]:
    return {field.alias or name for name, field in model.model_fields.items()}


@pytest.mark.parametrize("definition", sorted(MODELS))
def test_each_definition_matches_its_model(definition: str) -> None:
    schema_fields = set(_schema()["$defs"][definition]["properties"])

    assert _json_names(MODELS[definition]) == schema_fields


def test_the_top_level_matches_the_bundle_model() -> None:
    assert _json_names(case_file.CaseBundle) == set(_schema()["properties"])


def test_required_top_level_fields_are_required() -> None:
    required = set(_schema()["required"])
    model_required = {
        field.alias or name
        for name, field in case_file.CaseBundle.model_fields.items()
        if field.is_required()
    }

    assert model_required == required


@pytest.mark.parametrize("definition", sorted(MODELS))
def test_required_fields_match(definition: str) -> None:
    required = set(_schema()["$defs"][definition].get("required", []))
    model = MODELS[definition]
    model_required = {
        field.alias or name for name, field in model.model_fields.items() if field.is_required()
    }

    assert model_required == required
