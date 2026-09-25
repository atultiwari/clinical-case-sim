"""Nightly backup of the Case Vault's `casevault` schema (SPEC §4.2, PLAN L0.3).

    uv run --env-file .env python -m scripts.backup_case_vault

The Free plan has no downloadable backups, so this dump and the exported
bundles in git are the backup. It dumps the `casevault` schema only, never
Nidana's `play` schema (testers' data), through the session pooler with the
Supabase CLI, whose pg_dump matches the server's Postgres 17. Docker must be
running. Each run writes a timestamped folder with schema.sql, data.sql and
SHA256SUMS, and keeps the newest KEEP_BACKUPS folders.

The password never goes on a command line: the URL is passed without it and
the password travels in PGPASSWORD.
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

BACKUP_URL_KEY = "CASE_VAULT_DB_URL_BACKUP"
BACKUP_DIR_KEY = "CASE_VAULT_BACKUP_DIR"
DEFAULT_BACKUP_DIR = Path.home() / "CaseVaultBackups"
SCHEMA = "casevault"
KEEP_BACKUPS = 14
STAMP_FORMAT = "%Y%m%dT%H%M%SZ"
STAMP_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")
# A schema dump that holds fewer tables than this is not a real backup.
MIN_TABLES = 20

Runner = Callable[[Sequence[str], Mapping[str, str]], subprocess.CompletedProcess[str]]


class BackupError(RuntimeError):
    """The backup failed. The message says why, without the password."""


@dataclass(frozen=True)
class Connection:
    url: str  # without the password
    password: str


@dataclass(frozen=True)
class BackupResult:
    folder: Path
    files: tuple[Path, ...]
    removed: tuple[Path, ...]


def split_url(url: str) -> Connection:
    """Separate the password from a postgresql:// URL."""
    parts = urlsplit(url)
    if parts.scheme not in ("postgresql", "postgres") or not parts.hostname:
        raise BackupError(f"{BACKUP_URL_KEY} must be a postgresql:// URL with a host.")
    if parts.password is None:
        raise BackupError(f"{BACKUP_URL_KEY} has no password.")
    host = parts.hostname + (f":{parts.port}" if parts.port else "")
    netloc = f"{parts.username}@{host}" if parts.username else host
    return Connection(urlunsplit(parts._replace(netloc=netloc)), unquote(parts.password))


def dump_commands(conn: Connection, folder: Path) -> list[list[str]]:
    base = ["supabase", "db", "dump", "--db-url", conn.url, "--schema", SCHEMA]
    return [
        [*base, "--file", str(folder / "schema.sql")],
        [*base, "--data-only", "--use-copy", "--file", str(folder / "data.sql")],
    ]


def run_command(argv: Sequence[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        list(argv), env=dict(env), capture_output=True, text=True, check=False
    )


def backup(
    conn: Connection,
    root: Path,
    *,
    now: datetime | None = None,
    runner: Runner = run_command,
    keep: int = KEEP_BACKUPS,
) -> BackupResult:
    """Dump into a new timestamped folder under root, then prune old folders."""
    stamp = (now or datetime.now(UTC)).strftime(STAMP_FORMAT)
    folder = root / stamp
    partial = root / f".{stamp}.partial"
    partial.mkdir(parents=True, exist_ok=False)
    try:
        env = {**os.environ, "PGPASSWORD": conn.password}
        for argv in dump_commands(conn, partial):
            _run_dump(argv, env, runner, conn.password)
        files = _verify(partial)
        _write_checksums(partial, files)
        partial.rename(folder)
    except BaseException:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    removed = prune(root, keep)
    return BackupResult(folder, tuple(folder / f.name for f in files), removed)


def _run_dump(argv: Sequence[str], env: Mapping[str, str], runner: Runner, password: str) -> None:
    result = runner(argv, env)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "no output").strip().replace(password, "***")
        raise BackupError(f"supabase db dump failed ({result.returncode}): {message[-800:]}")


def _verify(folder: Path) -> list[Path]:
    schema, data = folder / "schema.sql", folder / "data.sql"
    for path in (schema, data):
        if not path.is_file():
            raise BackupError(f"{path.name} was not written.")
    tables = len(re.findall(rf'CREATE TABLE (IF NOT EXISTS )?"?{SCHEMA}"?\.', schema.read_text()))
    if tables < MIN_TABLES:
        raise BackupError(f"schema.sql holds {tables} {SCHEMA} tables; expected {MIN_TABLES}+.")
    if re.search(r'(?<![\w])"?play"?\.', schema.read_text() + data.read_text()):
        raise BackupError("The dump contains the play schema, which must never be backed up here.")
    return [schema, data]


def _write_checksums(folder: Path, files: Sequence[Path]) -> None:
    lines = [f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n" for f in files]
    (folder / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")


def prune(root: Path, keep: int) -> tuple[Path, ...]:
    """Remove the oldest backup folders beyond `keep`. Other files are never touched."""
    folders = sorted(p for p in root.iterdir() if p.is_dir() and STAMP_PATTERN.match(p.name))
    old = folders[: max(len(folders) - keep, 0)]
    for folder in old:
        shutil.rmtree(folder)
    return tuple(old)


def main(env: Mapping[str, str] | None = None, runner: Runner = run_command) -> int:
    source = os.environ if env is None else env
    url = source.get(BACKUP_URL_KEY, "").strip()
    root = Path(source.get(BACKUP_DIR_KEY, "").strip() or DEFAULT_BACKUP_DIR).expanduser()
    try:
        if not url:
            raise BackupError(f"{BACKUP_URL_KEY} is not set in .env.")
        result = backup(split_url(url), root, runner=runner)
    except (BackupError, OSError) as exc:
        print(f"{datetime.now(UTC):%Y-%m-%d %H:%M}Z backup FAILED: {exc}", file=sys.stderr)
        return 1
    sizes = ", ".join(f"{f.name} {f.stat().st_size:,} bytes" for f in result.files)
    print(f"{datetime.now(UTC):%Y-%m-%d %H:%M}Z backup ok: {result.folder} ({sizes})")
    if result.removed:
        print(f"Removed {len(result.removed)} old backup(s), keeping the newest {KEEP_BACKUPS}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
