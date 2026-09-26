"""P0.2: scoring conditions (Case Library SPEC §10.4)."""

import pytest
from pydantic import ValidationError

from sambhasha.domain.conditions import Condition, ScoredItem


def test_a_simple_condition_parses() -> None:
    condition = Condition.model_validate({"ordered_any": ["LAB.TOX.BLOOD_LEAD"]})

    assert condition.ordered_any == ("LAB.TOX.BLOOD_LEAD",)


def test_nested_all_any_and_not_parse_under_their_json_names() -> None:
    condition = Condition.model_validate(
        {
            "all": [
                {"any": [{"dx_in": ["DX.A"]}, {"dx_in": ["DX.B"]}]},
                {"not": {"plan_has": ["RX.STEROID.*"]}},
            ]
        }
    )

    assert condition.all_ is not None
    first, second = condition.all_
    assert first.any_ is not None
    assert len(first.any_) == 2
    assert second.not_ is not None
    assert second.not_.plan_has == ("RX.STEROID.*",)


def test_a_condition_round_trips_to_its_json_names() -> None:
    raw = {"not": {"asked_any": ["HX.MEDS.SUPPLEMENTS"]}}

    assert Condition.model_validate(raw).to_json_data() == raw


def test_finding_released_with_from_tests_is_allowed() -> None:
    condition = Condition.model_validate(
        {"finding_released": ["FND.X"], "from_tests": ["LAB.HAEM.FILM"]}
    )

    assert condition.from_tests == ("LAB.HAEM.FILM",)


def test_from_tests_needs_finding_released() -> None:
    with pytest.raises(ValidationError, match="from_tests needs finding_released"):
        Condition.model_validate({"from_tests": ["LAB.HAEM.FILM"]})


def test_an_empty_condition_is_rejected() -> None:
    with pytest.raises(ValidationError, match="one or two"):
        Condition.model_validate({})


def test_three_keys_are_rejected() -> None:
    with pytest.raises(ValidationError, match="one or two"):
        Condition.model_validate({"dx_in": ["DX.A"], "plan_has": ["RX.A"], "asked_any": ["HX.A"]})


def test_an_empty_id_list_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Condition.model_validate({"dx_in": []})


def test_an_unknown_key_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Condition.model_validate({"diagnosis_is": ["DX.A"]})


def test_plan_before_takes_exactly_two_ids() -> None:
    with pytest.raises(ValidationError):
        Condition.model_validate({"plan_before": ["RX.A"]})


def test_a_plain_text_scored_item_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ScoredItem.model_validate("Review the blood film")


def test_a_scored_item_parses_strictly_from_json() -> None:
    item = ScoredItem.model_validate_json(
        '{"text": "Name it", "if": {"dx_in": ["DX.A"]}}', strict=True
    )

    assert item.if_ is not None
    assert item.if_.dx_in == ("DX.A",)


def test_a_scored_item_carries_its_condition() -> None:
    item = ScoredItem.model_validate({"text": "Order a lead level", "if": {"ordered_any": ["X"]}})

    assert item.if_ is not None
    assert item.if_.ordered_any == ("X",)
