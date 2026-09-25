"""Run rendered SQL files against the Case Vault, for Atul to run himself (PLAN L1.3).

    uv run --env-file .env python -m scripts.vault_load build/batch1/*.sql

Loads that are too large for the Supabase connector (catalogue versions, whole
cases from scripts/case_sql.py) are run by Atul with this script, under his own
write-capable login in CASE_VAULT_DB_URL_OWNER (never committed, never shown to
Claude). Each file is one transaction: it commits whole or not at all. The
script stops at the first failure and refuses any database that is not the Case
Vault project.
"""

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import psycopg

CASE_VAULT_REF = "vxiymbaxsiavxuyxzhnt"
URL_VARIABLE = "CASE_VAULT_DB_URL_OWNER"


class LoadError(RuntimeError):
    """The load cannot start or a file failed. The message says which and why."""


@dataclass(frozen=True)
class FileResult:
    path: Path
    ok: bool
    message: str


def check_url(url: str | None) -> str:
    """The Case Vault URL, or a LoadError that says what is wrong with it."""
    if not url:
        raise LoadError(
            f"{URL_VARIABLE} is not set. Add it to case-library/.env (never commit it)."
        )
    if CASE_VAULT_REF not in url:
        raise LoadError(f"{URL_VARIABLE} does not point at the Case Vault ({CASE_VAULT_REF}).")
    return url


def run_files(db: psycopg.Connection, files: Sequence[Path]) -> list[FileResult]:
    """Run each file in order, each in its own transaction; stop at the first failure."""
    results: list[FileResult] = []
    for path in files:
        sql = path.read_text(encoding="utf-8")
        try:
            db.execute(sql)
        except psycopg.Error as error:
            db.rollback()
            first_line = (
                str(error).strip().splitlines()[0] if str(error).strip() else type(error).__name__
            )
            results.append(FileResult(path, False, first_line))
            break
        results.append(FileResult(path, True, "committed"))
    return results


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        url = check_url(os.environ.get(URL_VARIABLE))
        missing = [str(f) for f in args.files if not f.is_file()]
        if missing:
            raise LoadError("Not found: " + ", ".join(missing))
        with psycopg.connect(url, autocommit=True) as db:
            results = run_files(db, args.files)
    except (LoadError, psycopg.OperationalError) as error:
        print(f"Not loaded: {error}", file=sys.stderr)
        return 2
    for r in results:
        print(f"{'OK  ' if r.ok else 'FAIL'} {r.path.name}: {r.message}")
    not_run = len(args.files) - len(results)
    if not_run:
        print(f"Stopped: {not_run} file(s) not run. Tell Claude the FAIL line.")
    return 0 if all(r.ok for r in results) and not not_run else 1


if __name__ == "__main__":
    sys.exit(main())
