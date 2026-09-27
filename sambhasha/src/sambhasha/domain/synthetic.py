"""A result the Synthetic Findings Service generated for a request outside the catalogue
(SPEC §8; D-023). Kept in the run database's `synthetic_ledger`, one row per
(bundle, request code, day bucket), so the same request always gets the same result."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from sambhasha.domain.base import DomainModel, NonEmptyStr


class SyntheticRow(DomainModel):
    bundle_id: NonEmptyStr
    code: NonEmptyStr  # "REQ:" + the normalised request text
    day_bucket: int | None
    query: NonEmptyStr  # the request as the seat wrote it
    kind: NonEmptyStr  # the catalogue kinds it was coded against, e.g. "test"
    result_text: NonEmptyStr
    rationale: str
    confidence: Annotated[float, Field(ge=0, le=1)]
    checks: tuple[str, ...]  # the checks it passed
    generator_model: NonEmptyStr
    prompt_version: NonEmptyStr
    gap_id: str | None = None
    review_status: Literal["pending", "approved", "edited", "rejected"] = "pending"
    created_at: datetime
