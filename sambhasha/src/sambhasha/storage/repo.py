"""The repository interface every storage implementation provides (SPEC §12; PLAN P0.3).

Bundles are stored once and never change (invariant I7). The Event Log only grows, one
event at a time in sequence (invariant I6). Nothing here returns a mutable object.
"""

import re
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sambhasha.domain.base import DomainModel
from sambhasha.domain.case_file import CaseBundle
from sambhasha.domain.events import Event
from sambhasha.domain.orders import Order
from sambhasha.domain.runs import Run, RunStatus
from sambhasha.domain.scores import Score

_BUNDLE_ID = re.compile(r"(?P<case_version>.+)\.r(?P<revision>[0-9]+)")


class RepositoryError(Exception):
    """A storage request that cannot be carried out."""


class NotFoundError(RepositoryError):
    """The bundle, run or other record does not exist."""


class DuplicateError(RepositoryError):
    """The record already exists, and records here are written once."""


class SequenceError(RepositoryError):
    """An event is not the next one in its run's sequence."""


class BundleRecord(DomainModel):
    """A stored bundle in the case registry."""

    bundle_id: str
    case_version_id: str
    revision: int
    schema_version: str
    catalogue_version: int
    sha256: str
    imported_at: datetime
    primary_eligible: bool = False
    eligibility_reason: str | None = None


def split_bundle_id(bundle_id: str) -> tuple[str, int]:
    """`PMC12949993@v1.r3` -> (`PMC12949993@v1`, 3)."""
    match = _BUNDLE_ID.fullmatch(bundle_id)
    if match is None:
        raise ValueError(f"not a bundle id: {bundle_id!r}")
    return match["case_version"], int(match["revision"])


class CaseRepository(Protocol):
    def add_bundle(self, bundle: CaseBundle, sha256: str) -> None: ...
    def get_bundle(self, bundle_id: str) -> CaseBundle: ...
    def list_bundles(self) -> tuple[BundleRecord, ...]: ...
    def set_eligibility(self, bundle_id: str, *, eligible: bool, reason: str) -> None: ...


class RunRepository(Protocol):
    def add_run(self, run: Run) -> None: ...
    def get_run(self, run_id: UUID) -> Run: ...
    def finish_run(self, run_id: UUID, *, status: RunStatus, ended_at: datetime) -> Run: ...
    def append_event(self, event: Event) -> None: ...
    def events(self, run_id: UUID) -> tuple[Event, ...]: ...
    def put_order(self, order: Order) -> None: ...
    def orders(self, run_id: UUID) -> tuple[Order, ...]: ...
    def add_score(self, score: Score) -> None: ...
    def scores(self, run_id: UUID) -> tuple[Score, ...]: ...


class Repository(CaseRepository, RunRepository, Protocol):
    """Everything the engine, importer and Evaluator store."""
