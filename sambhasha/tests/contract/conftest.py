"""One contract suite, run against every repository implementation (PLAN P0.3).

The in-memory repository always runs. The Postgres one is marked `integration`: it needs
the local database from `supabase db start` and runs with `pytest -m integration`.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from sambhasha.domain.case_file import CaseBundle, parse_bundle
from sambhasha.storage.memory import InMemoryRepository
from sambhasha.storage.postgres import PostgresRepository
from sambhasha.storage.repo import Repository

LOCAL_DB_URL = "postgresql://postgres:postgres@127.0.0.1:56322/postgres"
EXPORTS = Path(__file__).resolve().parents[3] / "case-library" / "exports"
PILOT_BUNDLE = EXPORTS / "PMC12949993@v1.r3.json"


def db_url() -> str:
    return os.environ.get("SAMBHASHA_TEST_DB_URL", LOCAL_DB_URL)


@pytest.fixture(scope="session")
def local_db() -> Iterator[psycopg.Connection]:
    """A connection to the local database, or a skip when it is not running."""
    try:
        conn = psycopg.connect(db_url(), connect_timeout=3, autocommit=True)
    except psycopg.OperationalError as error:
        if os.environ.get("SAMBHASHA_REQUIRE_DB") == "1":
            pytest.fail(f"local database unreachable at {db_url()}: {error}")
        pytest.skip("local database not running; start it with `supabase db start`")
    with conn:
        yield conn


@pytest.fixture
def db(local_db: psycopg.Connection) -> Iterator[psycopg.Connection]:
    """The local database inside a transaction that is always rolled back."""
    with local_db.transaction(force_rollback=True):
        yield local_db


@pytest.fixture(params=["memory", pytest.param("postgres", marks=pytest.mark.integration)])
def repo(request: pytest.FixtureRequest) -> Repository:
    if request.param == "memory":
        return InMemoryRepository()
    connection: psycopg.Connection = request.getfixturevalue("db")
    return PostgresRepository(connection)


@pytest.fixture(scope="session")
def pilot() -> CaseBundle:
    return parse_bundle(PILOT_BUNDLE.read_bytes())


@pytest.fixture(scope="session")
def pilot_sha256() -> str:
    return (PILOT_BUNDLE.parent / f"{PILOT_BUNDLE.name}.sha256").read_text().split()[0]
