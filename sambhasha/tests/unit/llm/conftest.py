"""A models config that needs no API key, for gateway tests with the FakeLLM."""

from pathlib import Path

import pytest

from sambhasha.llm.config import ModelsConfig, load_models_config

TEST_CONFIG = """
providers:
  cloud: {base_url: "https://example.invalid/v1", api_key: test-key, reports_cost: true}
  local: {base_url: "http://localhost:11434/v1", api_key: ollama}
profiles:
  doctor: {provider: cloud, model: vendor/doctor, family: vendor, temperature: 0, seed: 7,
           max_tokens: 500}
  other: {provider: local, model: small, family: other, structured_output: json_object}
roles: {attending: doctor, challenger: doctor, consultant: doctor, service: doctor,
        matcher: doctor, synthetic: other, curator: doctor, evaluator: other}
family_exception: tests use one scripted model
"""


@pytest.fixture
def config(tmp_path: Path) -> ModelsConfig:
    path = tmp_path / "models.yaml"
    path.write_text(TEST_CONFIG, encoding="utf-8")
    return load_models_config(path)
