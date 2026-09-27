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
    sdk_retries: int = Field(default=2, ge=0)  # the SDK's own retries; 0 when Sambhasha paces

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
    rpm: int | None = Field(default=None, ge=1)  # requests per minute this model allows
    rpd: int | None = Field(default=None, ge=1)  # requests per day


class Endpoint(DomainModel):
    base_url: str
    api_key: str
    reports_cost: bool
    model: str = ""
    rpm: int | None = None
    rpd: int | None = None
    sdk_retries: int = 2


class ModelsConfig(DomainModel):
    providers: dict[str, Provider]
    profiles: dict[str, Profile]
    roles: dict[str, str]
    # Why the Synthetic Findings Service or the Evaluator may share a family with the doctor
    # seats (D-010); required whenever they do.
    family_exception: str | None = None

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
        doctors = {self.profiles[self.roles[r]].family for r in DOCTOR_ROLES}
        shared = [
            r for r in ("synthetic", "evaluator") if self.profiles[self.roles[r]].family in doctors
        ]
        if shared and not self.family_exception:
            raise ValueError(
                f"D-010: {' and '.join(shared)} share a model family with the doctor seats;"
                " use another family or state family_exception"
            )
        return self

    def with_doctor_profile(self, profile: str) -> "ModelsConfig":
        """The same config with every doctor seat on another profile (P1.11's second profile)."""
        if profile not in self.profiles:
            raise ConfigError(f"no profile {profile!r} in the models config")
        roles = {**self.roles, **dict.fromkeys(DOCTOR_ROLES, profile)}
        return ModelsConfig.model_validate({**self.model_dump(), "roles": roles})

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
        profile = self.profile_for(role)
        return Endpoint(
            base_url=base_url,
            api_key=api_key,
            reports_cost=provider.reports_cost,
            model=profile.model,
            rpm=profile.rpm,
            rpd=profile.rpd,
            sdk_retries=provider.sdk_retries,
        )


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
