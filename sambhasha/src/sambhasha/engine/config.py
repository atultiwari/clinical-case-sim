"""A run's configuration, from `configs/*.yaml` (SPEC §10.4; D-020)."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Final

import yaml
from pydantic import Field, ValidationError

from sambhasha.domain.base import DomainModel, NonEmptyStr

DEFAULT_RUN_CONFIG: Final = Path(__file__).resolve().parents[3] / "configs" / "pilot.yaml"


class RunConfigError(ValueError):
    """The run configuration is missing or malformed."""


class Limits(DomainModel):
    attending_turns: Annotated[int, Field(ge=1)]
    referrals: Annotated[int, Field(ge=0)]
    budget_inr: Annotated[Decimal, Field(gt=0)]


class ChallengerConfig(DomainModel):
    before_commit: bool = True
    every_n_turns: Annotated[int, Field(ge=0)] = 0


class RunConfig(DomainModel):
    bundle: NonEmptyStr
    limits: Limits
    consultant_session_actions: Annotated[int, Field(ge=1)] = 4
    challenger: ChallengerConfig = ChallengerConfig()
    consultants: tuple[NonEmptyStr, ...]
    services: tuple[NonEmptyStr, ...]

    def config_hash(self) -> str:
        """SHA-256 of the configuration, recorded on the run."""
        body = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()


def load_run_config(path: Path = DEFAULT_RUN_CONFIG) -> RunConfig:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RunConfigError(f"run config not found: {path}") from error
    try:
        return RunConfig.model_validate(data)
    except ValidationError as error:
        raise RunConfigError(f"{path.name}: {error}") from error
