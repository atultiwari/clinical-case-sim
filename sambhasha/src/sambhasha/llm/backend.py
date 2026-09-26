"""The one client for every provider: the openai SDK against OpenAI-compatible endpoints
(OpenRouter in the cloud, Ollama locally; SPEC §11)."""

import json
from collections.abc import Callable
from decimal import Decimal
from typing import Any, Protocol

import openai

from sambhasha.llm.config import Endpoint
from sambhasha.llm.types import LLMRequest, LLMResponse

TIMEOUT_SECONDS = 120.0
SDK_RETRIES = 2  # the SDK's own retries on connection errors and rate limits


class LLMCallError(RuntimeError):
    """A provider call failed. The message names the model, never the key."""


class ChatBackend(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...


class OpenAIBackend:
    def __init__(self, endpoint: Endpoint, create: Callable[..., Any] | None = None) -> None:
        self._reports_cost = endpoint.reports_cost
        if create is None:
            client = openai.OpenAI(
                base_url=endpoint.base_url,
                api_key=endpoint.api_key,
                timeout=TIMEOUT_SECONDS,
                max_retries=SDK_RETRIES,
            )
            create = client.chat.completions.create
        self._create = create

    def complete(self, request: LLMRequest) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": [m.model_dump() for m in request.messages],
            "max_tokens": request.max_tokens,
        }
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.seed is not None:
            kwargs["seed"] = request.seed
        if request.response_format:
            kwargs["response_format"] = json.loads(request.response_format)
        if self._reports_cost:
            kwargs["extra_body"] = {"usage": {"include": True}}  # OpenRouter adds usage.cost
        try:
            completion = self._create(**kwargs)
        except openai.OpenAIError as error:
            raise LLMCallError(f"call to {request.model} failed: {type(error).__name__}") from error
        usage = getattr(completion, "usage", None)
        return LLMResponse(
            content=completion.choices[0].message.content or "",
            model=request.model,
            tokens_in=getattr(usage, "prompt_tokens", 0) or 0,
            tokens_out=getattr(usage, "completion_tokens", 0) or 0,
            cost_usd=self._cost(usage),
        )

    def _cost(self, usage: object) -> Decimal | None:
        if not self._reports_cost:
            return Decimal(0)
        cost = getattr(usage, "cost", None)
        return None if cost is None else Decimal(str(cost))
