"""Shared fixtures. Integration tests need the local database from `supabase start`.

Without it they are skipped, so `uv run pytest` passes on a fresh clone. Set
CASE_LIBRARY_REQUIRE_DB=1 (as CI does) to make a missing database a failure.
"""

import os
from collections.abc import Iterator

import psycopg
import pytest

LOCAL_DB_URL = "postgresql://postgres:postgres@127.0.0.1:55322/postgres"
CONNECT_TIMEOUT_SECONDS = 3


@pytest.fixture(scope="session")
def local_db() -> Iterator[psycopg.Connection]:
    url = os.environ.get("CASE_LIBRARY_LOCAL_DB_URL", LOCAL_DB_URL)
    try:
        conn = psycopg.connect(url, connect_timeout=CONNECT_TIMEOUT_SECONDS, autocommit=True)
    except psycopg.OperationalError as exc:
        if os.environ.get("CASE_LIBRARY_REQUIRE_DB") == "1":
            pytest.fail(f"Local database unreachable at {url}: {exc}")
        pytest.skip("Local database not running; start it with `supabase start`")
    with conn:
        yield conn
