"""Read, check and build the catalogue from the CSV files in catalogue/ (SPEC §5, PLAN L0.4).

    uv run python -m scripts.catalogue check
    uv run python -m scripts.catalogue build --version 0

`build` writes the load document, build/catalogue.v<version>.json, which Claude
loads through the Supabase MCP with casevault.load_catalogue. The CSV files are
the source; the database is never edited directly (CLAUDE.md). The file formats
are in catalogue/README.md.
"""

import argparse
import csv
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.catalogue_checks import check

__all__ = ["FILES", "Catalogue", "CatalogueError", "build_document", "check", "read_catalogue"]

CASE_LIBRARY = Path(__file__).resolve().parents[1]
DEFAULT_DIR = CASE_LIBRARY / "catalogue"
DEFAULT_OUT_DIR = CASE_LIBRARY / "build"

ITEM_COLUMNS = ("id", "name", "category", "synonyms", "specialty_scope")
FILES: Mapping[str, tuple[str, ...]] = {
    "history.csv": ITEM_COLUMNS,
    "exam.csv": ITEM_COLUMNS,
    "tests.csv": (
        *ITEM_COLUMNS,
        "route",
        "specimen",
        "price_inr",
        "price_source",
        "tat_minutes",
        "invasive",
        "loinc",
        "components",
    ),
    "components.csv": (
        "id",
        "name",
        "loinc",
        "unit_si",
        "unit_conv",
        "conv_factor",
        "decimals",
        "normal_text",
    ),
    "component_ranges.csv": (
        "component_id",
        "sex",
        "age_min",
        "age_max",
        "low",
        "high",
        "text",
        "display",
        "source",
    ),
    "actions.csv": ITEM_COLUMNS,
    "referrals.csv": ITEM_COLUMNS,
    "diagnoses.csv": (*ITEM_COLUMNS, "icd11", "icd10", "codes_verified"),
    "findings.csv": (*ITEM_COLUMNS, "shown_by"),
    "normal_templates.csv": ("item_id", "template", "review_status"),
    "value_rules.csv": ("id", "kind", "target", "inputs", "factor", "tolerance_pct", "formula"),
}
# The catalogue_item kind of each item file.
ITEM_FILES: Mapping[str, str] = {
    "history.csv": "history",
    "exam.csv": "exam",
    "tests.csv": "test",
    "actions.csv": "action",
    "referrals.csv": "referral",
    "diagnoses.csv": "diagnosis",
    "findings.csv": "finding",
}

Row = Mapping[str, str]


class CatalogueError(ValueError):
    """A catalogue file is missing or unreadable. The message names the file."""


@dataclass(frozen=True)
class Catalogue:
    """Every CSV file's rows, keyed by file name, with cells stripped."""

    files: Mapping[str, tuple[Row, ...]]

    def rows(self, file: str) -> tuple[Row, ...]:
        return self.files[file]

    def items(self) -> tuple[tuple[str, Row], ...]:
        """(kind, row) for every catalogue item, in file order."""
        return tuple((kind, row) for file, kind in ITEM_FILES.items() for row in self.rows(file))


def split_list(cell: str) -> list[str]:
    return [part.strip() for part in cell.split("|") if part.strip()]


def read_catalogue(directory: Path) -> Catalogue:
    """Read every file in FILES, checking that each exists and has exactly its header."""
    return Catalogue({name: _read_file(directory / name, header) for name, header in FILES.items()})


def _read_file(path: Path, header: tuple[str, ...]) -> tuple[Row, ...]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != header:
                raise CatalogueError(
                    f"{path.name}: the header must be exactly {','.join(header)}; "
                    f"found {','.join(reader.fieldnames or ())}."
                )
            return tuple({k: (v or "").strip() for k, v in row.items()} for row in reader)
    except FileNotFoundError as err:
        raise CatalogueError(f"{path.name} is missing from {path.parent}.") from err


def _num(cell: str) -> int | float | None:
    if not cell:
        return None
    value = float(cell)
    return int(value) if value.is_integer() and "." not in cell else value


def _text(cell: str) -> str | None:
    return cell or None


def _range(row: Row) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "sex": row["sex"],
        "age_min": _num(row["age_min"]),
        "age_max": _num(row["age_max"]),
        "low": _num(row["low"]),
        "high": _num(row["high"]),
        "text": _text(row["text"]),
        "display": _text(row["display"]),
        "source": row["source"],
    }
    return {k: v for k, v in fields.items() if v is not None}


def _item(kind: str, row: Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "kind": kind,
        "name": row["name"],
        "category": row["category"],
        "synonyms": split_list(row["synonyms"]),
        "specialty_scope": split_list(row["specialty_scope"]),
    }


def build_document(catalogue: Catalogue, version: int) -> dict[str, Any]:
    """The JSON document casevault.load_catalogue takes, sorted so builds are reproducible."""
    ranges: dict[str, list[dict[str, Any]]] = {}
    for row in catalogue.rows("component_ranges.csv"):
        ranges.setdefault(row["component_id"], []).append(_range(row))

    items = sorted((_item(kind, r) for kind, r in catalogue.items()), key=lambda i: str(i["id"]))
    tests = [
        {
            "item_id": r["id"],
            "route": r["route"],
            "specimen": _text(r["specimen"]),
            "price_inr": _num(r["price_inr"]),
            "price_source": r["price_source"],
            "tat_minutes": _num(r["tat_minutes"]),
            "invasive": r["invasive"] == "true",
            "loinc": _text(r["loinc"]),
            "components": split_list(r["components"]),
        }
        for r in catalogue.rows("tests.csv")
    ]
    components = [
        {
            "id": r["id"],
            "name": r["name"],
            "loinc": _text(r["loinc"]),
            "unit_si": _text(r["unit_si"]),
            "unit_conv": _text(r["unit_conv"]),
            "conv_factor": _num(r["conv_factor"]),
            "decimals": _num(r["decimals"]),
            "ref_ranges": ranges.get(r["id"], []),
            "normal_text": _text(r["normal_text"]),
        }
        for r in catalogue.rows("components.csv")
    ]
    return {
        "version": version,
        "items": items,
        "tests": sorted(tests, key=lambda t: t["item_id"]),
        "components": sorted(components, key=lambda c: c["id"]),
        "normal_templates": sorted(
            (
                {
                    "item_id": r["item_id"],
                    "template": r["template"],
                    "review_status": r["review_status"],
                }
                for r in catalogue.rows("normal_templates.csv")
            ),
            key=lambda t: t["item_id"],
        ),
        "diagnoses": sorted(
            (
                {"item_id": r["id"], "icd11": _text(r["icd11"]), "icd10": _text(r["icd10"])}
                for r in catalogue.rows("diagnoses.csv")
            ),
            key=lambda d: d["item_id"],
        ),
        "value_rules": sorted(
            (
                {
                    "id": r["id"],
                    "kind": r["kind"],
                    "target": r["target"],
                    "inputs": split_list(r["inputs"]),
                    "factor": _num(r["factor"]) or 1,
                    "tolerance_pct": _num(r["tolerance_pct"]) or 2,
                    "formula": r["formula"],
                }
                for r in catalogue.rows("value_rules.csv")
            ),
            key=lambda v: v["id"],
        ),
    }


def _summary(catalogue: Catalogue) -> str:
    counts = [f"{kind} {len(catalogue.rows(file))}" for file, kind in ITEM_FILES.items()]
    counts.append(f"component {len(catalogue.rows('components.csv'))}")
    return ", ".join(counts)


def _load_checked(directory: Path) -> Catalogue | None:
    try:
        catalogue = read_catalogue(directory)
    except CatalogueError as err:
        print(err, file=sys.stderr)
        return None
    problems = check(catalogue)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        print(f"{len(problems)} problem(s).", file=sys.stderr)
        return None
    return catalogue


def _write_parts(document: dict[str, Any], out: Path, max_bytes: int) -> None:
    from scripts.catalogue_parts import dumps, split_document

    pieces = split_document(document, max_bytes)
    for number, piece in enumerate(pieces, start=1):
        path = out.with_name(f"{out.stem}.part{number:02d}.json")
        path.write_text(dumps(piece) + "\n", encoding="utf-8")
    print(f"Wrote {len(pieces)} parts beside it; load them in order.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "build"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    build = sub.choices["build"]
    build.add_argument("--version", type=int, required=True)
    build.add_argument("--out", type=Path)
    build.add_argument(
        "--max-bytes", type=int, help="also write <out>.part<n>.json parts of at most this size"
    )
    args = parser.parse_args(argv)

    catalogue = _load_checked(args.dir)
    if catalogue is None:
        return 1
    print(f"Catalogue is clean: {_summary(catalogue)}.")
    if args.command == "build":
        out = args.out or DEFAULT_OUT_DIR / f"catalogue.v{args.version}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        document = build_document(catalogue, args.version)
        out.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"Wrote {out}.")
        if args.max_bytes:
            _write_parts(document, out, args.max_bytes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
