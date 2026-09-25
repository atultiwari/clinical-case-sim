"""Schema 0.3 tables: presence, access and constraints (SPEC §10, PLAN L0.3)."""

import psycopg
import pytest

from tests.integration.conftest import seed_case_version

pytestmark = pytest.mark.integration

SPEC_TABLES = {
    "source_article", "case", "case_version", "fact", "raw_material", "media", "gap",
    "report", "consult_note", "ground_truth", "path_analysis", "synthetic_ledger",
    "test_utility", "bundle", "catalogue_item", "test_def", "component", "test_component",
    "normal_template", "diagnosis_def", "review_batch", "review_decision", "missing_request",
    "value_rule",  # formulas and physiology checks, loaded with the catalogue (L0.4)
}  # fmt: skip
INSERT_REPORT = (
    "insert into casevault.report"
    " (case_version_id, id, variant, status, status_line, generator, skill_version)"
    " values (%s, %s, %s, %s, %s, 'g', 's')"
)
INSERT_ITEM = (
    "insert into casevault.catalogue_item (id, kind, name, since_version) values (%s, %s, 'x', 0)"
)


def _tables(db: psycopg.Connection, *, rls_only: bool = False) -> set[str]:
    rows = db.execute(
        "select tablename from pg_tables"
        " where schemaname = 'casevault' and (rowsecurity or not %s)",
        (rls_only,),
    ).fetchall()
    return {row[0] for row in rows}


def test_every_spec_table_exists(db: psycopg.Connection) -> None:
    assert _tables(db) == SPEC_TABLES


def test_rls_is_on_for_every_table(db: psycopg.Connection) -> None:
    assert _tables(db, rls_only=True) == SPEC_TABLES


def test_no_client_policies(db: psycopg.Connection) -> None:
    row = db.execute("select count(*) from pg_policies where schemaname = 'casevault'").fetchone()

    assert row == (0,)


@pytest.mark.parametrize("role", ["anon", "authenticated"])
def test_client_roles_cannot_use_the_schema(db: psycopg.Connection, role: str) -> None:
    row = db.execute("select has_schema_privilege(%s, 'casevault', 'usage')", (role,)).fetchone()

    assert row == (False,)


def test_original_report_must_be_provisional_with_a_status_line(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)

    db.execute(INSERT_REPORT, (cv, "RP01", "original", "provisional", "Provisional report."))
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute(INSERT_REPORT, (cv, "RP02", "original", "final", "Final."))
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute(INSERT_REPORT, (cv, "RP03", "original", "provisional", None))


def test_catalogue_id_must_match_its_kind(db: psycopg.Connection) -> None:

    db.execute(INSERT_ITEM, ("LAB.CBC", "test"))
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute(INSERT_ITEM, ("DX.CBC", "test"))


def test_affected_ledger_rows_need_rationale_and_confidence(db: psycopg.Connection) -> None:
    cv = seed_case_version(db)

    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute(
            "insert into casevault.synthetic_ledger"
            " (case_version_id, target, tier, value, generator, skill_version)"
            " values (%s, 'CMP.ZPP', 'affected', '{}', 'g', 's')",
            (cv,),
        )


def test_case_version_id_matches_case_and_version(db: psycopg.Connection) -> None:
    db.execute("insert into casevault.\"case\" (id, source_type) values ('NID-9002', 'de_novo')")

    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute(
            "insert into casevault.case_version (id, case_id, version)"
            " values ('NID-9002@v2', 'NID-9002', 1)"
        )


def test_case_media_bucket_is_private(db: psycopg.Connection) -> None:
    storage = db.execute("select to_regclass('storage.buckets') is not null").fetchone()
    if storage != (True,):
        pytest.skip("Storage is not installed in this database (CI starts the database only)")

    row = db.execute("select public from storage.buckets where id = 'case-media'").fetchone()

    assert row == (False,)
