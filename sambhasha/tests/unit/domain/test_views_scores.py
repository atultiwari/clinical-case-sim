"""P0.2: seat views (SPEC §5.5) and scores (SPEC §12, §13)."""

import typing
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError

from sambhasha.domain.case_file import GroundTruth
from sambhasha.domain.scores import Score
from sambhasha.domain.views import ChartEntry, Limits, SeatView, ServiceView


def _nested_models(model: type[BaseModel]) -> set[type[BaseModel]]:
    """Every model reachable from a model's field annotations, the model included."""
    found: set[type[BaseModel]] = set()
    pending = [model]
    while pending:
        current = pending.pop()
        if current in found:
            continue
        found.add(current)
        for field in current.model_fields.values():
            stack: list[Any] = [field.annotation]
            while stack:
                annotation = stack.pop()
                if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                    pending.append(annotation)
                stack.extend(typing.get_args(annotation))
    return found


@pytest.mark.parametrize("view", [SeatView, ServiceView])
def test_no_view_can_hold_the_ground_truth(view: type[BaseModel]) -> None:
    assert GroundTruth not in _nested_models(view)


@pytest.mark.parametrize("view", [SeatView, ServiceView])
def test_no_view_carries_an_event_source(view: type[BaseModel]) -> None:
    for model in _nested_models(view):
        assert "source" not in model.model_fields, model.__name__


def _limits() -> Limits:
    return Limits(turns_left=30, referrals_left=4, budget_left_inr=Decimal(5000), sim_minutes=0)


def test_a_seat_view_is_immutable() -> None:
    entry = ChartEntry(event_id="E1", sim_minutes=0, seat="gatekeeper", type="answer", text="Hi")
    view = SeatView(
        seat_id="attending", role_card="You lead.", chart=(entry,), own_notes=(), limits=_limits()
    )

    with pytest.raises(ValidationError):
        view.chart = ()  # type: ignore[misc]
    assert isinstance(view.chart, tuple)


def test_a_service_view_belongs_to_a_service() -> None:
    with pytest.raises(ValidationError, match="service"):
        ServiceView(
            seat_id="attending",
            role_card="You report.",
            order_id="O1",
            test="Blood film",
            clinical_details="Anaemia",
            raw_material="Stippled red cells.",
        )


def test_limits_cannot_go_negative() -> None:
    with pytest.raises(ValidationError):
        Limits(turns_left=-1, referrals_left=0, budget_left_inr=Decimal(0), sim_minutes=0)


# --- scores ---


def _score(**overrides: Any) -> Score:
    fields: dict[str, Any] = {
        "id": uuid4(),
        "run_id": uuid4(),
        "rater": "evaluator",
        "rater_type": "llm",
        "dx_score": 5,
        "dx_rank": 1,
    }
    return Score.model_validate({**fields, **overrides})


@pytest.mark.parametrize(("dx_score", "correct"), [(5, True), (4, True), (3, False), (1, False)])
def test_a_diagnosis_score_of_4_or_more_is_correct(dx_score: int, correct: bool) -> None:
    assert _score(dx_score=dx_score).dx_correct is correct


@pytest.mark.parametrize("dx_score", [0, 6])
def test_the_diagnosis_score_runs_from_1_to_5(dx_score: int) -> None:
    with pytest.raises(ValidationError):
        _score(dx_score=dx_score)


@pytest.mark.parametrize(
    ("rank", "top1", "top3"),
    [(1, True, True), (3, False, True), (4, False, False), (None, False, False)],
)
def test_top_1_and_top_3(rank: int | None, top1: bool, top3: bool) -> None:
    score = _score(dx_rank=rank)

    assert (score.top1, score.top3) == (top1, top3)


@pytest.mark.parametrize("dependence", [-0.1, 1.5])
def test_synthetic_dependence_is_a_share(dependence: float) -> None:
    with pytest.raises(ValidationError):
        _score(synthetic_dependence=dependence)


def test_the_fallback_flag_defaults_to_false() -> None:
    assert _score().used_fallback is False


def test_an_unknown_plan_rating_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _score(plan_rating="fine")
