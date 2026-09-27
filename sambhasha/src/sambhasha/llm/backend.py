"""The one client for every provider: the openai SDK against OpenAI-compatible endpoints
(OpenRouter in the cloud, Ollama locally; SPEC §11)."""

import json
import time as _time
from collections.abc import Callable
from decimal import Decimal
from typing import Any, Final, Protocol

import openai

from sambhasha.llm.config import Endpoint
from sambhasha.llm.ratelimit import DailyQuotaError, RateLimiter, WaitLedger, retry_delay
from sambhasha.llm.types import LLMRequest, LLMResponse

TIMEOUT_SECONDS: Final = 120.0
RATE_RETRIES: Final = 6  # retries after a 429 before giving up
FIRST_BACKOFF_SECONDS: Final = 15.0
MAX_BACKOFF_SECONDS: Final = 120.0
SERVER_RETRIES: Final = 4  # retries after a temporary server or connection error
FIRST_SERVER_PAUSE_SECONDS: Final = 5.0
_TRANSIENT: Final = (openai.InternalServerError, openai.APIConnectionError)


class LLMCallError(RuntimeError):
    """A provider call failed. The message names the model, never the key."""


class QuotaExhaustedError(LLMCallError, DailyQuotaError):
    """The day's requests for a model are used up."""


class ChatBackend(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...


class OpenAIBackend:
    def __init__(
        self,
        endpoint: Endpoint,
        create: Callable[..., Any] | None = None,
        *,
        ledger: WaitLedger | None = None,
        clock: Callable[[], float] = _time.monotonic,
        sleep: Callable[[float], None] = _time.sleep,
    ) -> None:
        self._reports_cost = endpoint.reports_cost
        if create is None:
            client = openai.OpenAI(
                base_url=endpoint.base_url,
                api_key=endpoint.api_key,
                timeout=TIMEOUT_SECONDS,
                max_retries=endpoint.sdk_retries,
            )
            create = client.chat.completions.create
        self._create = create
        self._limiter = RateLimiter(
            endpoint.rpm,
            endpoint.rpd,
            model=endpoint.model or "model",
            ledger=ledger or WaitLedger(),
            clock=clock,
            sleep=sleep,
        )

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
        completion = self._call(request, kwargs)
        usage = getattr(completion, "usage", None)
        return LLMResponse(
            content=completion.choices[0].message.content or "",
            model=request.model,
            tokens_in=getattr(usage, "prompt_tokens", 0) or 0,
            tokens_out=getattr(usage, "completion_tokens", 0) or 0,
            cost_usd=self._cost(usage),
        )

    def _call(self, request: LLMRequest, kwargs: dict[str, Any]) -> Any:
        """One completion, paced to the model's limits and retried after a 429 or a temporary
        server error; every pause is recorded."""
        server_failures = 0
        for attempt in range(RATE_RETRIES + SERVER_RETRIES + 1):
            try:
                self._limiter.acquire()
            except DailyQuotaError as error:
                raise QuotaExhaustedError(str(error)) from error
            try:
                return self._create(**kwargs)
            except openai.RateLimitError as error:
                text = f"{error} {getattr(error, 'body', '')}"
                if "PerDay" in text or "per day" in text.lower():
                    raise QuotaExhaustedError(
                        f"{request.model}: the daily quota is used up; it resets at midnight"
                        " Pacific time"
                    ) from error
                delay = retry_delay(text) or min(
                    FIRST_BACKOFF_SECONDS * 2**attempt, MAX_BACKOFF_SECONDS
                )
                if attempt < RATE_RETRIES:
                    self._limiter.pause(delay, "rate limited")
                else:
                    break
            except _TRANSIENT as error:
                server_failures += 1
                if server_failures > SERVER_RETRIES:
                    raise LLMCallError(
                        f"call to {request.model} failed: {type(error).__name__}"
                    ) from error
                pause = FIRST_SERVER_PAUSE_SECONDS * 2 ** (server_failures - 1)
                self._limiter.pause(pause, "server error")
            except openai.OpenAIError as error:
                raise LLMCallError(
                    f"call to {request.model} failed: {type(error).__name__}"
                ) from error
        raise LLMCallError(f"call to {request.model} failed: still rate limited after retries")

    def _cost(self, usage: object) -> Decimal | None:
        if not self._reports_cost:
            return Decimal(0)
        cost = getattr(usage, "cost", None)
        return None if cost is None else Decimal(str(cost))
