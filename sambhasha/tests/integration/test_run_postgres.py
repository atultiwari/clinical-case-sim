"""P1.7: the pilot's efficient path, with the Event Log in Postgres."""

from pathlib import Path

import psycopg
import pytest

from sambhasha.storage.postgres import PostgresRepository
from tests.unit.engine.test_scheduler import EFFICIENT_PATH, _run

pytestmark = pytest.mark.integration


def test_the_efficient_path_runs_on_postgres(db: psycopg.Connection, tmp_path: Path) -> None:
    repo = PostgresRepository(db)

    result, _ = _run(EFFICIENT_PATH, tmp_path, repo=repo)

    assert result.run.status == "completed"
    stored = repo.events(result.run.id)
    assert stored == result.events
    assert stored[-1].hash == result.event_hash
    assert sorted(o.status for o in repo.orders(result.run.id)) == ["reported", "resulted"]
