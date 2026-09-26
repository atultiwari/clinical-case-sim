"""Event Log rows (SPEC §12). The log is append-only (invariant I6).

An event's `source` says where released text came from. It is stored for audit and never
shown to a seat: the Chart view (views.py) has no source field.
"""

from decimal import Decimal
from typing import Annotated, Final, Literal, Self
from uuid import UUID

from pydantic import Discriminator, Field, NonNegativeInt, Tag, model_validator

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
from sambhasha.domain.base import DomainModel, NonEmptyStr
from sambhasha.domain.seats import SeatId

EventType = Literal[
    "request",
    "answer",
    "refusal",
    "order",
    "result",
    "report",
    "consult_note",
    "differential",
    "challenge",
    "commit",
    "llm_call",
]
Source = Literal["article", "synthetic", "seat", "engine"]
Audience = Literal["team"] | SeatId


class Answer(DomainModel):
    """Stored text the Gatekeeper released (invariant I4), and what it came from."""

    record: Literal["answer"] = "answer"
    text: NonEmptyStr
    fact_ids: tuple[str, ...] = ()
    ledger_ids: tuple[str, ...] = ()


class Refusal(DomainModel):
    record: Literal["refusal"] = "refusal"
    reason: NonEmptyStr


class Result(DomainModel):
    """A direct result posted to the Chart for an order."""

    record: Literal["result"] = "result"
    order_id: NonEmptyStr
    text: NonEmptyStr
    fact_ids: tuple[str, ...] = ()
    ledger_ids: tuple[str, ...] = ()


class LlmCall(DomainModel):
    record: Literal["llm_call"] = "llm_call"
    role: NonEmptyStr
    request_hash: NonEmptyStr
    cached: bool = False


def _payload_tag(value: object) -> str | None:
    if isinstance(value, dict):
        tag = value.get("action") or value.get("record")
    else:
        tag = getattr(value, "action", None) or getattr(value, "record", None)
    return tag if isinstance(tag, str) else None


Payload = Annotated[
    Annotated[AskHistory, Tag("ask_history")]
    | Annotated[Examine, Tag("examine")]
    | Annotated[BedsideTest, Tag("bedside_test")]
    | Annotated[OrderTest, Tag("order_test")]
    | Annotated[Refer, Tag("refer")]
    | Annotated[ConsultNote, Tag("consult_note")]
    | Annotated[Report, Tag("report")]
    | Annotated[UpdateDifferential, Tag("update_differential")]
    | Annotated[Challenge, Tag("challenge")]
    | Annotated[Commit, Tag("commit")]
    | Annotated[Answer, Tag("answer")]
    | Annotated[Refusal, Tag("refusal")]
    | Annotated[Result, Tag("result")]
    | Annotated[LlmCall, Tag("llm_call")],
    Discriminator(_payload_tag),
]

PAYLOADS_BY_TYPE: Final[dict[str, tuple[type[DomainModel], ...]]] = {
    "request": (AskHistory, Examine, BedsideTest, Refer),
    "order": (OrderTest,),
    "answer": (Answer,),
    "refusal": (Refusal,),
    "result": (Result,),
    "report": (Report,),
    "consult_note": (ConsultNote,),
    "differential": (UpdateDifferential,),
    "challenge": (Challenge,),
    "commit": (Commit,),
    "llm_call": (LlmCall,),
}


class Event(DomainModel):
    run_id: UUID
    seq: NonNegativeInt
    sim_minutes: NonNegativeInt
    seat: SeatId
    type: EventType
    payload: Payload
    visibility: tuple[Audience, ...]
    source: Source
    model: str | None = None
    prompt_version: str | None = None
    tokens_in: NonNegativeInt | None = None
    tokens_out: NonNegativeInt | None = None
    cost_usd: Annotated[Decimal, Field(ge=0)] | None = None
    hash: str | None = None

    @property
    def event_id(self) -> str:
        """The id seats cite, for example in `Commit.evidence`."""
        return f"E{self.seq}"

    @model_validator(mode="after")
    def _payload_matches_type(self) -> Self:
        allowed = PAYLOADS_BY_TYPE[self.type]
        if not isinstance(self.payload, allowed):
            names = ", ".join(kind.__name__ for kind in allowed)
            raise ValueError(
                f"a {self.type} event needs a {names} payload, not {type(self.payload).__name__}"
            )
        return self
