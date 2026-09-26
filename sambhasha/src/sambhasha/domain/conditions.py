"""Scoring conditions shared with Nidana (Case Library SPEC §10.4).

A condition is a small JSON object over catalogue ids. Ids ending in `.*` match every item
with that prefix. Evaluating conditions is the Evaluator's job (P1.8); this module only
parses and checks their shape.
"""

from typing import Annotated, Any, Self

from pydantic import Field, model_validator

from sambhasha.domain.base import DomainModel, NonEmptyStr

Ids = Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]


class Condition(DomainModel):
    """One or two keys; `not`, `all` and `any` nest further conditions."""

    dx_in: Ids | None = None
    evidence_has: Ids | None = None
    released_all: Ids | None = None
    released_any: Ids | None = None
    finding_released: Ids | None = None
    from_tests: Ids | None = None
    asked_any: Ids | None = None
    ordered_any: Ids | None = None
    ordered_all: Ids | None = None
    referred_any: Ids | None = None
    plan_has: Ids | None = None
    plan_has_any: Ids | None = None
    plan_before: tuple[NonEmptyStr, NonEmptyStr] | None = None
    not_: "Condition | None" = Field(default=None, alias="not")
    all_: "Annotated[tuple[Condition, ...], Field(min_length=1)] | None" = Field(
        default=None, alias="all"
    )
    any_: "Annotated[tuple[Condition, ...], Field(min_length=1)] | None" = Field(
        default=None, alias="any"
    )

    @model_validator(mode="after")
    def _check_shape(self) -> Self:
        keys = [name for name in type(self).model_fields if getattr(self, name) is not None]
        if not 1 <= len(keys) <= 2:
            raise ValueError(f"a condition has one or two keys, not {len(keys)}")
        if self.from_tests is not None and self.finding_released is None:
            raise ValueError("from_tests needs finding_released")
        return self

    def to_json_data(self) -> dict[str, Any]:
        """The condition as it appears in a bundle."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class ScoredItem(DomainModel):
    """A must-do or must-not-do item: text, and the condition that scores it.

    The JSON schema also allows a plain string, but only for schema 0.2 imports inside the
    Case Library; no published 0.3 bundle uses one, so Sambhasha requires the object form.
    """

    text: NonEmptyStr
    if_: Condition | None = Field(default=None, alias="if")


class RubricAnchor(DomainModel):
    """A diagnosis score (1 to 5) awarded when its condition holds."""

    score: Annotated[int, Field(ge=1, le=5)]
    text: NonEmptyStr
    if_: Condition = Field(alias="if")


class Rubric(DomainModel):
    default_score: Annotated[int, Field(ge=1, le=5)]
    rubric: tuple[RubricAnchor, ...]
