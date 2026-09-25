"""casevault_reader: the Case Studio's and the scripts' read-only role (SPEC §8, PLAN L0.7)."""

import psycopg
import pytest
from psycopg import sql

from tests.integration.conftest import seed_mini_case

pytestmark = pytest.mark.integration

TABLES = (
    "source_article",
    "case",
    "case_version",
    "fact",
    "raw_material",
    "media",
    "gap",
    "report",
    "consult_note",
    "ground_truth",
    "path_analysis",
    "synthetic_ledger",
    "test_utility",
    "bundle",
    "catalogue_item",
    "test_def",
    "component",
    "test_component",
    "normal_template",
    "diagnosis_def",
    "value_rule",
    "review_batch",
    "review_decision",
    "missing_request",
)


@pytest.fixture
def seeded(db: psycopg.Connection) -> tuple[psycopg.Connection, str]:
    """The fixture case, loaded as the owner; the test then switches role."""
    return db, seed_mini_case(db)


def _as(db: psycopg.Connection, role: str) -> None:
    db.execute(f"set local role {role}")


@pytest.mark.parametrize("table", TABLES)
def test_the_reader_can_read_every_table(
    seeded: tuple[psycopg.Connection, str], table: str
) -> None:
    db, _ = seeded
    _as(db, "casevault_reader")
    db.execute(sql.SQL("select * from casevault.{} limit 1").format(sql.Identifier(table)))


def test_the_reader_sees_rows_despite_row_level_security(
    seeded: tuple[psycopg.Connection, str],
) -> None:
    db, cv = seeded
    _as(db, "casevault_reader")
    row = db.execute(
        "select count(*) from casevault.fact where case_version_id = %s", (cv,)
    ).fetchone()
    assert row is not None
    assert row[0] > 0


@pytest.mark.parametrize(
    "statement",
    [
        "insert into casevault.missing_request (source, query) values ('nidana', 'x')",
        "update casevault.case_version set vignette = 'x'",
        "delete from casevault.fact",
        "update casevault.catalogue_item set name = 'x'",
        "select casevault.import_case_json('{}'::jsonb, 'g', 'v')",
        "select casevault.resolve_normals('X@v1')",
        "select casevault.compute_derived('X@v1', 'g', 'v')",
    ],
)
def test_the_reader_cannot_write(seeded: tuple[psycopg.Connection, str], statement: str) -> None:
    db, _ = seeded
    _as(db, "casevault_reader")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(statement)


def test_the_reader_can_run_the_checks_and_export(
    seeded: tuple[psycopg.Connection, str],
) -> None:
    db, cv = seeded
    _as(db, "casevault_reader")
    db.execute("select * from casevault.coverage_report(%s)", (cv,))
    db.execute("select * from casevault.check_consistency(%s)", (cv,))
    db.execute("select * from casevault.leak_scan(%s)", (cv,))
    blockers = db.execute("select * from casevault.export_blockers(%s)", (cv,)).fetchall()
    assert any("not frozen" in b[0] for b in blockers)


@pytest.mark.parametrize("role", ["anon", "authenticated"])
def test_nidana_player_roles_cannot_read_the_case_vault(
    seeded: tuple[psycopg.Connection, str], role: str
) -> None:
    db, _ = seeded
    _as(db, role)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("select * from casevault.ground_truth")
