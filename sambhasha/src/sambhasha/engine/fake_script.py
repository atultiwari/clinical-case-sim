"""Scripted replies for `sambhasha run --fake`, from `configs/fake/*.yaml` (PLAN P1.9)."""

import json
from pathlib import Path
from typing import Final

import yaml

CONFIGS: Final = Path(__file__).resolve().parents[3] / "configs"


class FakeScriptError(ValueError):
    """The fake script is missing or malformed."""


def load_fake_script(name: str, directory: Path = CONFIGS) -> dict[str, list[str]]:
    """Each role's replies, in order, as the JSON text a model would send."""
    path = directory / name
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FakeScriptError(f"fake script not found: {path}") from error
    except yaml.YAMLError as error:
        raise FakeScriptError(f"{path.name} is not valid YAML: {error}") from error
    if not isinstance(data, dict) or not all(isinstance(v, list) for v in data.values()):
        raise FakeScriptError(f"{path.name}: each role needs a list of replies")
    return {role: [json.dumps(reply) for reply in replies] for role, replies in data.items()}
