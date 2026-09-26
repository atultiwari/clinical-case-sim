"""Model profiles per role, from `configs/models.yaml` (SPEC §11; D-020).

API keys are named by environment variable and read only when an endpoint is needed, so
the file holds no secret and tests that use the FakeLLM need no key.
"""

import os
from pathlib import Path
from typing import Final, Literal, Self

import yaml
from pydantic import Field, ValidationError, model_validator

from sambhasha.domain.base import DomainModel, NonEmptyStr

ROLES: Final = (
    "attending",
    "challenger",
    "consultant",
    "service",
    "matcher",
    "synthetic",
    "curator",
    "evaluator",
)
DOCTOR_ROLES: Final = ("attending", "challenger", "consultant", "service")
DEFAULT_CONFIG: Final = Path(__file__).resolve().parents[3] / "configs" / "models.yaml"


class ConfigError(ValueError):
    """The models configuration is missing, malformed or incomplete."""


class Provider(DomainModel):
    base_url: str | None = None
    base_url_env: str | None = None
    default_base_url: str | None = None
    api_key: str | None = None  # only for keyless local servers such as Ollama
    api_key_env: str | None = None
    reports_cost: bool = False

    @model_validator(mode="after")
    def _has_url_and_key(self) -> Self:
        if not (self.base_url or self.base_url_env):
            raise ValueError("a provider needs base_url or base_url_env")
        if not (self.api_key or self.api_key_env):
            raise ValueError("a provider needs api_key_env (or api_key for a local server)")
        return self


class Profile(DomainModel):
    provider: NonEmptyStr
    model: NonEmptyStr
    family: NonEmptyStr  # the model family, for the D-010 check
    temperature: float | None = 0
    seed: int | None = None
    max_tokens: int = Field(default=2000, ge=1)
    structured_output: Literal["json_schema", "json_object"] = "json_schema"


class Endpoint(DomainModel):
    base_url: str
    api_key: str
    reports_cost: bool


class ModelsConfig(DomainModel):
    providers: dict[str, Provider]
    profiles: dict[str, Profile]
    roles: dict[str, str]

    @model_validator(mode="after")
    def _references_resolve(self) -> Self:
        missing_roles = [r for r in ROLES if r not in self.roles]
        if missing_roles:
            raise ValueError(f"roles without a profile: {', '.join(missing_roles)}")
        for role, profile in self.roles.items():
            if profile not in self.profiles:
                raise ValueError(f"role {role} names an unknown profile {profile!r}")
        for name, profile_config in self.profiles.items():
            if profile_config.provider not in self.providers:
                raise ValueError(
                    f"profile {name} names an unknown provider {profile_config.provider!r}"
                )
        return self

    def profile_for(self, role: str) -> Profile:
        try:
            return self.profiles[self.roles[role]]
        except KeyError:
            raise ConfigError(f"no profile for role {role!r}") from None

    def endpoint_for(self, role: str) -> Endpoint:
        """The URL and key for a role's provider, read from the environment now."""
        provider = self.providers[self.profile_for(role).provider]
        base_url = (
            os.environ.get(provider.base_url_env or "")
            or provider.base_url
            or provider.default_base_url
        )
        api_key = provider.api_key or os.environ.get(provider.api_key_env or "")
        if not base_url:
            raise ConfigError(f"set {provider.base_url_env} for role {role}")
        if not api_key:
            raise ConfigError(f"set {provider.api_key_env} in .env for role {role}")
        return Endpoint(base_url=base_url, api_key=api_key, reports_cost=provider.reports_cost)


def load_models_config(path: Path = DEFAULT_CONFIG) -> ModelsConfig:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"models config not found: {path}") from error
    except yaml.YAMLError as error:
        raise ConfigError(f"{path.name} is not valid YAML: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name} must be a mapping of providers, profiles and roles")
    try:
        return ModelsConfig.model_validate(data)
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or 'config'}: {e['msg']}" for e in error.errors()
        )
        raise ConfigError(f"{path.name}: {problems}") from error
