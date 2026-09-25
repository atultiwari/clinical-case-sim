"""Split a catalogue load document into parts small enough for one MCP call each.

Every part is marked "partial", so casevault.load_catalogue deactivates nothing
while the parts load (see migration casevault_load_template_status). Parts come
in dependency order: components, then value rules, then items with the rows
that hang off them (a test's definition and component list, a template, a
diagnosis's codes). Load them in the order written.
"""

import json
from collections.abc import Iterator
from typing import Any

Doc = dict[str, Any]
SECTIONS = ("items", "components", "tests", "normal_templates", "diagnoses", "value_rules")
PART_OVERHEAD = 200  # the version, the partial flag and the section keys


def dumps(document: Doc) -> str:
    """Compact JSON, as sent to the MCP."""
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"))


def _units(doc: Doc) -> Iterator[Doc]:
    """The smallest loadable pieces, in dependency order."""
    for component in doc["components"]:
        yield {"components": [component]}
    if doc["value_rules"]:
        # One unit: the loader replaces all value rules whenever a part carries any.
        yield {"value_rules": list(doc["value_rules"])}
    tests = {t["item_id"]: t for t in doc["tests"]}
    templates = {t["item_id"]: t for t in doc["normal_templates"]}
    diagnoses = {d["item_id"]: d for d in doc["diagnoses"]}
    for item in doc["items"]:
        unit: Doc = {"items": [item]}
        for key, rows in (
            ("tests", tests),
            ("normal_templates", templates),
            ("diagnoses", diagnoses),
        ):
            if item["id"] in rows:
                unit[key] = [rows[item["id"]]]
        yield unit


def _unit_size(unit: Doc) -> int:
    return sum(len(dumps(row).encode("utf-8")) + 1 for rows in unit.values() for row in rows)


def _part(version: int, units: list[Doc]) -> Doc:
    part: Doc = {"version": version, "partial": True}
    for key in SECTIONS:
        rows = [row for unit in units for row in unit.get(key, [])]
        if rows:
            part[key] = rows
    return part


def split_document(doc: Doc, max_bytes: int) -> list[Doc]:
    """Parts of at most max_bytes of compact JSON each, every row exactly once."""
    parts: list[Doc] = []
    current: list[Doc] = []
    size = PART_OVERHEAD
    for unit in _units(doc):
        unit_size = _unit_size(unit)
        if unit_size + PART_OVERHEAD > max_bytes:
            raise ValueError(f"One catalogue row needs {unit_size} bytes, more than {max_bytes}.")
        if current and size + unit_size > max_bytes:
            parts.append(_part(doc["version"], current))
            current, size = [], PART_OVERHEAD
        current.append(unit)
        size += unit_size
    if current:
        parts.append(_part(doc["version"], current))
    for part in parts:
        if len(dumps(part).encode("utf-8")) > max_bytes:
            raise ValueError(f"A part came out larger than {max_bytes} bytes.")
    return parts
