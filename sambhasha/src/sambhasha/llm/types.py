"""Requests, responses and call records for the LLM gateway (SPEC §11)."""

import hashlib
import json
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, NonNegativeInt

from sambhasha.domain.base import DomainModel


class ChatMessage(DomainModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMRequest(DomainModel):
    """One call to a model. `role` says which seat or service asked; it is not sent."""

    model: str
    messages: tuple[ChatMessage, ...]
    temperature: float | None = None
    seed: int | None = None
    max_tokens: Annotated[int, Field(ge=1)]
    response_format: str | None = None  # the provider's response_format, as JSON text
    role: str = ""

    def cache_key(self) -> str:
        """SHA-256 of everything the model sees; the role and any API key are not part of it."""
        body = self.model_dump(mode="json", exclude={"role"})
        return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class LLMResponse(DomainModel):
    content: str
    model: str
    tokens_in: NonNegativeInt = 0
    tokens_out: NonNegativeInt = 0
    cost_usd: Annotated[Decimal, Field(ge=0)] | None = None  # None: the provider did not say


class LlmCallRecord(DomainModel):
    """What the Event Log keeps about one call (an `llm_call` event)."""

    role: str
    model: str
    prompt_version: str
    request_hash: str
    tokens_in: NonNegativeInt
    tokens_out: NonNegativeInt
    cost_usd: Annotated[Decimal, Field(ge=0)] | None
    cached: bool
    valid: bool
