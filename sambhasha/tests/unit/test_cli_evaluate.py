"""P1.8: `sambhasha evaluate <run_id>` scores a stored run and saves the score."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

from sambhasha import cli
from sambhasha.llm.config import load_models_config
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway
from sambhasha.storage.memory import InMemoryRepository
from tests.unit.engine.test_scheduler import EFFICIENT_PATH, MODELS, _run

runner = CliRunner()
MAPPING_REPLIES = [
    json.dumps({"items": ["FND.COARSE_BASOPHILIC_STIPPLING"]}),  # the film report
    json.dumps({"item_id": "DX.LEAD_POISONING"}),  # the committed diagnosis
    json.dumps(
        {
            "items": [
                "ACT.STOP_SUSPECTED_SOURCE",
                "RX.CHELATION.SUCCIMER_ORAL",
                "ACT.NOTIFY_PUBLIC_HEALTH",
            ]
        }
    ),  # the plan
]


@pytest.fixture
def stored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[InMemoryRepository, UUID]:
    shared = InMemoryRepository()
    result, _ = _run(EFFICIENT_PATH, tmp_path, repo=shared)
    models = tmp_path / "models.yaml"
    models.write_text(MODELS, encoding="utf-8")
    fake = FakeLLM({"matcher": MAPPING_REPLIES})

    @contextmanager
    def fake_open(url: str) -> Iterator[InMemoryRepository]:
        yield shared

    monkeypatch.setattr(cli, "open_repository", fake_open)
    monkeypatch.setattr(
        cli,
        "make_gateway",
        lambda replay_only: LLMGateway(load_models_config(models), backend_for=lambda e: fake),
    )
    return shared, result.run.id


def test_evaluate_scores_and_stores_the_run(stored: tuple[InMemoryRepository, UUID]) -> None:
    repo, run_id = stored

    result = runner.invoke(cli.app, ["evaluate", str(run_id)])

    assert result.exit_code == 0, result.output
    # The scripted commit cites E2, which in this run is the question, not the answer holding
    # H10, so the supplement is not in the evidence: lead poisoning without its source is 4.
    assert "Diagnosis score: 4/5 (correct)" in result.output
    (score,) = repo.scores(run_id)
    assert score.mapping is not None
    assert score.mapping.diagnosis == "DX.LEAD_POISONING"


def test_evaluate_refuses_an_unknown_run(stored: tuple[InMemoryRepository, UUID]) -> None:
    result = runner.invoke(cli.app, ["evaluate", str(uuid4())])

    assert result.exit_code == 1
    assert "Refused" in result.output
