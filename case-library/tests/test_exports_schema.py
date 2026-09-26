"""Every case's newest exported bundle meets the bundle schema in full (PLAN L1.7).

Older revisions stay in exports/ as they were written (a bundle is never rewritten), so only
the newest revision of each case is checked; engines load the newest.
"""

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
SCHEMA = ROOT / "schemas" / "case-bundle.v0.3.schema.json"
BUNDLE_NAME = re.compile(r"(?P<case>.+)@v(?P<version>[0-9]+)\.r(?P<revision>[0-9]+)\.json")


def newest_revisions(paths: list[Path]) -> list[Path]:
    """The newest bundle file of each case, by version and then revision."""
    newest: dict[str, tuple[tuple[int, int], Path]] = {}
    for path in paths:
        match = BUNDLE_NAME.fullmatch(path.name)
        assert match, f"unexpected file name in exports/: {path.name}"
        rank = (int(match["version"]), int(match["revision"]))
        if match["case"] not in newest or rank > newest[match["case"]][0]:
            newest[match["case"]] = (rank, path)
    return sorted(path for _, path in newest.values())


NEWEST = newest_revisions(sorted(EXPORTS.glob("*.json")))
_SCHEMA = json.loads(SCHEMA.read_text(encoding="utf-8"))
VALIDATOR = jsonschema.Draft202012Validator(_SCHEMA)
# The schema leaves ground_truth.rubric open, but its anchors use the same conditions.
CONDITION = jsonschema.Draft202012Validator(
    {"$defs": _SCHEMA["$defs"], "$ref": "#/$defs/condition"}
)


def _rubric_errors(bundle: dict[str, Any]) -> list[str]:
    rubric = bundle["ground_truth"].get("rubric") or {}
    return [
        f"ground_truth/rubric/rubric/{i}/if/{'/'.join(map(str, e.absolute_path))}: {e.message}"
        for i, anchor in enumerate(rubric.get("rubric", []))
        for e in CONDITION.iter_errors(anchor.get("if"))
    ]


def test_newest_revisions_pick_the_highest_version_and_revision() -> None:
    names = ["A@v1.r1.json", "A@v1.r3.json", "A@v2.r1.json", "B@v1.r2.json"]

    assert [p.name for p in newest_revisions([Path(n) for n in names])] == [
        "A@v2.r1.json",
        "B@v1.r2.json",
    ]


def test_there_are_exports_to_check() -> None:
    assert NEWEST


@pytest.mark.parametrize("path", NEWEST, ids=lambda p: p.name)
def test_the_newest_bundle_of_each_case_meets_the_schema(path: Path) -> None:
    bundle = json.loads(path.read_bytes())

    errors = [
        f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in VALIDATOR.iter_errors(bundle)
    ] + _rubric_errors(bundle)

    assert not errors, "\n".join(errors[:20])
