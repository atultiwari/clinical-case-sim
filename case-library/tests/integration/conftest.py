"""Fixtures for tests that write to the local Case Vault database."""

from collections.abc import Iterator

import psycopg
import pytest


@pytest.fixture
def db(local_db: psycopg.Connection) -> Iterator[psycopg.Connection]:
    """The local database inside a transaction that is always rolled back."""
    with local_db.transaction(force_rollback=True):
        yield local_db


def seed_case_version(db: psycopg.Connection, case_id: str = "NID-9001", version: int = 1) -> str:
    """Insert a de novo case and a draft version of it; return the version id."""
    db.execute(
        "insert into casevault.\"case\" (id, source_type) values (%s, 'de_novo')", (case_id,)
    )
    db.execute(
        "insert into casevault.case_version (id, case_id, version) values (%s, %s, %s)",
        (f"{case_id}@v{version}", case_id, version),
    )
    return f"{case_id}@v{version}"
