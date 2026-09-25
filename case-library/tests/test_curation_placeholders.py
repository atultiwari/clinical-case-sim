"""No reviewer placeholder survives in text a player can see (PLAN L0.10).

The pilot's marrow reports reached review with "[to be set by the reviewer]"
in their report text; the Case Vault's leak scan looks only for diagnosis
terms, so this checks every case's curation files directly.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest

CASES = Path(__file__).resolve().parents[1] / "cases"
PLACEHOLDER = re.compile(r"to be set|set by the reviewer|\bTBD\b|\bplaceholder\b", re.IGNORECASE)

# Fields a player can see, per curation file. Rationale and notes are reviewer-only.
VISIBLE: dict[str, tuple[str, ...]] = {
    "reports.json": ("report_text", "impression", "status_line", "findings"),
    "consult_notes.json": ("note_text", "recommendations"),
    "lay_text.json": ("lay_text",),
}


def _visible_texts(file: Path) -> list[str]:
    rows: list[dict[str, Any]] = json.loads(file.read_text(encoding="utf-8"))
    if file.name == "affected.json":
        # Reviewer rows are placeholders by design until the review fills them.
        return [
            json.dumps([r.get("value"), r.get("release_text"), r.get("lay_text")])
            for r in rows
            if r.get("tier") != "reviewer"
        ]
    fields = VISIBLE.get(file.name, ())
    return [json.dumps(r.get(f)) for r in rows for f in fields if r.get(f) is not None]


FILES = sorted(f for f in CASES.glob("*/curation/*.json") if f.name in (*VISIBLE, "affected.json"))


@pytest.mark.parametrize("file", FILES, ids=lambda f: f"{f.parent.parent.name}/{f.name}")
def test_no_placeholder_in_player_visible_text(file: Path) -> None:
    assert [t for t in _visible_texts(file) if PLACEHOLDER.search(t)] == []
