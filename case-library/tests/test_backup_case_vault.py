"""scripts/backup_case_vault.py with a fake `supabase db dump` (no network)."""

import secrets
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import pytest

from scripts import backup_case_vault as bk

# Made up per run (with an "@" so the URL must percent-encode it); never a real one.
FAKE_PASSWORD = f"{secrets.token_hex(4)}@{secrets.token_hex(4)}"
URL = f"postgresql://postgres.ref:{quote(FAKE_PASSWORD, safe='')}@pooler.example.com:5432/postgres"
SCHEMA_SQL = "".join(f'CREATE TABLE "casevault"."t{i}" (id int);\n' for i in range(24))


class FakeDump:
    """Writes the files `supabase db dump` would, and records how it was called."""

    def __init__(self, *, fail: bool = False, schema_sql: str = SCHEMA_SQL) -> None:
        self.fail = fail
        self.schema_sql = schema_sql
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def __call__(
        self, argv: Sequence[str], env: Mapping[str, str]
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((list(argv), dict(env)))
        if self.fail:
            return subprocess.CompletedProcess(argv, 1, "", f"auth failed for {FAKE_PASSWORD}")
        target = Path(argv[argv.index("--file") + 1])
        is_data = "--data-only" in argv
        target.write_text("COPY casevault.fact FROM stdin;\n" if is_data else self.schema_sql)
        return subprocess.CompletedProcess(argv, 0, "", "")


def _at(day: int) -> datetime:
    return datetime(2026, 9, day, 21, 0, tzinfo=UTC)


def test_split_url_keeps_the_password_out_of_the_url() -> None:
    conn = bk.split_url(URL)

    assert conn.url == "postgresql://postgres.ref@pooler.example.com:5432/postgres"
    assert conn.password == FAKE_PASSWORD


@pytest.mark.parametrize(
    "url", ["https://x@host/db", "postgresql://user@host/db", "postgresql:///db"]
)
def test_split_url_refuses_unusable_urls(url: str) -> None:
    with pytest.raises(bk.BackupError):
        bk.split_url(url)


def test_backup_dumps_casevault_only_with_password_in_env(tmp_path: Path) -> None:
    dump = FakeDump()

    result = bk.backup(bk.split_url(URL), tmp_path, now=_at(25), runner=dump)

    assert result.folder == tmp_path / "20260925T210000Z"
    assert sorted(p.name for p in result.folder.iterdir()) == [
        "SHA256SUMS",
        "data.sql",
        "schema.sql",
    ]
    for argv, env in dump.calls:
        assert argv[argv.index("--schema") + 1] == "casevault"
        assert FAKE_PASSWORD not in " ".join(argv)
        assert env["PGPASSWORD"] == FAKE_PASSWORD
    assert "--data-only" in dump.calls[1][0]


def test_failed_dump_leaves_nothing_behind_and_hides_the_password(tmp_path: Path) -> None:
    with pytest.raises(bk.BackupError, match=r"\*\*\*") as err:
        bk.backup(bk.split_url(URL), tmp_path, now=_at(25), runner=FakeDump(fail=True))

    assert FAKE_PASSWORD not in str(err.value)
    assert list(tmp_path.iterdir()) == []


def test_a_near_empty_schema_dump_is_refused(tmp_path: Path) -> None:
    with pytest.raises(bk.BackupError, match="expected"):
        bk.backup(bk.split_url(URL), tmp_path, now=_at(25), runner=FakeDump(schema_sql="--\n"))


def test_a_dump_touching_play_is_refused(tmp_path: Path) -> None:
    leaky = SCHEMA_SQL + 'CREATE TABLE "play"."session" (id int);\n'

    with pytest.raises(bk.BackupError, match="play"):
        bk.backup(bk.split_url(URL), tmp_path, now=_at(25), runner=FakeDump(schema_sql=leaky))


def test_display_columns_are_not_mistaken_for_play(tmp_path: Path) -> None:
    schema = SCHEMA_SQL + "-- for display.\n"

    bk.backup(bk.split_url(URL), tmp_path, now=_at(25), runner=FakeDump(schema_sql=schema))


def test_old_backups_are_pruned_and_other_files_left_alone(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("keep me")
    conn = bk.split_url(URL)
    for day in range(1, 6):
        bk.backup(conn, tmp_path, now=_at(day), runner=FakeDump(), keep=3)

    kept = sorted(p.name for p in tmp_path.iterdir() if p.is_dir())

    assert kept == ["20260903T210000Z", "20260904T210000Z", "20260905T210000Z"]
    assert (tmp_path / "notes.txt").read_text() == "keep me"


def test_main_reports_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    env = {bk.BACKUP_URL_KEY: URL, bk.BACKUP_DIR_KEY: str(tmp_path)}

    assert bk.main(env, runner=FakeDump()) == 0
    assert "backup ok" in capsys.readouterr().out


def test_main_explains_a_missing_url(capsys: pytest.CaptureFixture[str]) -> None:
    assert bk.main({}, runner=FakeDump()) == 1
    assert "CASE_VAULT_DB_URL_BACKUP is not set" in capsys.readouterr().err


def test_main_reports_a_failed_dump(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    env = {bk.BACKUP_URL_KEY: URL, bk.BACKUP_DIR_KEY: str(tmp_path)}

    assert bk.main(env, runner=FakeDump(fail=True)) == 1
    err = capsys.readouterr().err
    assert "backup FAILED" in err
    assert FAKE_PASSWORD not in err
