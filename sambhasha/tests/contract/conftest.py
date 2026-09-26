"""One contract suite, run against every repository implementation (PLAN P0.3).

The in-memory repository always runs. The Postgres one is marked `integration`: it needs
the local database from `supabase db start` and runs with `pytest -m integration`.
"""

from pathlib import Path

import psycopg
import pytest

from sambhasha.domain.case_file import CaseBundle, parse_bundle
from sambhasha.storage.memory import InMemoryRepository
from sambhasha.storage.postgres import PostgresRepository
from sambhasha.storage.repo import Repository

EXPORTS = Path(__file__).resolve().parents[3] / "case-library" / "exports"
PILOT_BUNDLE = EXPORTS / "PMC12949993@v1.r3.json"


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
