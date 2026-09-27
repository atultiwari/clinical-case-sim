"""Shared fixtures: the local database for tests marked `integration`."""

import os
from collections.abc import Iterator

import psycopg
import pytest
from hypothesis import HealthCheck, settings

from sambhasha.config import LOCAL_DB_URL

# The invariant suite's random runs: 40 per test in CI; `HYPOTHESIS_PROFILE=thorough` for 400.
settings.register_profile(
    "default",
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
settings.register_profile(
    "thorough",
    max_examples=400,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


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
        row = conn.execute(
            "select (select count(*) from sambhasha.case_bundle)"
            " + (select count(*) from sambhasha.run)"
        ).fetchone()
        if row and row[0]:
            pytest.fail(
                "the local run database holds imported bundles or runs, which the tests would"
                " clash with; run `supabase db reset` first"
            )
        yield conn


@pytest.fixture
def db(local_db: psycopg.Connection) -> Iterator[psycopg.Connection]:
    """The local database inside a transaction that is always rolled back."""
    with local_db.transaction(force_rollback=True):
        yield local_db
