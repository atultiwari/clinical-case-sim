"""Fixtures for tests that write to the local Case Vault database."""

from collections.abc import Iterator
from pathlib import Path

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


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
MINI_GENERATOR = "claude-test via case-curate v0.0"


def seed_mini_case(db: psycopg.Connection, *, with_path: bool = True) -> str:
    """Load the fixture catalogue and case; return the draft case version id."""
    db.execute((FIXTURES / "mini_catalogue.sql").read_text(encoding="utf-8"))
    row = db.execute(
        "select casevault.import_case_json(%s::jsonb, %s, 'v0.0')",
        ((FIXTURES / "mini_case.json").read_text(encoding="utf-8"), MINI_GENERATOR),
    ).fetchone()
    assert row is not None
    cv = str(row[0])
    if with_path:
        db.execute(
            "insert into casevault.path_analysis (case_version_id, path_id, kind, name, items)"
            " values (%s, 'P1', 'efficient', 'Find the lead',"
            " '{HX.SUPPLEMENTS,LAB.BLOOD_LEAD,LAB.FILM,REF.TOXICOLOGY}')",
            (cv,),
        )
    return cv
