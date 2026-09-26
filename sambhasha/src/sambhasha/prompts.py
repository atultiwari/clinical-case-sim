"""Prompts in `prompts/*.md`, each with a `version` in YAML front matter (CLAUDE.md)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

PROMPTS_DIR: Final = Path(__file__).resolve().parents[2] / "prompts"


class PromptError(ValueError):
    """A prompt file is missing or has no version."""


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    text: str


def load_prompt(name: str, directory: Path = PROMPTS_DIR) -> Prompt:
    path = directory / f"{name}.md"
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise PromptError(f"prompt not found: {path}") from error
    if not raw.startswith("---\n") or "\n---\n" not in raw[4:]:
        raise PromptError(f"{path.name} has no front matter")
    header, body = raw[4:].split("\n---\n", 1)
    meta = yaml.safe_load(header) or {}
    version = meta.get("version") if isinstance(meta, dict) else None
    if version is None:
        raise PromptError(f"{path.name} has no version in its front matter")
    return Prompt(name=name, version=str(version), text=body.strip())
