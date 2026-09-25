"""Write a case bundle to exports/ (SPEC §7.5, PLAN L0.3).

    uv run --env-file .env python -m scripts.export_bundle PMC12949993@v1 --catalogue-version 1

casevault.export_bundle assembles the bundle and refuses until the version is
frozen, fully covered, reviewed and clean. This script writes the file once,
with the RFC 8785 serializer, and the SHA-256 of its bytes beside it as
<bundle id>.json.sha256. It only reads the Case Vault: Claude records the hash
in casevault.bundle through the MCP.
"""

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg

from scripts.config import ConfigError, load_settings, require_db_url
from scripts.jcs import canonicalize

DEFAULT_OUT_DIR = Path(__file__).resolve().parents[1] / "exports"
EXPORT_QUERY = "select casevault.export_bundle(%s, %s, %s)"


class ExportError(RuntimeError):
    """The bundle cannot be exported. The message says why."""


@dataclass(frozen=True)
class ExportResult:
    bundle_id: str
    path: Path
    sha256: str
    written: bool  # False when an identical file was already there


def export_bundle(
    conn: psycopg.Connection[Any],
    case_version_id: str,
    revision: int,
    catalogue_version: int,
    out_dir: Path,
) -> ExportResult:
    """Fetch the bundle, write it canonically once, and save its SHA-256 beside it."""
    body = _fetch(conn, case_version_id, revision, catalogue_version)
    data = canonicalize(body)
    bundle_id = str(body["bundle_id"])
    path = out_dir / f"{bundle_id}.json"
    sha256 = hashlib.sha256(data).hexdigest()

    if path.exists():
        if path.read_bytes() != data:
            raise ExportError(
                f"{path.name} already exists with different content. A bundle is written once; "
                "export a new revision instead."
            )
        return ExportResult(bundle_id, path, sha256, written=False)

    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.with_name(f"{path.name}.sha256").write_text(f"{sha256}  {path.name}\n", encoding="utf-8")
    return ExportResult(bundle_id, path, sha256, written=True)


def _fetch(
    conn: psycopg.Connection[Any], case_version_id: str, revision: int, catalogue_version: int
) -> dict[str, Any]:
    try:
        row = conn.execute(EXPORT_QUERY, (case_version_id, revision, catalogue_version)).fetchone()
    except psycopg.errors.ObjectNotInPrerequisiteState as exc:
        detail = exc.diag.message_detail or ""
        raise ExportError(f"{exc.diag.message_primary}\n{detail}".strip()) from exc
    if row is None or not isinstance(row[0], dict):
        raise ExportError(f"The Case Vault returned no bundle for {case_version_id}.")
    return row[0]


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a frozen case version as a bundle.")
    parser.add_argument("case_version_id", help="for example PMC12949993@v1")
    parser.add_argument("--revision", type=int, default=1, help="bundle revision (default 1)")
    parser.add_argument("--catalogue-version", type=int, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="output folder")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        url = require_db_url(load_settings())
        with psycopg.connect(url) as conn:
            conn.read_only = True
            result = export_bundle(
                conn, args.case_version_id, args.revision, args.catalogue_version, args.out
            )
    except (ConfigError, ExportError) as exc:
        print(f"Not exported: {exc}", file=sys.stderr)
        return 1
    except psycopg.Error as exc:
        print(f"Not exported: the Case Vault query failed ({exc.sqlstate}).", file=sys.stderr)
        return 1

    state = "Wrote" if result.written else "Already there, identical:"
    print(f"{state} {result.path}\nSHA-256 {result.sha256}")
    print("Next: record the hash in casevault.bundle through the MCP.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
