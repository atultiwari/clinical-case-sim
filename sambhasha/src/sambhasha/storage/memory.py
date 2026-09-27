"""The in-memory repository, for unit tests and fake runs (SPEC §12).

It stores the frozen domain objects themselves, so what comes back is what went in.
"""

from datetime import UTC, datetime
from uuid import UUID

from sambhasha.domain.case_file import CaseBundle
from sambhasha.domain.events import Event
from sambhasha.domain.orders import Order
from sambhasha.domain.runs import Run, RunStatus
from sambhasha.domain.scores import Score
from sambhasha.domain.synthetic import SyntheticRow
from sambhasha.storage.repo import (
    BundleRecord,
    DuplicateError,
    NotFoundError,
    SequenceError,
    split_bundle_id,
)


class InMemoryRepository:
    def __init__(self) -> None:
        self._bundles: dict[str, CaseBundle] = {}
        self._records: dict[str, BundleRecord] = {}
        self._runs: dict[UUID, Run] = {}
        self._events: dict[UUID, tuple[Event, ...]] = {}
        self._orders: dict[UUID, Order] = {}
        self._scores: dict[UUID, Score] = {}
        self._synthetic: dict[tuple[str, str, int | None], SyntheticRow] = {}

    # --- cases ---

    def add_bundle(self, bundle: CaseBundle, sha256: str) -> None:
        if bundle.bundle_id in self._bundles:
            raise DuplicateError(f"bundle {bundle.bundle_id} is already imported")
        case_version_id, revision = split_bundle_id(bundle.bundle_id)
        self._bundles[bundle.bundle_id] = bundle
        self._records[bundle.bundle_id] = BundleRecord(
            bundle_id=bundle.bundle_id,
            case_version_id=case_version_id,
            revision=revision,
            schema_version=bundle.schema_version,
            catalogue_version=bundle.catalogue_version,
            sha256=sha256,
            imported_at=datetime.now(UTC),
        )

    def get_bundle(self, bundle_id: str) -> CaseBundle:
        try:
            return self._bundles[bundle_id]
        except KeyError:
            raise NotFoundError(f"no bundle {bundle_id}") from None

    def list_bundles(self) -> tuple[BundleRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def set_eligibility(self, bundle_id: str, *, eligible: bool, reason: str) -> None:
        record = self._records.get(bundle_id)
        if record is None:
            raise NotFoundError(f"no bundle {bundle_id}")
        self._records[bundle_id] = record.model_copy(
            update={"primary_eligible": eligible, "eligibility_reason": reason}
        )

    def get_synthetic(
        self, bundle_id: str, code: str, day_bucket: int | None
    ) -> SyntheticRow | None:
        return self._synthetic.get((bundle_id, code, day_bucket))

    def add_synthetic(self, row: SyntheticRow) -> None:
        if row.bundle_id not in self._bundles:
            raise NotFoundError(f"no bundle {row.bundle_id}")
        key = (row.bundle_id, row.code, row.day_bucket)
        if key in self._synthetic:
            raise DuplicateError(f"a synthetic row for {key} already exists")
        self._synthetic[key] = row

    def synthetic_rows(self, bundle_id: str) -> tuple[SyntheticRow, ...]:
        return tuple(r for (b, _, _), r in self._synthetic.items() if b == bundle_id)

    # --- runs ---

    def add_run(self, run: Run) -> None:
        if run.id in self._runs:
            raise DuplicateError(f"run {run.id} already exists")
        if run.bundle_id not in self._bundles:
            raise NotFoundError(f"no bundle {run.bundle_id}")
        self._runs[run.id] = run
        self._events[run.id] = ()

    def get_run(self, run_id: UUID) -> Run:
        try:
            return self._runs[run_id]
        except KeyError:
            raise NotFoundError(f"no run {run_id}") from None

    def finish_run(self, run_id: UUID, *, status: RunStatus, ended_at: datetime) -> Run:
        finished = self.get_run(run_id).model_copy(update={"status": status, "ended_at": ended_at})
        self._runs[run_id] = finished
        return finished

    def append_event(self, event: Event) -> None:
        log = self._events.get(event.run_id)
        if log is None:
            raise NotFoundError(f"no run {event.run_id}")
        if event.seq != len(log):
            raise SequenceError(f"run {event.run_id} expects event {len(log)}, not {event.seq}")
        self._events[event.run_id] = (*log, event)

    def events(self, run_id: UUID) -> tuple[Event, ...]:
        return self._events.get(run_id, ())

    def put_order(self, order: Order) -> None:
        self.get_run(order.run_id)
        existing = self._orders.get(order.id)
        if existing is not None and existing.run_id != order.run_id:
            raise DuplicateError(f"order {order.id} belongs to another run")
        self._orders[order.id] = order

    def orders(self, run_id: UUID) -> tuple[Order, ...]:
        mine = (o for o in self._orders.values() if o.run_id == run_id)
        return tuple(sorted(mine, key=lambda o: (o.ordered_at_min, str(o.id))))

    def add_score(self, score: Score) -> None:
        self.get_run(score.run_id)
        if score.id in self._scores:
            raise DuplicateError(f"score {score.id} already exists")
        self._scores[score.id] = score

    def scores(self, run_id: UUID) -> tuple[Score, ...]:
        return tuple(s for s in self._scores.values() if s.run_id == run_id)
