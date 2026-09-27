"""P1.5: the simulated clock and costs (SPEC §10.4)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from sambhasha.catalogue import Catalogue
from sambhasha.domain.orders import Order
from sambhasha.engine.clock import MINUTES_PER_DAY, SimClock
from sambhasha.engine.costs import budget_left, place_order, total_cost
from sambhasha.engine.tables import generate_tables

TABLES = generate_tables(Catalogue.load())
RUN = uuid4()


def test_the_clock_starts_at_day_0_and_advances_immutably() -> None:
    clock = SimClock()
    later = clock.advance(MINUTES_PER_DAY + 30)

    assert (clock.minutes, clock.day) == (0, 0)
    assert (later.minutes, later.day) == (1470, 1)


def test_the_clock_never_runs_backwards() -> None:
    with pytest.raises(ValueError, match="backwards"):
        SimClock().advance(-1)


def test_an_order_is_due_after_its_turnaround_and_costs_its_price() -> None:
    order = place_order(
        TABLES,
        run_id=RUN,
        item_id="LAB.HAEM.CBC",
        item_text="CBC",
        indication="anaemia",
        route="direct",
        clock=SimClock(minutes=60),
    )

    assert (order.ordered_at_min, order.due_at_min) == (60, 300)
    assert order.cost_inr == Decimal(300)
    assert order.status == "placed"


def test_an_order_outside_the_catalogue_is_priced_by_the_estimate() -> None:
    order = place_order(
        TABLES,
        run_id=RUN,
        item_id=None,
        item_text="serum thallium",
        indication="x",
        route="direct",
        clock=SimClock(),
    )

    assert order.code is None
    assert order.cost_inr == Decimal(TABLES.unmatched_price)
    assert order.due_at_min == TABLES.unmatched_turnaround


def test_costs_add_up_per_order() -> None:
    orders = [
        place_order(
            TABLES,
            run_id=RUN,
            item_id=i,
            item_text=i,
            indication="x",
            route="direct",
            clock=SimClock(),
        )
        for i in ("LAB.HAEM.CBC", "LAB.TOX.BLOOD_LEAD", "LAB.HAEM.CBC")
    ]
    expected = sum((TABLES.price(i).inr for i in ("LAB.HAEM.CBC", "LAB.TOX.BLOOD_LEAD")), 0) + 300

    assert total_cost(orders) == Decimal(expected)
    assert budget_left(Decimal(5000), orders) == Decimal(5000) - Decimal(expected)


def test_a_cancelled_order_costs_nothing() -> None:
    order = place_order(
        TABLES,
        run_id=RUN,
        item_id="LAB.HAEM.CBC",
        item_text="CBC",
        indication="x",
        route="direct",
        clock=SimClock(),
    )
    cancelled = order.model_copy(update={"status": "cancelled"})

    assert total_cost([order, cancelled]) == Decimal(300)


def test_the_budget_never_shows_below_zero() -> None:
    order = place_order(
        TABLES,
        run_id=RUN,
        item_id="LAB.HAEM.CBC",
        item_text="CBC",
        indication="x",
        route="direct",
        clock=SimClock(),
    )

    assert budget_left(Decimal(100), [order]) == Decimal(0)


def test_orders_are_frozen() -> None:
    assert isinstance(
        place_order(
            TABLES,
            run_id=RUN,
            item_id="LAB.HAEM.CBC",
            item_text="CBC",
            indication="x",
            route="direct",
            clock=SimClock(),
        ),
        Order,
    )
