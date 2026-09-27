"""The Postgres repository (SPEC §12; migrations in `supabase/migrations/`).

All of Sambhasha's SQL outside the migrations lives here. Each bundle row is stored with its
key columns and, in `data`, the row exactly as the domain model dumps it, so a stored bundle
reads back equal to the one imported. The database guards sealed bundles and the Event Log
itself; this module never updates or deletes either.
"""

from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Final, LiteralString
from uuid import UUID

import psycopg
from psycopg.rows import TupleRow
from psycopg.types.json import Jsonb
from pydantic import BaseModel

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

Row = tuple[Any, ...]

# Bundle list -> (table, its key columns; every table also has bundle_id, pos and data).
_ROW_TABLES: Final[dict[str, tuple[LiteralString, tuple[LiteralString, ...]]]] = {
    "facts": ("fact", ("id", "category", "item", "catalogue_ref", "day", "release", "origin")),
    "ledger": ("ledger_row", ("id", "target", "day_bucket", "tier")),
    "reports": ("report", ("id", "test_item_id", "variant", "status")),
    "consult_notes": ("consult_note", ("id", "specialty", "variant")),
    "raw_material": ("raw_material", ("id", "test", "release", "day")),
    "media": ("media", ("id",)),
    "gaps": ("gap", ("id", "item", "auto_generate")),
    "test_utility": ("test_utility", ("test_item_id", "utility")),
    "path_analysis": ("path_analysis", ("path_id", "kind")),
}
_HEAD_FIELDS: Final = ("case", "source", "clock", "vignette", "opening_statement_lay")


def _dump(model: BaseModel) -> Any:
    return model.model_dump(mode="json", by_alias=True)


class PostgresRepository:
    """Storage in the `sambhasha` schema. The caller owns the connection."""

    def __init__(self, connection: psycopg.Connection[TupleRow]) -> None:
        self._conn = connection

    # --- cases ---

    def add_bundle(self, bundle: CaseBundle, sha256: str) -> None:
        case_version_id, revision = split_bundle_id(bundle.bundle_id)
        dumped = _dump(bundle)
        try:
            with self._conn.transaction():
                self._lock_bundle_id(bundle.bundle_id)
                self._conn.execute(
                    "insert into sambhasha.case_bundle (bundle_id, case_version_id, revision,"
                    " schema_version, catalogue_version, sha256, head)"
                    " values (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        bundle.bundle_id,
                        case_version_id,
                        revision,
                        bundle.schema_version,
                        bundle.catalogue_version,
                        sha256,
                        Jsonb({key: dumped[key] for key in _HEAD_FIELDS}),
                    ),
                )
                for field, (table, columns) in _ROW_TABLES.items():
                    self._insert_rows(bundle.bundle_id, table, columns, getattr(bundle, field))
                self._conn.execute(
                    "insert into sambhasha.ground_truth (bundle_id, data) values (%s, %s)",
                    (bundle.bundle_id, Jsonb(dumped["ground_truth"])),
                )
                self._conn.execute(
                    "update sambhasha.case_bundle set sealed_at = now() where bundle_id = %s",
                    (bundle.bundle_id,),
                )
        except psycopg.errors.UniqueViolation as error:
            if error.diag.table_name != "case_bundle":
                raise
            raise DuplicateError(f"bundle {bundle.bundle_id} is already imported") from error

    def _lock_bundle_id(self, bundle_id: str) -> None:
        """Serialise imports of one bundle id, then refuse it if it is already stored."""
        self._conn.execute("select pg_advisory_xact_lock(hashtext(%s))", (bundle_id,))
        exists = self._conn.execute(
            "select 1 from sambhasha.case_bundle where bundle_id = %s", (bundle_id,)
        ).fetchone()
        if exists:
            raise DuplicateError(f"bundle {bundle_id} is already imported")

    def _insert_rows(
        self,
        bundle_id: str,
        table: LiteralString,
        columns: tuple[LiteralString, ...],
        rows: Sequence[BaseModel],
    ) -> None:
        names = ", ".join(("bundle_id", "pos", *columns, "data"))
        marks = ", ".join(["%s"] * (len(columns) + 3))
        query: LiteralString = f"insert into sambhasha.{table} ({names}) values ({marks})"  # noqa: S608
        with self._conn.cursor() as cursor:
            cursor.executemany(
                query,
                [
                    (bundle_id, pos, *(getattr(row, c) for c in columns), Jsonb(_dump(row)))
                    for pos, row in enumerate(rows)
                ],
            )

    def get_bundle(self, bundle_id: str) -> CaseBundle:
        head = self._one(
            "select schema_version, catalogue_version, head from sambhasha.case_bundle"
            " where bundle_id = %s",
            (bundle_id,),
            f"no bundle {bundle_id}",
        )
        schema_version, catalogue_version, fields = head
        truth = self._one(
            "select data from sambhasha.ground_truth where bundle_id = %s",
            (bundle_id,),
            f"bundle {bundle_id} has no ground truth",
        )
        lists = {
            field: [
                data
                for (data,) in self._conn.execute(
                    f"select data from sambhasha.{table} where bundle_id = %s order by pos",  # noqa: S608
                    (bundle_id,),
                )
            ]
            for field, (table, _) in _ROW_TABLES.items()
        }
        return CaseBundle.model_validate(
            {
                "bundle_id": bundle_id,
                "schema_version": schema_version,
                "catalogue_version": catalogue_version,
                **fields,
                **lists,
                "ground_truth": truth[0],
            }
        )

    def list_bundles(self) -> tuple[BundleRecord, ...]:
        rows = self._conn.execute(
            "select b.bundle_id, b.case_version_id, b.revision, b.schema_version,"
            " b.catalogue_version, b.sha256, b.imported_at,"
            " coalesce(e.primary_eligible, false), e.reason"
            " from sambhasha.case_bundle b"
            " left join sambhasha.bundle_eligibility e using (bundle_id)"
            " where b.sealed_at is not null order by b.bundle_id"
        ).fetchall()
        return tuple(
            BundleRecord(
                bundle_id=r[0],
                case_version_id=r[1],
                revision=r[2],
                schema_version=r[3],
                catalogue_version=r[4],
                sha256=r[5],
                imported_at=r[6],
                primary_eligible=r[7],
                eligibility_reason=r[8],
            )
            for r in rows
        )

    def set_eligibility(self, bundle_id: str, *, eligible: bool, reason: str) -> None:
        self._one(
            "select 1 from sambhasha.case_bundle where bundle_id = %s",
            (bundle_id,),
            f"no bundle {bundle_id}",
        )
        self._conn.execute(
            "insert into sambhasha.bundle_eligibility (bundle_id, primary_eligible, reason)"
            " values (%s, %s, %s) on conflict (bundle_id) do update"
            " set primary_eligible = excluded.primary_eligible, reason = excluded.reason,"
            " decided_at = now()",
            (bundle_id, eligible, reason),
        )

    def get_synthetic(
        self, bundle_id: str, code: str, day_bucket: int | None
    ) -> SyntheticRow | None:
        row = self._conn.execute(
            "select bundle_id, code, day_bucket, query, kind, result_text, rationale,"
            " confidence, checks, generator_model, prompt_version, gap_id, review_status,"
            " created_at from sambhasha.synthetic_ledger"
            " where bundle_id = %s and code = %s and day_bucket is not distinct from %s",
            (bundle_id, code, day_bucket),
        ).fetchone()
        return None if row is None else _synthetic(row)

    def add_synthetic(self, row: SyntheticRow) -> None:
        self._write(
            lambda: self._conn.execute(
                "insert into sambhasha.synthetic_ledger (bundle_id, code, day_bucket, query,"
                " kind, result_text, rationale, confidence, checks, generator_model,"
                " prompt_version, gap_id, review_status, created_at)"
                " values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    row.bundle_id,
                    row.code,
                    row.day_bucket,
                    row.query,
                    row.kind,
                    row.result_text,
                    row.rationale,
                    row.confidence,
                    Jsonb(list(row.checks)),
                    row.generator_model,
                    row.prompt_version,
                    row.gap_id,
                    row.review_status,
                    row.created_at,
                ),
            ),
            duplicate=f"a synthetic row for {row.bundle_id} {row.code} {row.day_bucket} exists",
            missing=f"no bundle {row.bundle_id}",
        )

    def synthetic_rows(self, bundle_id: str) -> tuple[SyntheticRow, ...]:
        rows = self._conn.execute(
            "select bundle_id, code, day_bucket, query, kind, result_text, rationale,"
            " confidence, checks, generator_model, prompt_version, gap_id, review_status,"
            " created_at from sambhasha.synthetic_ledger where bundle_id = %s"
            " order by created_at, code",
            (bundle_id,),
        ).fetchall()
        return tuple(_synthetic(r) for r in rows)

    # --- runs ---

    def add_run(self, run: Run) -> None:
        self._write(
            lambda: self._conn.execute(
                "insert into sambhasha.run (id, bundle_id, engine_version, config_hash,"
                " started_at, ended_at, status) values (%s, %s, %s, %s, %s, %s, %s)",
                (
                    run.id,
                    run.bundle_id,
                    run.engine_version,
                    run.config_hash,
                    run.started_at,
                    run.ended_at,
                    run.status,
                ),
            ),
            duplicate=f"run {run.id} already exists",
            missing=f"no bundle {run.bundle_id}",
        )

    def get_run(self, run_id: UUID) -> Run:
        row = self._one(
            "select id, bundle_id, engine_version, config_hash, started_at, ended_at, status"
            " from sambhasha.run where id = %s",
            (run_id,),
            f"no run {run_id}",
        )
        return Run(
            id=row[0],
            bundle_id=row[1],
            engine_version=row[2],
            config_hash=row[3],
            started_at=row[4],
            ended_at=row[5],
            status=row[6],
        )

    def finish_run(self, run_id: UUID, *, status: RunStatus, ended_at: datetime) -> Run:
        updated = self._conn.execute(
            "update sambhasha.run set status = %s, ended_at = %s where id = %s",
            (status, ended_at, run_id),
        )
        if updated.rowcount == 0:
            raise NotFoundError(f"no run {run_id}")
        return self.get_run(run_id)

    def append_event(self, event: Event) -> None:
        with self._conn.transaction():
            # Lock the run so that concurrent appends to it take their turn.
            self._one(
                "select 1 from sambhasha.run where id = %s for update",
                (event.run_id,),
                f"no run {event.run_id}",
            )
            row = self._conn.execute(
                "select count(*) from sambhasha.event where run_id = %s", (event.run_id,)
            ).fetchone()
            expected = row[0] if row else 0
            if event.seq != expected:
                raise SequenceError(f"run {event.run_id} expects event {expected}, not {event.seq}")
            self._write(
                lambda: self._conn.execute(
                    "insert into sambhasha.event (run_id, seq, sim_minutes, seat, type, payload,"
                    " visibility, source, model, prompt_version, tokens_in, tokens_out,"
                    " cost_usd, hash) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,"
                    " %s, %s)",
                    (
                        event.run_id,
                        event.seq,
                        event.sim_minutes,
                        event.seat,
                        event.type,
                        Jsonb(_dump(event.payload)),
                        list(event.visibility),
                        event.source,
                        event.model,
                        event.prompt_version,
                        event.tokens_in,
                        event.tokens_out,
                        event.cost_usd,
                        event.hash,
                    ),
                ),
                duplicate=f"run {event.run_id} already has event {event.seq}",
                missing=f"no run {event.run_id}",
                duplicate_error=SequenceError,
            )

    def events(self, run_id: UUID) -> tuple[Event, ...]:
        rows = self._conn.execute(
            "select run_id, seq, sim_minutes, seat, type, payload, visibility, source, model,"
            " prompt_version, tokens_in, tokens_out, cost_usd, hash"
            " from sambhasha.event where run_id = %s order by seq",
            (run_id,),
        ).fetchall()
        return tuple(
            Event.model_validate(
                {
                    "run_id": r[0],
                    "seq": r[1],
                    "sim_minutes": r[2],
                    "seat": r[3],
                    "type": r[4],
                    "payload": r[5],
                    "visibility": tuple(r[6]),
                    "source": r[7],
                    "model": r[8],
                    "prompt_version": r[9],
                    "tokens_in": r[10],
                    "tokens_out": r[11],
                    "cost_usd": r[12],
                    "hash": r[13],
                }
            )
            for r in rows
        )

    def put_order(self, order: Order) -> None:
        def write() -> None:
            written = self._conn.execute(
                'insert into sambhasha."order" (id, run_id, ordered_by, item_text, code,'
                " indication, route, status, cost_inr, ordered_at_min, due_at_min)"
                " values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                " on conflict (id) do update set ordered_by = excluded.ordered_by,"
                " item_text = excluded.item_text, code = excluded.code,"
                " indication = excluded.indication, route = excluded.route,"
                " status = excluded.status, cost_inr = excluded.cost_inr,"
                " ordered_at_min = excluded.ordered_at_min, due_at_min = excluded.due_at_min"
                ' where "order".run_id = excluded.run_id',
                (
                    order.id,
                    order.run_id,
                    order.ordered_by,
                    order.item_text,
                    order.code,
                    order.indication,
                    order.route,
                    order.status,
                    order.cost_inr,
                    order.ordered_at_min,
                    order.due_at_min,
                ),
            )
            if written.rowcount == 0:
                raise DuplicateError(f"order {order.id} belongs to another run")

        self._write(
            write, duplicate=f"order {order.id} already exists", missing=f"no run {order.run_id}"
        )

    def orders(self, run_id: UUID) -> tuple[Order, ...]:
        rows = self._conn.execute(
            "select id, run_id, ordered_by, item_text, code, indication, route, status,"
            ' cost_inr, ordered_at_min, due_at_min from sambhasha."order"'
            " where run_id = %s order by ordered_at_min, id",
            (run_id,),
        ).fetchall()
        fields = Order.model_fields.keys()
        return tuple(Order.model_validate(dict(zip(fields, r, strict=True))) for r in rows)

    def add_score(self, score: Score) -> None:
        self._write(
            lambda: self._conn.execute(
                "insert into sambhasha.score (id, run_id, data, rater, rater_type, dx_score)"
                " values (%s, %s, %s, %s, %s, %s)",
                (
                    score.id,
                    score.run_id,
                    Jsonb(_dump(score)),
                    score.rater,
                    score.rater_type,
                    score.dx_score,
                ),
            ),
            duplicate=f"score {score.id} already exists",
            missing=f"no run {score.run_id}",
        )

    def scores(self, run_id: UUID) -> tuple[Score, ...]:
        rows = self._conn.execute(
            "select data from sambhasha.score where run_id = %s order by recorded_at, id",
            (run_id,),
        ).fetchall()
        return tuple(Score.model_validate(data) for (data,) in rows)

    # --- helpers ---

    def _one(self, query: LiteralString, params: Iterable[object], missing: str) -> Row:
        row = self._conn.execute(query, tuple(params)).fetchone()
        if row is None:
            raise NotFoundError(missing)
        return row

    def _write(
        self,
        statement: Callable[[], object],
        *,
        duplicate: str,
        missing: str,
        duplicate_error: type[DuplicateError | SequenceError] = DuplicateError,
    ) -> None:
        """Run one write in a savepoint, turning key violations into repository errors."""
        try:
            with self._conn.transaction():
                statement()
        except psycopg.errors.UniqueViolation as error:
            raise duplicate_error(duplicate) from error
        except psycopg.errors.ForeignKeyViolation as error:
            raise NotFoundError(missing) from error


def _synthetic(row: Row) -> SyntheticRow:
    fields = (
        "bundle_id",
        "code",
        "day_bucket",
        "query",
        "kind",
        "result_text",
        "rationale",
        "confidence",
        "checks",
        "generator_model",
        "prompt_version",
        "gap_id",
        "review_status",
        "created_at",
    )
    data = dict(zip(fields, row, strict=True))
    return SyntheticRow.model_validate(
        {**data, "confidence": float(data["confidence"]), "checks": tuple(data["checks"])}
    )


@contextmanager
def open_postgres(url: str) -> Iterator[PostgresRepository]:
    """A repository on its own autocommit connection, closed afterwards."""
    with psycopg.connect(url, autocommit=True) as connection:
        yield PostgresRepository(connection)
