"""Orders and their costs (SPEC §10.4; D-013). Prices come from the generated tables."""

from collections.abc import Iterable
from decimal import Decimal
from uuid import UUID, uuid4

from sambhasha.domain.orders import Order, Route
from sambhasha.engine.clock import SimClock
from sambhasha.engine.tables import Tables


def place_order(
    tables: Tables,
    *,
    run_id: UUID,
    item_id: str | None,
    item_text: str,
    indication: str,
    route: Route,
    clock: SimClock,
) -> Order:
    """A new order, priced and due after the item's turnaround (the estimate if unmatched)."""
    return Order(
        id=uuid4(),
        run_id=run_id,
        ordered_by="attending",
        item_text=item_text,
        code=item_id,
        indication=indication,
        route=route,
        status="placed",
        cost_inr=Decimal(tables.price(item_id).inr),
        ordered_at_min=clock.minutes,
        due_at_min=clock.minutes + tables.turnaround(item_id),
    )


def total_cost(orders: Iterable[Order]) -> Decimal:
    return sum((o.cost_inr for o in orders if o.status != "cancelled"), Decimal(0))


def budget_left(budget: Decimal, orders: Iterable[Order]) -> Decimal:
    return max(budget - total_cost(orders), Decimal(0))
