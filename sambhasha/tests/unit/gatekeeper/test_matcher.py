"""P1.3: the matcher model chooses among candidate catalogue ids only (D-022)."""

from pathlib import Path

import pytest

from sambhasha.catalogue import Catalogue
from sambhasha.gatekeeper.matcher import LLMMatcher
from sambhasha.llm.config import ModelsConfig, load_models_config
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway
from sambhasha.prompts import PromptError, load_prompt

CATALOGUE = Catalogue.load()
CANDIDATES = (CATALOGUE.get("LAB.HAEM.CBC"), CATALOGUE.get("LAB.HAEM.FILM"))
CONFIG = """
providers:
  local: {base_url: "http://localhost:11434/v1", api_key: ollama}
profiles:
  p: {provider: local, model: small, family: other}
roles: {attending: p, challenger: p, consultant: p, service: p, matcher: p, synthetic: p,
        curator: p, evaluator: p}
"""


@pytest.fixture
def config(tmp_path: Path) -> ModelsConfig:
    path = tmp_path / "models.yaml"
    path.write_text(CONFIG, encoding="utf-8")
    return load_models_config(path)


def _matcher(config: ModelsConfig, *replies: str) -> tuple[LLMMatcher, FakeLLM]:
    fake = FakeLLM({"matcher": list(replies)})
    return LLMMatcher(LLMGateway(config, backend_for=lambda e: fake)), fake


def test_a_choice_from_the_list_is_returned(config: ModelsConfig) -> None:
    matcher, fake = _matcher(config, '{"item_id": "LAB.HAEM.CBC"}')

    assert matcher.choose("full blood picture", CANDIDATES) == "LAB.HAEM.CBC"
    prompt = fake.requests[0].messages[-1].content
    assert "Request: full blood picture" in prompt
    assert "LAB.HAEM.CBC: Full blood count" in prompt


def test_none_means_no_match(config: ModelsConfig) -> None:
    matcher, _ = _matcher(config, '{"item_id": null}')

    assert matcher.choose("something else", CANDIDATES) is None


def test_an_id_outside_the_list_is_ignored(config: ModelsConfig) -> None:
    matcher, _ = _matcher(config, '{"item_id": "LAB.TOX.BLOOD_LEAD"}')

    assert matcher.choose("full blood picture", CANDIDATES) is None


def test_a_model_that_never_answers_validly_means_no_match(config: ModelsConfig) -> None:
    matcher, _ = _matcher(config, "no", "still no", "never")

    assert matcher.choose("full blood picture", CANDIDATES) is None


def test_the_matcher_prompt_has_a_version() -> None:
    prompt = load_prompt("matcher")

    assert prompt.version == "1"
    assert "catalogue" in prompt.text


def test_a_prompt_without_front_matter_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "bad.md").write_text("no header", encoding="utf-8")
    (tmp_path / "unversioned.md").write_text("---\ntitle: x\n---\nbody", encoding="utf-8")

    with pytest.raises(PromptError, match="front matter"):
        load_prompt("bad", tmp_path)
    with pytest.raises(PromptError, match="version"):
        load_prompt("unversioned", tmp_path)
    with pytest.raises(PromptError, match="not found"):
        load_prompt("absent", tmp_path)
