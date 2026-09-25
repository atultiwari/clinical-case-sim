"""Build and read the case review pack, an Excel workbook for Atul (SPEC §7.2-§7.3, PLAN L0.6).

    uv run --env-file .env python -m scripts.review_pack build pilot --cases PMC12949993@v1
    uv run python -m scripts.review_pack read review/pilot.xlsx

(`uv run python scripts/review_pack.py ...` works too.) `build` reads the Case
Vault through the read-only URL with SELECTs only and writes review/<batch>.xlsx
(git-ignored: it shows diagnoses). `read` checks the returned workbook, prints a
summary per case and writes <pack>.decisions.json beside it; it never writes to
the Case Vault. Claude applies the decisions through the MCP after Atul's go-ahead.
"""

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in {None, ""}:  # run as a file: make `scripts` importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REVIEW_DIR = Path(__file__).resolve().parents[1] / "review"
BATCH_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def default_out(batch: str) -> Path:
    return REVIEW_DIR / f"{batch}.xlsx"


def run_build(batch: str, case_version_ids: Sequence[str], out: Path | None) -> int:
    import psycopg

    from scripts.config import ConfigError, load_settings, require_db_url
    from scripts.review_pack_data import ReviewPackError, fetch_pack_data
    from scripts.review_pack_write import write_pack

    if not BATCH_NAME.match(batch):
        print(f"Not built: the batch name {batch!r} must be letters, digits, '.', '_' or '-'.",
              file=sys.stderr)  # fmt: skip
        return 1
    target = out or default_out(batch)
    try:
        url = require_db_url(load_settings())
        with psycopg.connect(url) as conn:
            conn.read_only = True
            data = fetch_pack_data(conn, case_version_ids, batch=batch)
    except (ConfigError, ReviewPackError) as exc:
        print(f"Not built: {exc}", file=sys.stderr)
        return 1
    except psycopg.Error as exc:
        print(f"Not built: the Case Vault query failed ({exc.sqlstate}).", file=sys.stderr)
        return 1
    counts = write_pack(data, target)
    print(f"Wrote {target}: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + ".")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or read a case review pack.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="write review/<batch>.xlsx from the Case Vault")
    build.add_argument("batch", help="batch name, for example pilot")
    build.add_argument("--cases", nargs="+", required=True, metavar="CASE_VERSION_ID")
    build.add_argument("--out", type=Path, help="output file (default review/<batch>.xlsx)")
    read = sub.add_parser("read", help="check a returned pack and write its decisions JSON")
    read.add_argument("workbook", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "read":
        from scripts.review_pack_read import run_read

        return run_read(args.workbook)
    return run_build(args.batch, args.cases, args.out)


if __name__ == "__main__":
    sys.exit(main())
