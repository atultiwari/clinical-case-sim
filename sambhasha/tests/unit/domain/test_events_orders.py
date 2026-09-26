"""P0.2: events and orders (SPEC §6, §12)."""

from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from sambhasha.domain.actions import AskHistory, OrderTest
from sambhasha.domain.events import Answer, Event, LlmCall, Refusal
from sambhasha.domain.orders import Order
from sambhasha.domain.seats import is_consultant, is_service, validate_seat_id

RUN = uuid4()


def _event(**overrides: Any) -> Event:
    fields: dict[str, Any] = {
        "run_id": RUN,
        "seq": 3,
        "sim_minutes": 10,
        "seat": "gatekeeper",
        "type": "answer",
        "payload": Answer(text="No known toxin exposure.", fact_ids=("H09",)),
        "visibility": ("team",),
        "source": "article",
    }
    return Event.model_validate({**fields, **overrides})


@pytest.mark.parametrize(
    "seat",
    [
        "attending",
        "challenger",
        "consultant.haematology",
        "consultant.clinical_toxicology",
        "service.pathology",
        "service.radiology",
        "service.microbiology",
        "gatekeeper",
        "synthetic",
        "evaluator",
        "scheduler",
    ],
)
def test_the_glossary_seat_ids_are_valid(seat: str) -> None:
    assert validate_seat_id(seat) == seat


@pytest.mark.parametrize(
    "seat", ["Attending", "consultant", "consultant.Haematology", "service.cardiology", "judge"]
)
def test_other_seat_ids_are_rejected(seat: str) -> None:
    with pytest.raises(ValueError, match="seat id"):
        validate_seat_id(seat)


def test_seat_kinds() -> None:
    assert is_consultant("consultant.neurology")
    assert not is_consultant("attending")
    assert is_service("service.pathology")
    assert not is_service("synthetic")


def test_an_event_has_an_id_seats_can_cite() -> None:
    assert _event(seq=12).event_id == "E12"


def test_an_event_accepts_a_matching_payload() -> None:
    event = _event(
        seat="attending",
        type="request",
        payload=AskHistory(question="Any supplements?"),
        source="seat",
    )

    assert isinstance(event.payload, AskHistory)


def test_an_event_payload_must_match_its_type() -> None:
    with pytest.raises(ValidationError, match="payload"):
        _event(type="order", payload=Answer(text="x"))


def test_a_refusal_carries_its_reason() -> None:
    event = _event(type="refusal", payload=Refusal(reason="Ask for a specific item."))

    assert isinstance(event.payload, Refusal)


def test_an_llm_call_records_tokens_and_cost() -> None:
    event = _event(
        seat="attending",
        type="llm_call",
        payload=LlmCall(role="attending", request_hash="abc"),
        visibility=(),
        source="engine",
        model="profile.attending",
        prompt_version="1",
        tokens_in=100,
        tokens_out=20,
        cost_usd=Decimal("0.0012"),
    )

    assert event.cost_usd == Decimal("0.0012")


def test_an_event_round_trips_through_json() -> None:
    event = _event(
        type="order",
        seat="attending",
        source="seat",
        payload=OrderTest(item="blood lead", indication="anaemia"),
    )

    assert Event.model_validate_json(event.model_dump_json()) == event


def test_events_are_immutable() -> None:
    event = _event()

    with pytest.raises(ValidationError):
        event.seq = 4  # type: ignore[misc]


@pytest.mark.parametrize("field", ["seq", "sim_minutes", "tokens_in"])
def test_counts_cannot_be_negative(field: str) -> None:
    with pytest.raises(ValidationError):
        _event(**{field: -1})


def test_an_unknown_source_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _event(source="article_text")


def test_an_unknown_audience_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _event(visibility=("everyone",))


# --- orders ---


def _order(**overrides: Any) -> Order:
    fields: dict[str, Any] = {
        "id": uuid4(),
        "run_id": RUN,
        "ordered_by": "attending",
        "item_text": "blood film",
        "code": "LAB.HAEM.FILM",
        "indication": "anaemia",
        "route": "service.pathology",
        "status": "placed",
        "cost_inr": Decimal("150"),
        "ordered_at_min": 30,
        "due_at_min": 270,
    }
    return Order.model_validate({**fields, **overrides})


def test_an_order_is_valid() -> None:
    assert _order().route == "service.pathology"


def test_a_result_cannot_be_due_before_the_order() -> None:
    with pytest.raises(ValidationError, match="due"):
        _order(due_at_min=10)


def test_an_order_cost_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        _order(cost_inr=Decimal("-1"))


def test_an_unknown_route_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _order(route="service.cardiology")
