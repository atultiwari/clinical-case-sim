"""What each seat is given each turn (SPEC §5.5). Human and model seats get the same views
(invariant I3); no view can hold the ground truth or an event's source (I8)."""

from collections.abc import Iterable

from sambhasha.domain.events import Event
from sambhasha.domain.views import Limits, SeatView, ServiceView
from sambhasha.engine.chart import chart_entries, referral_needed
from sambhasha.engine.clock import SimClock
from sambhasha.gatekeeper.resolver import ServiceRequest


def build_seat_view(
    seat: str,
    *,
    role_card: str,
    events: Iterable[Event],
    now: SimClock,
    limits: Limits,
    referred: frozenset[str],
) -> SeatView:
    """A doctor seat's view. A Consultant sees nothing of the Chart before its referral."""
    visible = () if referral_needed(seat, referred) else chart_entries(events, viewer=seat, now=now)
    return SeatView(
        seat_id=seat,
        role_card=role_card,
        chart=visible,
        own_notes=tuple(e for e in visible if e.seat == seat),
        limits=limits.model_copy(update={"sim_minutes": now.minutes}),
    )


def build_service_view(
    request: ServiceRequest, *, order_id: str, test_name: str, role_card: str
) -> ServiceView:
    """A Diagnostic Service's view: its one order, the clinical details and the raw material."""
    return ServiceView(
        seat_id=request.service,
        role_card=role_card,
        order_id=order_id,
        test=test_name,
        clinical_details=request.clinical_details or "None given.",
        raw_material=request.findings,
        media=request.media,
    )
