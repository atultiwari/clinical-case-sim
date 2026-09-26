"""P0.2: seat actions (SPEC §6)."""

import json

import pytest
from pydantic import ValidationError

from sambhasha.domain.actions import (
    AskHistory,
    BedsideTest,
    Challenge,
    Commit,
    ConsultNote,
    DifferentialItem,
    Examine,
    OrderTest,
    Refer,
    Report,
    UpdateDifferential,
    action_json_schema,
    parse_action,
)

EXAMPLES = [
    ({"action": "ask_history", "question": "Any herbal remedies?"}, AskHistory),
    ({"action": "examine", "system": "mouth", "manoeuvre": "gum margins"}, Examine),
    ({"action": "bedside_test", "test": "urine dipstick"}, BedsideTest),
    ({"action": "order_test", "item": "blood lead", "indication": "anaemia"}, OrderTest),
    ({"action": "refer", "specialty": "haematology", "question": "Why anaemic?"}, Refer),
    (
        {
            "action": "consult_note",
            "findings": "Pale",
            "impression": "Anaemia",
            "recommendations": [],
        },
        ConsultNote,
    ),
    (
        {"action": "report", "order_id": "O1", "report_text": "Stippling", "impression": "Toxic"},
        Report,
    ),
    (
        {
            "action": "update_differential",
            "items": [
                {
                    "diagnosis": "Anaemia",
                    "probability": 0.5,
                    "evidence_for": ["E3"],
                    "evidence_against": [],
                }
            ],
        },
        UpdateDifferential,
    ),
    ({"action": "challenge", "critique": "Anchoring", "alternatives": ["Toxin"]}, Challenge),
    (
        {
            "action": "commit",
            "final_diagnosis": "Anaemia",
            "differential": [],
            "treatment_plan": "Transfuse",
            "evidence": ["E3"],
        },
        Commit,
    ),
]


@pytest.mark.parametrize(("raw", "kind"), EXAMPLES, ids=lambda x: getattr(x, "__name__", ""))
def test_each_action_parses_from_json(raw: dict[str, object], kind: type) -> None:
    action = parse_action(json.dumps(raw))

    assert isinstance(action, kind)


def test_order_urgency_defaults_to_routine() -> None:
    action = parse_action('{"action": "order_test", "item": "CBC", "indication": "tired"}')

    assert isinstance(action, OrderTest)
    assert action.urgency == "routine"


def test_an_unknown_action_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_action('{"action": "read_article"}')


def test_extra_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_action('{"action": "ask_history", "question": "Pain?", "peek": "diagnosis"}')


def test_blank_text_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_action('{"action": "ask_history", "question": "   "}')


@pytest.mark.parametrize("probability", [-0.1, 1.1])
def test_a_probability_outside_0_to_1_is_rejected(probability: float) -> None:
    with pytest.raises(ValidationError):
        DifferentialItem(
            diagnosis="X", probability=probability, evidence_for=(), evidence_against=()
        )


def test_an_empty_differential_update_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UpdateDifferential(items=())


def test_actions_are_immutable() -> None:
    action = AskHistory(question="Pain?")

    with pytest.raises(ValidationError):
        action.question = "Fever?"  # type: ignore[misc]


def test_the_action_json_schema_is_available_for_structured_output() -> None:
    schema = action_json_schema()

    assert "oneOf" in schema or "anyOf" in schema
    assert "commit" in json.dumps(schema)
