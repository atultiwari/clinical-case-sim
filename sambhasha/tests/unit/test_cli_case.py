"""P0.6: `sambhasha case import` and `sambhasha case list`."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sambhasha import cli
from sambhasha.storage.memory import InMemoryRepository

PILOT_R1 = (
    Path(__file__).resolve().parents[3] / "case-library" / "exports" / "PMC12949993@v1.r1.json"
)
runner = CliRunner()


@pytest.fixture
def repo(monkeypatch: pytest.MonkeyPatch) -> InMemoryRepository:
    shared = InMemoryRepository()
    seen: list[str] = []

    @contextmanager
    def fake_open(url: str) -> Iterator[InMemoryRepository]:
        seen.append(url)
        yield shared

    monkeypatch.setattr(cli, "open_repository", fake_open)
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://example/db")
    return shared


def test_import_reports_the_bundle_and_its_rows(repo: InMemoryRepository) -> None:
    result = runner.invoke(cli.app, ["case", "import", str(PILOT_R1)])

    assert result.exit_code == 0, result.output
    assert "Imported PMC12949993@v1.r1" in result.output
    assert "191 facts" in result.output
    assert "no leaks" in result.output
    assert "not eligible for primary results" in result.output
    assert [r.bundle_id for r in repo.list_bundles()] == ["PMC12949993@v1.r1"]


def test_a_refused_import_exits_with_its_reason(repo: InMemoryRepository) -> None:
    runner.invoke(cli.app, ["case", "import", str(PILOT_R1)])

    result = runner.invoke(cli.app, ["case", "import", str(PILOT_R1)])

    assert result.exit_code == 1
    assert "already imported" in result.output


def test_list_shows_each_bundle_with_its_eligibility(repo: InMemoryRepository) -> None:
    runner.invoke(cli.app, ["case", "import", str(PILOT_R1)])

    result = runner.invoke(cli.app, ["case", "list"])

    assert result.exit_code == 0
    assert "PMC12949993@v1.r1" in result.output
    assert "not primary" in result.output


def test_list_says_when_nothing_is_imported(repo: InMemoryRepository) -> None:
    result = runner.invoke(cli.app, ["case", "list"])

    assert "No bundles imported yet." in result.output


def test_tables_generate_rewrites_the_committed_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    written: list[str] = []

    def fake_write(tables: object) -> tuple[Path, Path]:
        written.append("both")
        return Path("p.yaml"), Path("t.yaml")

    monkeypatch.setattr(cli, "write_tables", fake_write)

    result = runner.invoke(cli.app, ["tables", "generate"])

    assert result.exit_code == 0, result.output
    assert written == ["both"]
    assert "Wrote p.yaml and t.yaml." in result.output
