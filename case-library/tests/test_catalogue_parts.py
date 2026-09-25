"""scripts/catalogue_parts.py: splitting the load document into MCP-sized parts."""

import json
from pathlib import Path
from typing import Any

import pytest

from scripts import catalogue as cat
from scripts import catalogue_parts as parts

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "catalogue"
REAL = Path(__file__).resolve().parents[1] / "catalogue"


def _doc(path: Path = FIXTURE) -> dict[str, Any]:
    return cat.build_document(cat.read_catalogue(path), version=0)


def _size(part: dict[str, Any]) -> int:
    return len(parts.dumps(part).encode("utf-8"))


def test_every_part_is_partial_and_small_enough() -> None:
    doc = _doc(REAL)
    pieces = parts.split_document(doc, max_bytes=60_000)
    assert len(pieces) > 1
    assert all(p["partial"] is True and p["version"] == 0 for p in pieces)
    assert all(_size(p) <= 60_000 for p in pieces)


def test_the_parts_together_hold_every_row_once() -> None:
    doc = _doc(REAL)
    pieces = parts.split_document(doc, max_bytes=60_000)
    for key in ("items", "components", "tests", "normal_templates", "diagnoses", "value_rules"):
        joined = [row for p in pieces for row in p.get(key, [])]
        assert sorted(json.dumps(r, sort_keys=True) for r in joined) == sorted(
            json.dumps(r, sort_keys=True) for r in doc[key]
        ), key


def test_dependencies_load_first() -> None:
    doc = _doc(REAL)
    pieces = parts.split_document(doc, max_bytes=60_000)
    seen_items: set[str] = set()
    seen_components: set[str] = set()
    for piece in pieces:
        seen_items |= {i["id"] for i in piece.get("items", [])}
        seen_components |= {c["id"] for c in piece.get("components", [])}
        for test in piece.get("tests", []):
            assert test["item_id"] in seen_items
            assert set(test["components"]) <= seen_components
        for row in piece.get("normal_templates", []) + piece.get("diagnoses", []):
            assert row["item_id"] in seen_items
        for rule in piece.get("value_rules", []):
            assert {rule["target"], *rule["inputs"]} <= seen_components


def test_all_value_rules_travel_in_one_part() -> None:
    pieces = parts.split_document(_doc(REAL), max_bytes=60_000)
    assert sum(1 for p in pieces if "value_rules" in p) == 1


def test_a_small_document_is_one_part() -> None:
    pieces = parts.split_document(_doc(), max_bytes=1_000_000)
    assert len(pieces) == 1


def test_a_row_too_large_for_any_part_is_refused() -> None:
    with pytest.raises(ValueError, match="bytes"):
        parts.split_document(_doc(), max_bytes=200)


def test_cli_writes_numbered_parts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "doc.json"
    args = [
        "build",
        "--dir",
        str(REAL),
        "--version",
        "0",
        "--out",
        str(out),
        "--max-bytes",
        "60000",
    ]
    assert cat.main(args) == 0
    written = sorted(tmp_path.glob("doc.part*.json"))
    assert len(written) > 1
    assert "parts" in capsys.readouterr().out
    assert json.loads(written[0].read_text(encoding="utf-8"))["partial"] is True
