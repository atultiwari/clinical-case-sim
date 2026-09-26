"""A simulation run (SPEC §12). Every run starts clean (invariant I6)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import StringConstraints

from sambhasha.domain.base import DomainModel, NonEmptyStr

RunStatus = Literal["running", "completed", "aborted"]


class Run(DomainModel):
    id: UUID
    bundle_id: NonEmptyStr  # the bundle revision the run used (invariant I7)
    engine_version: NonEmptyStr
    config_hash: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    started_at: datetime
    status: RunStatus
    ended_at: datetime | None = None
