"""Seat actions (SPEC §6). Every seat returns exactly one action per turn.

Each action carries an `action` tag, so a model's structured output parses into the right
class. Which seat may take which action lives in `configs/permissions.yaml` (P1.3).
"""

from typing import Annotated, Any, Literal

from pydantic import Field, TypeAdapter

from sambhasha.domain.base import DomainModel, NonEmptyStr

EventRef = NonEmptyStr  # an event id such as "E12", as shown on the Chart


class AskHistory(DomainModel):
    action: Literal["ask_history"] = "ask_history"
    question: NonEmptyStr


class Examine(DomainModel):
    action: Literal["examine"] = "examine"
    system: NonEmptyStr  # e.g. "abdomen", "nervous system"
    manoeuvre: NonEmptyStr | None = None  # e.g. "gingival margin inspection"


class BedsideTest(DomainModel):
    """A Consultant's own-domain bedside test, such as a urine dipstick."""

    action: Literal["bedside_test"] = "bedside_test"
    test: NonEmptyStr


class OrderTest(DomainModel):
    """Attending only. The free text is matched to catalogue ids (D-022)."""

    action: Literal["order_test"] = "order_test"
    item: NonEmptyStr
    indication: NonEmptyStr  # clinical details written on the requisition
    urgency: Literal["routine", "urgent"] = "routine"


class Refer(DomainModel):
    """Attending only."""

    action: Literal["refer"] = "refer"
    specialty: NonEmptyStr  # e.g. "haematology"
    question: NonEmptyStr


class ConsultNote(DomainModel):
    """Ends a Consultant's session."""

    action: Literal["consult_note"] = "consult_note"
    findings: NonEmptyStr
    impression: NonEmptyStr
    recommendations: tuple[NonEmptyStr, ...]  # tests or referrals the Attending may act on


class Report(DomainModel):
    """A Diagnostic Service's report on one of its own orders."""

    action: Literal["report"] = "report"
    order_id: NonEmptyStr
    report_text: NonEmptyStr
    impression: NonEmptyStr
    suggested_reflex_tests: tuple[NonEmptyStr, ...] = ()


class Wait(DomainModel):
    """Attending only. Let simulated time pass until the next pending result arrives."""

    action: Literal["wait"] = "wait"
    reason: NonEmptyStr | None = None


class DifferentialItem(DomainModel):
    diagnosis: NonEmptyStr
    probability: Annotated[float, Field(ge=0, le=1)]
    evidence_for: tuple[EventRef, ...]
    evidence_against: tuple[EventRef, ...]


class UpdateDifferential(DomainModel):
    action: Literal["update_differential"] = "update_differential"
    items: Annotated[tuple[DifferentialItem, ...], Field(min_length=1)]


class Challenge(DomainModel):
    """The Challenger's critique of the leading diagnosis."""

    action: Literal["challenge"] = "challenge"
    critique: NonEmptyStr
    alternatives: tuple[NonEmptyStr, ...]


class Commit(DomainModel):
    """Attending only. Ends the work-up; the Evaluator scores it (P1.8)."""

    action: Literal["commit"] = "commit"
    final_diagnosis: NonEmptyStr
    differential: tuple[DifferentialItem, ...]
    treatment_plan: NonEmptyStr
    evidence: tuple[EventRef, ...]  # events that support the diagnosis


Action = Annotated[
    AskHistory
    | Examine
    | BedsideTest
    | OrderTest
    | Refer
    | ConsultNote
    | Report
    | UpdateDifferential
    | Challenge
    | Commit
    | Wait,
    Field(discriminator="action"),
]

_ACTION: TypeAdapter[Action] = TypeAdapter(Action)


def parse_action(raw: str | bytes) -> Action:
    """Parse a seat's JSON output into its action, or raise pydantic's ValidationError."""
    return _ACTION.validate_json(raw)


def action_json_schema() -> dict[str, Any]:
    """The JSON schema of every action, for a model's structured output (SPEC §11)."""
    return _ACTION.json_schema()
