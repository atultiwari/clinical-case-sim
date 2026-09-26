"""The matcher: a small model that chooses among candidate catalogue ids (D-005, D-022).

It sees only the request text and global catalogue entries, never the case, and it returns
an id from the list or none. It never writes an answer (invariant I4).
"""

import logging
from typing import Protocol

from pydantic import BaseModel

from sambhasha.catalogue import CatalogueItem
from sambhasha.llm.gateway import LLMGateway, LLMOutputError
from sambhasha.llm.types import ChatMessage
from sambhasha.prompts import Prompt, load_prompt

log = logging.getLogger(__name__)


class Matcher(Protocol):
    def choose(self, text: str, candidates: tuple[CatalogueItem, ...]) -> str | None: ...


class MatcherChoice(BaseModel):
    item_id: str | None


class LLMMatcher:
    def __init__(self, gateway: LLMGateway, prompt: Prompt | None = None) -> None:
        self._gateway = gateway
        self._prompt = prompt or load_prompt("matcher")

    def choose(self, text: str, candidates: tuple[CatalogueItem, ...]) -> str | None:
        listed = "\n".join(
            f"{n}. {item.id}: {item.name}"
            + (f" (also: {', '.join(item.synonyms)})" if item.synonyms else "")
            for n, item in enumerate(candidates, start=1)
        )
        messages = (
            ChatMessage(role="system", content=self._prompt.text),
            ChatMessage(role="user", content=f"Request: {text}\n\nCandidates:\n{listed}"),
        )
        try:
            result = self._gateway.structured(
                "matcher", messages, MatcherChoice, prompt_version=self._prompt.version
            )
        except LLMOutputError as error:
            log.warning("matcher gave no valid choice for %r: %s", text, error)
            return None
        choice = result.value.item_id
        return choice if choice in {item.id for item in candidates} else None
