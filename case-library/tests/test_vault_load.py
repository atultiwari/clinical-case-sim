"""scripts/vault_load.py: only the Case Vault, one transaction per file, stop at a failure."""

from pathlib import Path

import psycopg
import pytest

from scripts import vault_load as vl


def test_the_url_must_be_set() -> None:
    with pytest.raises(vl.LoadError, match="not set"):
        vl.check_url(None)


def test_another_project_is_refused() -> None:
    with pytest.raises(vl.LoadError, match="does not point at the Case Vault"):
        vl.check_url(
            "postgresql://postgres.otherproject:pw@aws-0-x.pooler.supabase.com:5432/postgres"
        )


def test_the_case_vault_url_is_accepted() -> None:
    url = f"postgresql://owner.{vl.CASE_VAULT_REF}:pw@aws-0-x.pooler.supabase.com:5432/postgres"
    assert vl.check_url(url) == url


@pytest.mark.integration
def test_files_run_in_order_and_stop_at_the_first_failure(
    local_db: psycopg.Connection, tmp_path: Path
) -> None:
    table = "vault_load_test"
    good = tmp_path / "1.sql"
    good.write_text(f"begin; create table {table} (x int); insert into {table} values (1); commit;")  # noqa: S608 (fixed test table)
    bad = tmp_path / "2.sql"
    bad.write_text(f"begin; insert into {table} values (2); select 1/0; commit;")  # noqa: S608 (fixed test table)
    never = tmp_path / "3.sql"
    never.write_text(f"begin; insert into {table} values (3); commit;")  # noqa: S608 (fixed test table)
    try:
        results = vl.run_files(local_db, [good, bad, never])
        assert [r.ok for r in results] == [True, False]
        rows = local_db.execute(f"select x from {table} order by x").fetchall()  # noqa: S608
        assert rows == [(1,)]
    finally:
        local_db.execute(f"drop table if exists {table}")
