"""Bundle export end to end on the fixture case (SPEC §7.5, §10.5; PLAN L0.3)."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psycopg
import psycopg.sql
import pytest

from scripts.export_bundle import ExportError, export_bundle
from tests.integration.conftest import MINI_GENERATOR, add_affected_cbc, seed_mini_case

pytestmark = pytest.mark.integration

SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "case-bundle.v0.3.schema.json"


def _prepare(
    db: psycopg.Connection, before_freeze: Callable[[psycopg.Connection, str], None] | None = None
) -> str:
    """Curate the fixture to completion: resolve, author, review and freeze."""
    cv = seed_mini_case(db)
    db.execute("select casevault.compute_derived(%s, %s, 'v0.0')", (cv, MINI_GENERATOR))
    add_affected_cbc(db, cv)
    db.execute("select casevault.resolve_normals(%s)", (cv,))
    db.execute(
        "insert into casevault.report (case_version_id, id, test_item_id, variant, status,"
        " findings, report_text, generator, skill_version) values"
        " (%s, 'RP01', 'LAB.FILM', 'only', 'final', '{FND.STIPPLING}', 'Coarse stippling.',"
        " 'g', 's')",
        (cv,),
    )
    db.execute(
        "insert into casevault.consult_note (case_version_id, id, specialty, note_text, origin,"
        " rationale, confidence, generator, skill_version) values"
        " (%s, 'CN01', 'REF.TOXICOLOGY', 'Happy to see her.', 'affected', 'r', 0.8, 'g', 's')",
        (cv,),
    )
    for table, status in (("fact", "verified"), ("synthetic_ledger", "approved"),
                          ("report", "approved"), ("consult_note", "approved")):  # fmt: skip
        db.execute(
            psycopg.sql.SQL(
                "update casevault.{} set review_status = %s, reviewed_by = 'reviewer',"
                " reviewed_at = '2026-09-25T12:00:00Z' where case_version_id = %s"
            ).format(psycopg.sql.Identifier(table)),
            (status, cv),
        )
    if before_freeze is not None:
        before_freeze(db, cv)
    db.execute(
        "update casevault.case_version set status = 'frozen', frozen_at = now() where id = %s",
        (cv,),
    )
    return cv


def _blockers(db: psycopg.Connection, cv: str) -> list[str]:
    return [r[0] for r in db.execute("select casevault.export_blockers(%s)", (cv,)).fetchall()]


def test_exporting_twice_gives_byte_identical_files(db: psycopg.Connection, tmp_path: Path) -> None:
    cv = _prepare(db)

    first = export_bundle(db, cv, 1, 0, tmp_path / "a")
    second = export_bundle(db, cv, 1, 0, tmp_path / "b")

    assert first.path.read_bytes() == second.path.read_bytes()
    assert first.sha256 == second.sha256
    assert first.bundle_id == "PMC0000001@v1.r1"


def test_bundle_holds_reviewed_rows_without_provenance(
    db: psycopg.Connection, tmp_path: Path
) -> None:
    cv = _prepare(db)
    bundle = json.loads(export_bundle(db, cv, 1, 0, tmp_path).path.read_bytes())

    assert len(bundle["facts"]) == 7  # 6 article (2 history, 2 Hb, RBC, lead) + derived MCH
    assert {f["origin"] for f in bundle["facts"]} == {"article", "derived"}
    assert all("generator" not in row and "review_status" not in row for row in bundle["ledger"])
    assert bundle["source"]["production_ok"] is True
    assert bundle["ground_truth"]["final_dx"]["id"] == "DX.LEAD_POISONING"


def test_bundle_meets_the_schema_required_fields(db: psycopg.Connection, tmp_path: Path) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    cv = _prepare(db)
    bundle = json.loads(export_bundle(db, cv, 1, 0, tmp_path).path.read_bytes())

    assert set(schema["required"]) <= set(bundle)
    item_defs = {
        key: prop["items"]["$ref"].rsplit("/", 1)[-1]
        for key, prop in schema["properties"].items()
        if prop.get("type") == "array" and "$ref" in prop.get("items", {})
    }
    for key, definition in item_defs.items():
        required = set(schema["$defs"][definition]["required"])
        for row in bundle[key]:
            assert required <= set(row), (key, row)


def test_draft_versions_cannot_be_exported(db: psycopg.Connection, tmp_path: Path) -> None:
    cv = seed_mini_case(db)

    assert any("not frozen" in b for b in _blockers(db, cv))
    assert any(b.startswith("coverage:") for b in _blockers(db, cv))
    with pytest.raises(ExportError, match="cannot be exported yet"), db.transaction():
        export_bundle(db, cv, 1, 0, tmp_path)
    assert not list(tmp_path.iterdir())


def test_pending_rows_block_export(db: psycopg.Connection) -> None:
    cv = _prepare(db)
    db.execute(
        "insert into casevault.synthetic_ledger (case_version_id, target, day_bucket, tier, value,"
        " generator, skill_version) values (%s, 'HX.EXTRA', null, 'normal', '{}', 'g', 's')",
        (cv,),
    )

    assert _blockers(db, cv) == ["synthetic_ledger: 1 rows still pending review"]


def test_revision_must_be_positive(db: psycopg.Connection) -> None:
    cv = _prepare(db)
    call: Any = "select casevault.export_bundle(%s, 0, 0)"

    with pytest.raises(psycopg.errors.InvalidParameterValue), db.transaction():
        db.execute(call, (cv,))
