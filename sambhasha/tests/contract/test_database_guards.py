"""Guards that live in the database itself (SPEC §12; invariants I6 and I7; PLAN P0.3).

Whatever code connects, a sealed bundle's rows cannot change and the Event Log is insert-only.
"""

from datetime import UTC, datetime
from uuid import uuid4

import psycopg
import pytest

from sambhasha.domain.actions import AskHistory
from sambhasha.domain.case_file import CaseBundle
from sambhasha.domain.events import Event
from sambhasha.domain.runs import Run
from sambhasha.storage.postgres import PostgresRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def stored(db: psycopg.Connection, pilot: CaseBundle, pilot_sha256: str) -> Run:
    repo = PostgresRepository(db)
    repo.add_bundle(pilot, pilot_sha256)
    run = Run(
        id=uuid4(),
        bundle_id=pilot.bundle_id,
        engine_version="0.1.0",
        config_hash="c" * 64,
        started_at=datetime(2026, 9, 26, tzinfo=UTC),
        status="running",
    )
    repo.add_run(run)
    repo.append_event(
        Event(
            run_id=run.id,
            seq=0,
            sim_minutes=0,
            seat="attending",
            type="request",
            payload=AskHistory(question="Any supplements?"),
            visibility=("team",),
            source="seat",
        )
    )
    return run


def _refused(db: psycopg.Connection, sql: str, *params: object) -> str:
    with pytest.raises(psycopg.errors.RaiseException) as caught, db.transaction():
        db.execute(sql, params)
    return str(caught.value)


@pytest.mark.parametrize(
    "sql",
    [
        "update sambhasha.fact set item = 'changed' where bundle_id = %s and id = 'H01'",
        "delete from sambhasha.fact where bundle_id = %s and id = 'H01'",
        "update sambhasha.ledger_row set tier = 'normal' where bundle_id = %s",
        "update sambhasha.ground_truth set data = '{}' where bundle_id = %s",
        "delete from sambhasha.consult_note where bundle_id = %s",
        "update sambhasha.case_bundle set sha256 = repeat('0', 64) where bundle_id = %s",
        "delete from sambhasha.case_bundle where bundle_id = %s",
    ],
)
def test_a_sealed_bundle_cannot_change(
    db: psycopg.Connection, stored: Run, pilot: CaseBundle, sql: str
) -> None:
    assert "sealed" in _refused(db, sql, pilot.bundle_id)


def test_no_row_can_be_added_to_a_sealed_bundle(
    db: psycopg.Connection, stored: Run, pilot: CaseBundle
) -> None:
    message = _refused(
        db,
        "insert into sambhasha.gap (bundle_id, id, pos, item, auto_generate, data)"
        " values (%s, 'G99', 99, 'Invented', true, '{}')",
        pilot.bundle_id,
    )

    assert "sealed" in message


def test_an_event_cannot_be_updated(db: psycopg.Connection, stored: Run) -> None:
    message = _refused(
        db, "update sambhasha.event set sim_minutes = 99 where run_id = %s", stored.id
    )

    assert "insert-only" in message


def test_an_event_cannot_be_deleted(db: psycopg.Connection, stored: Run) -> None:
    message = _refused(db, "delete from sambhasha.event where run_id = %s", stored.id)

    assert "insert-only" in message


def test_eligibility_stays_changeable_after_sealing(
    db: psycopg.Connection, stored: Run, pilot: CaseBundle
) -> None:
    repo = PostgresRepository(db)

    repo.set_eligibility(pilot.bundle_id, eligible=False, reason="S-010")

    assert repo.list_bundles()[0].eligibility_reason == "S-010"


def test_the_pilot_rows_are_all_stored(
    db: psycopg.Connection, stored: Run, pilot: CaseBundle
) -> None:
    counts = {
        table: db.execute(
            f"select count(*) from sambhasha.{table} where bundle_id = %s",  # noqa: S608
            (pilot.bundle_id,),
        ).fetchone()
        for table in (
            "fact",
            "ledger_row",
            "report",
            "consult_note",
            "raw_material",
            "media",
            "gap",
        )
    }

    assert {t: c[0] for t, c in counts.items() if c} == {
        "fact": len(pilot.facts),
        "ledger_row": len(pilot.ledger),
        "report": len(pilot.reports),
        "consult_note": len(pilot.consult_notes),
        "raw_material": len(pilot.raw_material),
        "media": len(pilot.media),
        "gap": len(pilot.gaps),
    }
