"""Mapping the run's free text to catalogue ids before scoring (D-022; SPEC §13).

- A diagnosis is coded against the catalogue's diagnoses (P1.2); if nothing matches
  exactly, the matcher chooses among the candidates.
- A plan becomes the ordered list of actions and referrals it commits to, and a Diagnostic
  Service report the findings it states; the matcher picks them from the catalogue's lists.

Only ids from the catalogue are kept.
"""

import logging
from typing import Protocol

from pydantic import BaseModel

from sambhasha.catalogue import Catalogue, CatalogueItem, Kind
from sambhasha.gatekeeper.coding import Coder
from sambhasha.gatekeeper.matcher import LLMMatcher
from sambhasha.llm.gateway import LLMGateway, LLMOutputError
from sambhasha.llm.types import ChatMessage
from sambhasha.prompts import Prompt, load_prompt

log = logging.getLogger(__name__)


class Mapper(Protocol):
    def diagnosis(self, text: str) -> str | None: ...
    def plan(self, text: str) -> tuple[str, ...]: ...
    def findings(self, text: str) -> tuple[str, ...]: ...
    def referral(self, specialty: str) -> str | None: ...


class ItemList(BaseModel):
    items: list[str]


class ScoringMapper:
    def __init__(
        self,
        catalogue: Catalogue,
        coder: Coder,
        gateway: LLMGateway,
        prompt: Prompt | None = None,
    ) -> None:
        self._catalogue = catalogue
        self._coder = coder
        self._gateway = gateway
        self._matcher = LLMMatcher(gateway)
        self._prompt = prompt or load_prompt("plan_mapper")
        self._plan_items = tuple(i for i in catalogue.items if i.kind in ("action", "referral"))
        self._finding_items = tuple(i for i in catalogue.items if i.kind == "finding")

    def diagnosis(self, text: str) -> str | None:
        return self._one(text, ("diagnosis",))

    def referral(self, specialty: str) -> str | None:
        return self._one(specialty, ("referral",))

    def plan(self, text: str) -> tuple[str, ...]:
        return self._many(text, self._plan_items)

    def findings(self, text: str) -> tuple[str, ...]:
        return self._many(text, self._finding_items)

    def _one(self, text: str, kinds: tuple[Kind, ...]) -> str | None:
        coding = self._coder.code(text, kinds=kinds)
        if coding.status == "exact":
            return coding.ids[0]
        if coding.status == "candidates":
            candidates = tuple(self._catalogue.get(i) for i in coding.ids)
            return self._matcher.choose(text, candidates)
        return None

    def _many(self, text: str, items: tuple[CatalogueItem, ...]) -> tuple[str, ...]:
        listed = "\n".join(f"- {item.id}: {item.name}" for item in items)
        messages = (
            ChatMessage(role="system", content=self._prompt.text),
            ChatMessage(role="user", content=f"Text:\n{text}\n\nCatalogue items:\n{listed}"),
        )
        try:
            result = self._gateway.structured(
                "matcher", messages, ItemList, prompt_version=self._prompt.version
            )
        except LLMOutputError as error:
            log.warning("no valid mapping for %r: %s", text, error)
            return ()
        known = {item.id for item in items}
        return tuple(dict.fromkeys(i for i in result.value.items if i in known))
