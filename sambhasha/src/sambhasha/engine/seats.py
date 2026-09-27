"""Seats: `act(view) -> Action`, played by a model or a person (SPEC §10.3; invariant I3).

Both kinds of seat get the same view, turned into text by the one `render_view`, with the
role card as the first message. A seat may only reply with the actions its role is allowed in
`configs/permissions.yaml`; anything else is invalid and asked for again.
"""

import json
from collections.abc import Callable, Mapping
from functools import cache
from typing import Annotated, Any, Final, Protocol

import jinja2
from pydantic import BaseModel, Field, TypeAdapter, ValidationError, create_model

from sambhasha.domain.actions import (
    AskHistory,
    BedsideTest,
    Challenge,
    Commit,
    ConsultNote,
    Examine,
    OrderTest,
    Refer,
    Report,
    UpdateDifferential,
    Wait,
)
from sambhasha.domain.base import DomainModel
from sambhasha.domain.views import SeatView, ServiceView
from sambhasha.engine.clock import MINUTES_PER_DAY
from sambhasha.gatekeeper.policy import load_permissions, seat_class
from sambhasha.llm.gateway import LLMGateway
from sambhasha.llm.types import ChatMessage
from sambhasha.prompts import Prompt, load_prompt

View = SeatView | ServiceView
ROLES: Final = ("attending", "challenger", "consultant", "service")
ACTION_CLASSES: Final[Mapping[str, type[DomainModel]]] = {
    "ask_history": AskHistory,
    "examine": Examine,
    "bedside_test": BedsideTest,
    "order_test": OrderTest,
    "refer": Refer,
    "consult_note": ConsultNote,
    "report": Report,
    "update_differential": UpdateDifferential,
    "challenge": Challenge,
    "commit": Commit,
    "wait": Wait,
}
HUMAN_ATTEMPTS: Final = 3


def _allowed_actions() -> Mapping[str, tuple[str, ...]]:
    matrix = load_permissions().actions
    return {
        role: tuple(sorted(action for action, roles in matrix.items() if role in roles))
        for role in ROLES
    }


ALLOWED_ACTIONS: Final = _allowed_actions()


class SeatInputError(RuntimeError):
    """A person gave no valid action after several tries."""


class Seat(Protocol):
    seat_id: str

    def act(self, view: View) -> DomainModel: ...


def role_of(seat: str) -> str:
    return seat_class(seat)


@cache
def _action_type(role: str) -> Any:
    classes = tuple(ACTION_CLASSES[name] for name in ALLOWED_ACTIONS[role])
    if len(classes) == 1:
        return classes[0]
    union = classes[0]
    for cls in classes[1:]:
        union = union | cls  # type: ignore[assignment]
    return Annotated[union, Field(discriminator="action")]


@cache
def _turn_model(role: str) -> type[BaseModel]:
    """The reply a model gives: {"turn": <one allowed action>}."""
    model: type[BaseModel] = create_model(
        f"{role.capitalize()}Turn", turn=(_action_type(role), ...)
    )
    return model


@cache
def action_type_for(role: str) -> TypeAdapter[Any]:
    """Validates one action for the role, strictly against that action's own shape."""
    return TypeAdapter(_action_type(role))


# One worked example per action, shown at the end of every view (to people and models alike).
EXAMPLES: Final[Mapping[str, dict[str, Any]]] = {
    "ask_history": {"action": "ask_history", "question": "Do you take any regular medicines?"},
    "examine": {"action": "examine", "system": "abdomen", "manoeuvre": None},
    "bedside_test": {"action": "bedside_test", "test": "urine dipstick"},
    "order_test": {
        "action": "order_test",
        "item": "full blood count",
        "indication": "anaemia under investigation",
        "urgency": "routine",
    },
    "refer": {"action": "refer", "specialty": "haematology", "question": "Cause of the anaemia?"},
    "consult_note": {
        "action": "consult_note",
        "findings": "What you found.",
        "impression": "Your impression.",
        "recommendations": ["A test or treatment to consider"],
    },
    "report": {
        "action": "report",
        "order_id": "O1",
        "report_text": "What the material shows.",
        "impression": "Your conclusion.",
        "suggested_reflex_tests": [],
    },
    "update_differential": {
        "action": "update_differential",
        "items": [
            {
                "diagnosis": "A diagnosis",
                "probability": 0.6,
                "evidence_for": ["E3"],
                "evidence_against": [],
            }
        ],
    },
    "challenge": {
        "action": "challenge",
        "critique": "What does not fit.",
        "alternatives": ["Another diagnosis"],
    },
    "commit": {
        "action": "commit",
        "final_diagnosis": "Your final diagnosis",
        "differential": [],
        "treatment_plan": "Your plan.",
        "evidence": ["E3"],
    },
    "wait": {"action": "wait", "reason": "Results pending"},
}


def _examples(role: str, order_id: str | None = None) -> str:
    lines = []
    for name in ALLOWED_ACTIONS[role]:
        example = dict(EXAMPLES[name])
        if order_id and "order_id" in example:
            example["order_id"] = order_id
        lines.append(json.dumps(example))
    return "Reply with exactly one action as JSON, in one of these forms:\n" + "\n".join(lines)


@cache
def flat_turn_schema(role: str) -> dict[str, Any]:
    """The schema the model is asked to follow: one flat object, {"turn": {...}}.

    Structured-output engines handle a flat object far better than a union of alternatives
    (a live Gemini run mixed the fields of two actions). Every field any allowed action uses
    is listed; `action` names which. The reply is then checked strictly, action by action.
    """
    properties: dict[str, Any] = {}
    definitions: dict[str, Any] = {}
    for name in ALLOWED_ACTIONS[role]:
        schema = ACTION_CLASSES[name].model_json_schema()
        definitions.update(schema.get("$defs", {}))
        for field_name, field_schema in schema["properties"].items():
            if field_name != "action":
                properties.setdefault(field_name, field_schema)
    turn = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": list(ALLOWED_ACTIONS[role])},
            **properties,
        },
        "required": ["action"],
    }
    flat: dict[str, Any] = {"type": "object", "properties": {"turn": turn}, "required": ["turn"]}
    if definitions:
        flat["$defs"] = definitions
    return flat


def load_role_card(seat: str) -> Prompt:
    """The seat's role card from prompts/, rendered for its specialty or department."""
    role = role_of(seat)
    name = f"service_{seat.split('.', 1)[1]}" if role == "service" else role
    prompt = load_prompt(name)
    specialty = seat.split(".", 1)[1].replace("_", " ") if "." in seat else ""
    environment = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=False)  # noqa: S701 (plain text, not HTML)
    text = environment.from_string(prompt.text).render(specialty=specialty)
    return Prompt(name=prompt.name, version=prompt.version, text=text)


def _day_and_time(minutes: int) -> tuple[int, str]:
    day, rest = divmod(minutes, MINUTES_PER_DAY)
    return day, f"{rest // 60:02d}:{rest % 60:02d}"


def render_view(view: View) -> str:
    """The view as text: what a model reads and what a person is shown."""
    if isinstance(view, ServiceView):
        parts = [
            f"Order {view.order_id}: {view.test}",
            f"Clinical details: {view.clinical_details}",
            f"Material:\n{view.raw_material}",
        ]
        if view.media:
            parts.append("Images: " + ", ".join(view.media))
        parts.append(_examples(role_of(view.seat_id), order_id=view.order_id))
        return "\n\n".join(parts)
    limits = view.limits
    day, time = _day_and_time(limits.sim_minutes)
    header = (
        f"Time: Day {day}, {time}\n"
        f"Turns left: {limits.turns_left}. Referrals left: {limits.referrals_left}. "
        f"Budget left: INR {limits.budget_left_inr}."
    )
    chart = "\n".join(
        f"[{e.event_id} · day {d} {t} · {e.seat} · {e.type}] {e.text}"
        for e in view.chart
        for d, t in (_day_and_time(e.sim_minutes),)
    )
    own = ", ".join(e.event_id for e in view.own_notes)
    return "\n\n".join(
        [
            header,
            "Chart:\n" + (chart or "Nothing on the Chart yet."),
            f"Your own entries: {own or 'none yet'}",
            _examples(role_of(view.seat_id)),
        ]
    )


class LLMSeat:
    def __init__(self, seat_id: str, gateway: LLMGateway) -> None:
        self.seat_id = seat_id
        self._role = role_of(seat_id)
        self._gateway = gateway
        self._version = load_role_card(seat_id).version

    def act(self, view: View) -> DomainModel:
        messages = (
            ChatMessage(role="system", content=view.role_card),
            ChatMessage(role="user", content=render_view(view)),
        )
        result = self._gateway.structured(
            self._role,
            messages,
            _turn_model(self._role),
            prompt_version=self._version,
            response_schema=flat_turn_schema(self._role),
        )
        action: DomainModel = result.value.turn  # type: ignore[attr-defined]
        return action


class HumanSeat:
    """A person at the terminal, shown the same text a model would read."""

    def __init__(
        self,
        seat_id: str,
        *,
        read: Callable[[], str] = input,
        write: Callable[[str], None] = print,
    ) -> None:
        self.seat_id = seat_id
        self._role = role_of(seat_id)
        self._read = read
        self._write = write

    def act(self, view: View) -> DomainModel:
        self._write(view.role_card)
        self._write(render_view(view))
        for _attempt in range(HUMAN_ATTEMPTS):
            raw = self._read()
            try:
                action: DomainModel = action_type_for(self._role).validate_json(raw)
            except ValidationError as error:
                allowed = ", ".join(ALLOWED_ACTIONS[self._role])
                self._write(f"That is not a valid action ({allowed}): {error.errors()[0]['msg']}")
                continue
            return action
        raise SeatInputError(f"{self.seat_id}: no valid action after {HUMAN_ATTEMPTS} tries")
