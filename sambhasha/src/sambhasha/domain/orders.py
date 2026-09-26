"""Test orders (SPEC §12). Direct results go to the Chart; interpretive ones to a service."""

from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, NonNegativeInt, model_validator

from sambhasha.domain.base import DomainModel, NonEmptyStr
from sambhasha.domain.seats import SeatId

Route = Literal["direct", "service.pathology", "service.radiology", "service.microbiology"]
OrderStatus = Literal["placed", "resulted", "reported", "cancelled"]


class Order(DomainModel):
    id: UUID
    run_id: UUID
    ordered_by: SeatId
    item_text: NonEmptyStr
    code: str | None  # the catalogue id the matcher chose; None if nothing matched
    indication: NonEmptyStr
    route: Route
    status: OrderStatus
    cost_inr: Annotated[Decimal, Field(ge=0)]
    ordered_at_min: NonNegativeInt
    due_at_min: NonNegativeInt

    @model_validator(mode="after")
    def _due_after_ordered(self) -> Self:
        if self.due_at_min < self.ordered_at_min:
            raise ValueError("a result cannot be due before its order was placed")
        return self
