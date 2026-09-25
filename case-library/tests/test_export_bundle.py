"""scripts/export_bundle.py without a database (a fake connection)."""

import hashlib
import json
from pathlib import Path
from typing import Any

import psycopg
import pytest

from scripts import export_bundle as eb

BODY = {"bundle_id": "PMC0000001@v1.r1", "schema_version": "0.3", "facts": [{"value_num": 72.0}]}
CANONICAL = b'{"bundle_id":"PMC0000001@v1.r1","facts":[{"value_num":72}],"schema_version":"0.3"}'


class FakeCursor:
    def __init__(self, row: Any) -> None:
        self._row = row

    def fetchone(self) -> Any:
        return self._row


class FakeConnection:
    def __init__(self, row: Any = (BODY,), error: Exception | None = None) -> None:
        self.row = row
        self.error = error
        self.read_only = False
        self.queries: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, query: str, params: tuple[Any, ...]) -> FakeCursor:
        self.queries.append((query, params))
        if self.error is not None:
            raise self.error
        return FakeCursor(self.row)

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _export(conn: FakeConnection, out: Path) -> eb.ExportResult:
    return eb.export_bundle(conn, "PMC0000001@v1", 1, 0, out)  # type: ignore[arg-type]


def test_writes_canonical_bytes_and_their_hash(tmp_path: Path) -> None:
    result = _export(FakeConnection(), tmp_path)

    assert result.written
    assert result.path.read_bytes() == CANONICAL
    assert result.sha256 == hashlib.sha256(CANONICAL).hexdigest()
    sidecar = tmp_path / "PMC0000001@v1.r1.json.sha256"
    assert sidecar.read_text() == f"{result.sha256}  PMC0000001@v1.r1.json\n"


def test_identical_export_is_left_alone(tmp_path: Path) -> None:
    _export(FakeConnection(), tmp_path)

    again = _export(FakeConnection(), tmp_path)

    assert not again.written


def test_a_different_bundle_is_never_written_over(tmp_path: Path) -> None:
    _export(FakeConnection(), tmp_path)
    changed = {**BODY, "facts": []}

    with pytest.raises(eb.ExportError, match="written once"):
        _export(FakeConnection(row=(changed,)), tmp_path)
    assert (tmp_path / "PMC0000001@v1.r1.json").read_bytes() == CANONICAL


def test_no_bundle_returned(tmp_path: Path) -> None:
    with pytest.raises(eb.ExportError, match="no bundle"):
        _export(FakeConnection(row=None), tmp_path)


def test_main_exports_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    conn = FakeConnection()
    monkeypatch.setenv("CASE_VAULT_DB_URL_READONLY", "postgresql://reader@localhost/db")
    monkeypatch.setattr(psycopg, "connect", lambda url: conn)

    code = eb.main(["PMC0000001@v1", "--catalogue-version", "0", "--out", str(tmp_path)])

    assert code == 0
    assert conn.read_only
    assert conn.queries == [(eb.EXPORT_QUERY, ("PMC0000001@v1", 1, 0))]
    assert "SHA-256" in capsys.readouterr().out
    assert json.loads((tmp_path / "PMC0000001@v1.r1.json").read_bytes()) == {
        **BODY,
        "facts": [{"value_num": 72}],
    }


def test_main_explains_a_missing_setting(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("CASE_VAULT_DB_URL_READONLY", raising=False)

    assert eb.main(["PMC0000001@v1", "--catalogue-version", "0"]) == 1
    assert "CASE_VAULT_DB_URL_READONLY is not set" in capsys.readouterr().err


def test_main_reports_a_failed_query(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    conn = FakeConnection(error=psycopg.errors.UndefinedFunction())
    monkeypatch.setenv("CASE_VAULT_DB_URL_READONLY", "postgresql://reader@localhost/db")
    monkeypatch.setattr(psycopg, "connect", lambda url: conn)

    assert eb.main(["PMC0000001@v1", "--catalogue-version", "0"]) == 1
    assert "query failed" in capsys.readouterr().err
