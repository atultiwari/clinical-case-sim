"""What a seat sees (SPEC §5.5). Human and model seats get identical views (invariant I3).

Views are built only from released events. They have no field that could hold the ground
truth (invariant I8) or an event's source.
"""

from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field, NonNegativeInt

from sambhasha.domain.base import DomainModel, NonEmptyStr
from sambhasha.domain.events import EventType
from sambhasha.domain.seats import SeatId, is_service


def _service_seat(seat: str) -> str:
    if not is_service(seat):
        raise ValueError(f"a service view belongs to a service.<department> seat, not {seat!r}")
    return seat


class ChartEntry(DomainModel):
    event_id: NonEmptyStr
    sim_minutes: NonNegativeInt
    seat: SeatId
    type: EventType
    text: NonEmptyStr


class Limits(DomainModel):
    turns_left: NonNegativeInt
    referrals_left: NonNegativeInt
    budget_left_inr: Annotated[Decimal, Field(ge=0)]
    sim_minutes: NonNegativeInt  # the simulated clock now


class SeatView(DomainModel):
    """A doctor seat's view: its role card, the Chart it may see, its notes and its limits."""

    seat_id: SeatId
    role_card: NonEmptyStr
    chart: tuple[ChartEntry, ...]
    own_notes: tuple[ChartEntry, ...]
    limits: Limits


class ServiceView(DomainModel):
    """A Diagnostic Service's view: one order, its clinical details and the raw material."""

    seat_id: Annotated[SeatId, AfterValidator(_service_seat)]
    role_card: NonEmptyStr
    order_id: NonEmptyStr
    test: NonEmptyStr
    clinical_details: NonEmptyStr
    raw_material: NonEmptyStr
    media: tuple[str, ...] = ()
