"""Integration checks against the local Supabase database (`supabase start`)."""

import psycopg
import pytest

pytestmark = pytest.mark.integration

POSTGRES_17 = 170000


def test_local_database_runs_postgres_17(local_db: psycopg.Connection) -> None:
    row = local_db.execute("select current_setting('server_version_num')::int").fetchone()

    assert row is not None
    assert row[0] // 10000 * 10000 == POSTGRES_17


def test_local_database_is_the_supabase_image(local_db: psycopg.Connection) -> None:
    row = local_db.execute(
        "select count(*) from pg_roles where rolname in ('anon', 'authenticated', 'service_role')"
    ).fetchone()

    assert row == (3,)
