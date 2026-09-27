"""Seats: `act(view) -> Action`, played by a model or a person (SPEC §10.3; invariant I3).

Both kinds of seat get the same view, turned into text by the one `render_view`, with the
role card as the first message. A seat may only reply with the actions its role is allowed in
`configs/permissions.yaml`; anything else is invalid and asked for again.
"""

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
def _action_adapter(role: str) -> TypeAdapter[Any]:
    return TypeAdapter(_action_type(role))


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
        parts.append('Reply with one action as JSON, for example {"action": "report", ...}.')
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
            'Reply with one action as JSON, for example {"action": "ask_history", ...}.',
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
            self._role, messages, _turn_model(self._role), prompt_version=self._version
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
                action: DomainModel = _action_adapter(self._role).validate_json(raw)
            except ValidationError as error:
                allowed = ", ".join(ALLOWED_ACTIONS[self._role])
                self._write(f"That is not a valid action ({allowed}): {error.errors()[0]['msg']}")
                continue
            return action
        raise SeatInputError(f"{self.seat_id}: no valid action after {HUMAN_ATTEMPTS} tries")
