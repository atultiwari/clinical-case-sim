"""A rater's score for a run (SPEC §12, §13)."""

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, NonNegativeInt, PositiveInt

from sambhasha.domain.base import DomainModel, NonEmptyStr

CORRECT_DX_SCORE = 4  # SDBench-style: 4 or more counts as correct (D-014)


class ScoringMapping(DomainModel):
    """How the run's free text was mapped to catalogue ids before scoring (D-022)."""

    diagnosis: str | None
    differential: tuple[str | None, ...] = ()
    plan: tuple[str, ...] = ()
    referrals: tuple[str, ...] = ()
    report_findings: dict[str, tuple[str, ...]] = Field(default_factory=dict)  # label -> FND ids


class Score(DomainModel):
    id: UUID
    run_id: UUID
    rater: NonEmptyStr
    rater_type: Literal["llm", "human"]
    dx_score: Annotated[int, Field(ge=1, le=5)]
    dx_rank: PositiveInt | None = None  # rank of the true diagnosis in the final differential
    plan_rating: Literal["appropriate", "acceptable", "unsafe"] | None = None
    must_do_hit: NonNegativeInt | None = None
    must_not_do_hit: NonNegativeInt | None = None
    cost_inr: Annotated[Decimal, Field(ge=0)] | None = None
    sim_hours: Annotated[float, Field(ge=0)] | None = None
    turns: NonNegativeInt | None = None
    unnecessary_tests: NonNegativeInt | None = None
    referrals_justified: NonNegativeInt | None = None
    referrals_missed: NonNegativeInt | None = None
    safety_flags: tuple[str, ...] = ()
    synthetic_dependence: Annotated[float, Field(ge=0, le=1)] | None = None
    used_fallback: bool = False  # the run used the out-of-catalogue service (D-023)
    notes: str | None = None
    mapping: ScoringMapping | None = None

    @property
    def dx_correct(self) -> bool:
        return self.dx_score >= CORRECT_DX_SCORE

    @property
    def top1(self) -> bool:
        return self.dx_rank == 1

    @property
    def top3(self) -> bool:
        return self.dx_rank is not None and self.dx_rank <= 3
