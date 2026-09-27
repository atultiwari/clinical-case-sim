"""P1.1: model profiles from configs/models.yaml (SPEC §11; D-010, D-020)."""

from pathlib import Path

import pytest

from sambhasha.llm.config import DOCTOR_ROLES, ROLES, ConfigError, load_models_config

CONFIG = Path(__file__).resolve().parents[3] / "configs" / "models.yaml"


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "models.yaml"
    path.write_text(text, encoding="utf-8")
    return path


MINIMAL = """
providers:
  openrouter:
    {base_url: "https://openrouter.ai/api/v1", api_key_env: TEST_KEY, reports_cost: true}
  ollama:
    {base_url_env: TEST_OLLAMA, default_base_url: "http://localhost:11434/v1", api_key: ollama}
profiles:
  cloud: {provider: openrouter, model: vendor/model-a, family: vendor}
  local: {provider: ollama, model: small, family: other, structured_output: json_object}
roles: {attending: cloud, challenger: cloud, consultant: cloud, service: cloud,
        matcher: cloud, synthetic: local, curator: cloud, evaluator: local}
"""


def test_the_repository_config_loads_and_covers_every_role() -> None:
    config = load_models_config(CONFIG)

    assert set(config.roles) == set(ROLES)
    for role in ROLES:
        assert config.profile_for(role).model


PRODUCTION = CONFIG.with_name("models.openrouter.yaml")


def test_the_production_profiles_keep_d010_strictly() -> None:
    config = load_models_config(PRODUCTION)
    doctor_families = {config.profile_for(role).family for role in DOCTOR_ROLES}

    assert config.family_exception is None
    assert config.profile_for("synthetic").family not in doctor_families
    assert config.profile_for("evaluator").family not in doctor_families


def test_the_pilot_runs_on_free_gemini_with_a_recorded_d010_exception() -> None:
    config = load_models_config(CONFIG)

    assert {config.profile_for(role).model for role in ROLES} <= {
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
    }
    assert config.profile_for("matcher").model == "gemini-3.5-flash-lite"
    assert config.family_exception
    assert "D-028" in config.family_exception


def test_a_same_family_config_without_an_exception_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("family: other", "family: vendor")

    with pytest.raises(ConfigError, match="D-010"):
        load_models_config(_write(tmp_path, text))


def test_a_stated_exception_allows_one_family(tmp_path: Path) -> None:
    text = MINIMAL.replace("family: other", "family: vendor") + (
        "family_exception: pilot on one provider\n"
    )

    assert load_models_config(_write(tmp_path, text)).family_exception == "pilot on one provider"


def test_rate_limits_reach_the_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_KEY", "k")
    text = MINIMAL.replace(
        "cloud: {provider: openrouter, model: vendor/model-a, family: vendor}",
        "cloud: {provider: openrouter, model: vendor/model-a, family: vendor, rpm: 10, rpd: 250}",
    )
    config = load_models_config(_write(tmp_path, text))

    endpoint = config.endpoint_for("attending")

    assert (endpoint.model, endpoint.rpm, endpoint.rpd) == ("vendor/model-a", 10, 250)


def test_the_doctor_seats_can_switch_profile() -> None:
    config = load_models_config(CONFIG)

    switched = config.with_doctor_profile("doctor-b")

    assert {switched.profile_for(r).model for r in DOCTOR_ROLES} == {"gemini-2.5-flash"}
    assert switched.profile_for("matcher") == config.profile_for("matcher")
    with pytest.raises(ConfigError, match="no-such"):
        config.with_doctor_profile("no-such")


def test_a_profile_resolves_its_provider_and_key_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TEST_KEY", "secret-value")
    config = load_models_config(_write(tmp_path, MINIMAL))

    endpoint = config.endpoint_for("attending")

    assert endpoint.base_url == "https://openrouter.ai/api/v1"
    assert endpoint.api_key == "secret-value"
    assert endpoint.reports_cost is True


def test_a_missing_api_key_is_a_clear_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TEST_KEY", raising=False)
    config = load_models_config(_write(tmp_path, MINIMAL))

    with pytest.raises(ConfigError, match="TEST_KEY"):
        config.endpoint_for("attending")


def test_ollama_falls_back_to_its_default_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TEST_OLLAMA", raising=False)
    config = load_models_config(_write(tmp_path, MINIMAL))

    endpoint = config.endpoint_for("synthetic")

    assert endpoint.base_url == "http://localhost:11434/v1"
    assert endpoint.api_key == "ollama"
    assert endpoint.reports_cost is False


def test_ollama_reads_its_url_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TEST_OLLAMA", "http://gpu-box:11434/v1")
    config = load_models_config(_write(tmp_path, MINIMAL))

    assert config.endpoint_for("synthetic").base_url == "http://gpu-box:11434/v1"


def test_a_role_without_a_profile_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("evaluator: local}", "}")

    with pytest.raises(ConfigError, match="evaluator"):
        load_models_config(_write(tmp_path, text))


def test_a_profile_naming_an_unknown_provider_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("provider: ollama", "provider: nowhere")

    with pytest.raises(ConfigError, match="nowhere"):
        load_models_config(_write(tmp_path, text))


def test_a_role_naming_an_unknown_profile_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("matcher: cloud", "matcher: missing")

    with pytest.raises(ConfigError, match="missing"):
        load_models_config(_write(tmp_path, text))


def test_an_unknown_field_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("family: vendor}", "family: vendor, temprature: 1}")

    with pytest.raises(ConfigError, match="temprature"):
        load_models_config(_write(tmp_path, text))


def test_a_missing_file_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_models_config(tmp_path / "absent.yaml")


def test_yaml_that_is_not_a_mapping_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="mapping"):
        load_models_config(_write(tmp_path, "- just\n- a list\n"))


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('base_url: "https://openrouter.ai/api/v1", ', "", "base_url"),
        ("api_key_env: TEST_KEY, ", "", "api_key"),
    ],
)
def test_a_provider_needs_a_url_and_a_key(tmp_path: Path, old: str, new: str, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_models_config(_write(tmp_path, MINIMAL.replace(old, new)))


def test_an_unknown_role_is_a_clear_error(tmp_path: Path) -> None:
    config = load_models_config(_write(tmp_path, MINIMAL))

    with pytest.raises(ConfigError, match="judge"):
        config.profile_for("judge")


def test_an_empty_url_variable_without_a_default_is_a_clear_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TEST_OLLAMA", raising=False)
    text = MINIMAL.replace(', default_base_url: "http://localhost:11434/v1"', "")
    config = load_models_config(_write(tmp_path, text))

    with pytest.raises(ConfigError, match="TEST_OLLAMA"):
        config.endpoint_for("synthetic")


def test_broken_yaml_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not valid YAML"):
        load_models_config(_write(tmp_path, "providers: [unclosed\n"))
