"""P1.9: `sambhasha run` and `sambhasha transcript`, offline with the fake model."""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

import pytest
from typer.testing import CliRunner

from sambhasha import cli
from sambhasha.domain.case_file import parse_bundle
from sambhasha.engine.config import DEFAULT_RUN_CONFIG
from sambhasha.storage.memory import InMemoryRepository

EXPORTS = Path(__file__).resolve().parents[3] / "case-library" / "exports"
PILOT = parse_bundle((EXPORTS / "PMC12949993@v1.r3.json").read_bytes())
runner = CliRunner()


@pytest.fixture
def repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> InMemoryRepository:
    shared = InMemoryRepository()
    shared.add_bundle(PILOT, "0" * 64)

    @contextmanager
    def fake_open(url: str) -> Iterator[InMemoryRepository]:
        yield shared

    monkeypatch.setattr(cli, "open_repository", fake_open)
    monkeypatch.setattr(cli, "MISSING_DIR", tmp_path / "missing")
    return shared


def _run_id(output: str) -> str:
    match = re.search(r"Run ([0-9a-f-]{36})", output)
    assert match, output
    return match.group(1)


def test_a_fake_run_completes_offline(repo: InMemoryRepository) -> None:
    result = runner.invoke(cli.app, ["run", "--fake"])

    assert result.exit_code == 0, result.output
    assert ": completed" in result.output
    assert "Committed: Lead poisoning from a herbal supplement" in result.output
    assert "sambhasha transcript" in result.output


def test_a_fake_run_names_no_real_model(repo: InMemoryRepository) -> None:
    run_id = _run_id(runner.invoke(cli.app, ["run", "--fake"]).output)

    models = {e.model for e in repo.events(UUID(run_id)) if e.type == "llm_call"}
    assert models == {"fake/scripted"}


def test_the_transcript_shows_the_whole_run(repo: InMemoryRepository) -> None:
    run_id = _run_id(runner.invoke(cli.app, ["run", "--fake"]).output)

    result = runner.invoke(cli.app, ["transcript", run_id])

    assert result.exit_code == 0, result.output
    assert "[E0 · day 0 00:00 · gatekeeper · answer · article · to team]" in result.output
    assert "herbal supplement" in result.output
    assert "model fake/scripted" in result.output
    assert "· commit ·" in result.output


def test_the_transcript_exports_html(repo: InMemoryRepository, tmp_path: Path) -> None:
    run_id = _run_id(runner.invoke(cli.app, ["run", "--fake"]).output)
    out = tmp_path / "run.html"

    result = runner.invoke(cli.app, ["transcript", run_id, "--html", str(out)])

    assert result.exit_code == 0, result.output
    page = out.read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>")
    assert "<table>" in page
    assert "Do not publish it" in page


def test_a_live_run_refuses_to_start_without_a_budget_cap(
    repo: InMemoryRepository, tmp_path: Path
) -> None:
    uncapped = tmp_path / "run.yaml"
    uncapped.write_text(
        DEFAULT_RUN_CONFIG.read_text(encoding="utf-8").replace(
            "llm_budget_usd: 1.00", "llm_budget_usd: null"
        ),
        encoding="utf-8",
    )

    result = runner.invoke(cli.app, ["run", "--config", str(uncapped)])

    assert result.exit_code == 1
    assert "needs llm_budget_usd" in result.output
    assert repo.list_bundles()  # nothing else happened


def test_a_run_needs_its_bundle_imported(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = InMemoryRepository()

    @contextmanager
    def fake_open(url: str) -> Iterator[InMemoryRepository]:
        yield empty

    monkeypatch.setattr(cli, "open_repository", fake_open)

    result = runner.invoke(cli.app, ["run", "--fake"])

    assert result.exit_code == 1
    assert "sambhasha case import" in result.output


def test_a_config_without_a_fake_script_cannot_run_fake(
    repo: InMemoryRepository, tmp_path: Path
) -> None:
    config = tmp_path / "run.yaml"
    config.write_text(
        DEFAULT_RUN_CONFIG.read_text(encoding="utf-8").replace("fake_script: fake/pilot.yaml", ""),
        encoding="utf-8",
    )

    result = runner.invoke(cli.app, ["run", "--config", str(config), "--fake"])

    assert result.exit_code == 1
    assert "no fake_script" in result.output


def test_the_transcript_of_an_unknown_run_is_refused(repo: InMemoryRepository) -> None:
    result = runner.invoke(cli.app, ["transcript", "00000000-0000-4000-8000-000000000009"])

    assert result.exit_code == 1


def test_a_capped_live_run_is_wired_to_the_cap_and_the_cache(
    repo: InMemoryRepository, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sambhasha.llm.cache import RecordReplayCache
    from sambhasha.runner import fake_models_config

    config = tmp_path / "run.yaml"
    config.write_text(
        DEFAULT_RUN_CONFIG.read_text(encoding="utf-8").replace(
            "llm_budget_usd: 1.00", "llm_budget_usd: 1.50"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "load_models_config", fake_models_config)
    # A replay-only cache with nothing in it: the first model call stops the run, offline.
    monkeypatch.setattr(
        cli, "RecordReplayCache", lambda _dir: RecordReplayCache(tmp_path, replay_only=True)
    )

    result = runner.invoke(cli.app, ["run", "--config", str(config)])

    assert result.exit_code == 0, result.output
    assert ": aborted" in result.output
    assert "Stopped: CacheMiss" in result.output
    assert "Model calls cost USD 0 of the USD 1.5 cap." in result.output


# --- the free Gemini pilot (P1.11 preparation) ---


def _capped(tmp_path: Path) -> Path:
    config = tmp_path / "run.yaml"
    config.write_text(
        DEFAULT_RUN_CONFIG.read_text(encoding="utf-8").replace(
            "llm_budget_usd: 1.00", "llm_budget_usd: 1.50"
        ),
        encoding="utf-8",
    )
    return config


def test_a_live_run_without_the_api_key_is_refused_before_it_starts(
    repo: InMemoryRepository, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = runner.invoke(cli.app, ["run", "--config", str(_capped(tmp_path))])

    assert result.exit_code == 1
    assert "GEMINI_API_KEY" in result.output


def test_an_unknown_doctor_profile_is_refused(
    repo: InMemoryRepository, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    result = runner.invoke(
        cli.app, ["run", "--config", str(_capped(tmp_path)), "--doctor-profile", "doctor-z"]
    )

    assert result.exit_code == 1
    assert "doctor-z" in result.output


def test_the_wait_report_names_the_time_a_paid_tier_would_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    from sambhasha.llm.ratelimit import WaitLedger

    monkeypatch.setattr(cli, "RUNS_DIR", tmp_path / "runs")
    ledger = WaitLedger()
    ledger.add("gemini-3.8-flash", 125, "pacing")
    ledger.add("gemini-3.5-flash-lite", 20, "rate limited")
    run_id = UUID("00000000-0000-4000-8000-00000000000b")

    cli._report_waits(run_id, ledger)

    out = capsys.readouterr().out
    assert "Waited 2 min 25 s for the free tier's rate limits (2 pauses)" in out
    assert "A paid tier would have saved most of this time." in out
    stats = json.loads((tmp_path / "runs" / f"{run_id}.waits.json").read_text())
    assert stats["waited_seconds"] == 145.0
    assert stats["by_model"] == {"gemini-3.8-flash": 125.0, "gemini-3.5-flash-lite": 20.0}


def test_each_tagged_repeat_gets_its_own_cache() -> None:
    from sambhasha.llm.cache import DEFAULT_CACHE_DIR

    assert cli.cache_dir(None) == DEFAULT_CACHE_DIR
    assert cli.cache_dir("pilot-a-1") == DEFAULT_CACHE_DIR / "pilot-a-1"


def test_a_cache_tag_cannot_leave_the_cache_folder() -> None:
    from sambhasha.engine.config import RunConfigError

    with pytest.raises(RunConfigError, match="cache tag"):
        cli.cache_dir("../elsewhere")
