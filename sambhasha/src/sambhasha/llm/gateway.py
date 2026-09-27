"""The LLM gateway: structured output, validation, retries, caching and call logging (SPEC §11).

`LLMGateway.structured` asks the role's model for one JSON object matching a Pydantic model.
It sends the JSON schema as the response format (or, for providers without schema support,
inside the prompt), validates the reply, and on an invalid reply retries up to MAX_RETRIES
times, telling the model what was wrong. Every attempt, cached or not, is reported through
`on_call` so the engine can log an `llm_call` event.
"""

import json
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from typing import Final
from uuid import UUID

from pydantic import BaseModel, ValidationError

from sambhasha.domain.events import Event, LlmCall
from sambhasha.llm.backend import ChatBackend, OpenAIBackend
from sambhasha.llm.cache import RecordReplayCache
from sambhasha.llm.config import Endpoint, ModelsConfig, Profile
from sambhasha.llm.ratelimit import WaitLedger
from sambhasha.llm.types import ChatMessage, LlmCallRecord, LLMRequest, LLMResponse

MAX_RETRIES: Final = 2
log = logging.getLogger(__name__)


class LLMBudgetExceededError(RuntimeError):
    """The spending cap is reached: no further paid call is made."""


class LLMOutputError(RuntimeError):
    """The model gave no valid reply after every retry."""

    def __init__(self, message: str, calls: tuple[LlmCallRecord, ...]) -> None:
        super().__init__(message)
        self.calls = calls


@dataclass(frozen=True)
class StructuredResult[T: BaseModel]:
    value: T
    calls: tuple[LlmCallRecord, ...]


class LLMGateway:
    def __init__(
        self,
        config: ModelsConfig,
        *,
        backend_for: Callable[[Endpoint], ChatBackend] | None = None,
        cache: RecordReplayCache | None = None,
        on_call: Callable[[LlmCallRecord], None] = lambda record: None,
        spend_cap_usd: Decimal | None = None,
        waits: WaitLedger | None = None,
    ) -> None:
        self.waits = waits or WaitLedger()
        if backend_for is None:
            ledger = self.waits

            def backend_for(endpoint: Endpoint) -> ChatBackend:
                return OpenAIBackend(endpoint, ledger=ledger)

        self._config = config
        self._cap = spend_cap_usd
        self._spent = Decimal(0)
        self._backend_for = cache_backends(backend_for)
        self._cache = cache
        self._on_call = on_call

    def structured[T: BaseModel](
        self,
        role: str,
        messages: Sequence[ChatMessage],
        schema: type[T],
        *,
        prompt_version: str,
    ) -> StructuredResult[T]:
        profile = self._config.profile_for(role)
        conversation = _with_schema(tuple(messages), schema, profile)
        calls: tuple[LlmCallRecord, ...] = ()
        error_text = ""
        for _attempt in range(MAX_RETRIES + 1):
            request = _request(role, profile, conversation, schema)
            response, cached = self._complete(role, request)
            try:
                value = schema.model_validate_json(_json_text(response.content))
            except ValidationError as error:
                error_text = str(error)
                calls = (
                    *calls,
                    self._record(role, request, response, prompt_version, cached, False),
                )
                conversation = (
                    *conversation,
                    ChatMessage(role="assistant", content=response.content),
                    ChatMessage(role="user", content=_correction(error_text, schema)),
                )
                continue
            calls = (*calls, self._record(role, request, response, prompt_version, cached, True))
            return StructuredResult(value=value, calls=calls)
        raise LLMOutputError(
            f"{role}: no valid {schema.__name__} after {MAX_RETRIES + 1} attempts: {error_text}",
            calls,
        )

    @property
    def spent_usd(self) -> Decimal:
        """What the calls made so far have cost (cached replays cost nothing)."""
        return self._spent

    def _complete(self, role: str, request: LLMRequest) -> tuple[LLMResponse, bool]:
        if self._cache is not None:
            hit = self._cache.get(request)
            if hit is not None:
                return hit, True
        if self._cap is not None and self._spent >= self._cap:
            raise LLMBudgetExceededError(
                f"spending cap of USD {self._cap} reached (spent USD {self._spent})"
            )
        response = self._backend_for(self._config.endpoint_for(role)).complete(request)
        if response.cost_usd is None and self._cap is not None:
            log.warning("%s did not report the cost of a call; it is not counted", request.model)
        self._spent += response.cost_usd or Decimal(0)
        if self._cache is not None:
            self._cache.put(request, response)
        return response, False

    def _record(
        self,
        role: str,
        request: LLMRequest,
        response: LLMResponse,
        prompt_version: str,
        cached: bool,
        valid: bool,
    ) -> LlmCallRecord:
        record = LlmCallRecord(
            role=role,
            model=request.model,
            prompt_version=prompt_version,
            request_hash=request.cache_key(),
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_usd=Decimal(0) if cached else response.cost_usd,  # a replay costs nothing
            cached=cached,
            valid=valid,
        )
        self._on_call(record)
        return record


def cache_backends(
    backend_for: Callable[[Endpoint], ChatBackend],
) -> Callable[[Endpoint], ChatBackend]:
    """One backend per endpoint, made on first use."""
    return cache(backend_for)


def _request(
    role: str, profile: Profile, messages: tuple[ChatMessage, ...], schema: type[BaseModel]
) -> LLMRequest:
    if profile.structured_output == "json_schema":
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": schema.model_json_schema(),
                "strict": False,
            },
        }
    else:
        response_format = {"type": "json_object"}
    return LLMRequest(
        role=role,
        model=profile.model,
        messages=messages,
        temperature=profile.temperature,
        seed=profile.seed,
        max_tokens=profile.max_tokens,
        response_format=json.dumps(response_format, sort_keys=True),
    )


def _with_schema(
    messages: tuple[ChatMessage, ...], schema: type[BaseModel], profile: Profile
) -> tuple[ChatMessage, ...]:
    """Without schema support, the provider sees the schema in the prompt instead."""
    if profile.structured_output == "json_schema":
        return messages
    return (
        *messages,
        ChatMessage(
            role="system",
            content="Reply with one JSON object matching this JSON schema:\n"
            + json.dumps(schema.model_json_schema(), sort_keys=True),
        ),
    )


def _json_text(content: str) -> str:
    """The reply without a Markdown code fence around it, if the model added one."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.removesuffix("```").strip()
    return text


def _correction(error: str, schema: type[BaseModel]) -> str:
    return (
        f"Your reply was not a valid {schema.__name__}:\n{error}\n"
        "Reply again with one JSON object only, matching the schema, and no other text."
    )


def call_event(
    record: LlmCallRecord, *, run_id: UUID, seq: int, sim_minutes: int, seat: str
) -> Event:
    """The `llm_call` Event Log row for one call. Seats never see it (visibility is empty)."""
    return Event(
        run_id=run_id,
        seq=seq,
        sim_minutes=sim_minutes,
        seat=seat,
        type="llm_call",
        payload=LlmCall(role=record.role, request_hash=record.request_hash, cached=record.cached),
        visibility=(),
        source="engine",
        model=record.model,
        prompt_version=record.prompt_version,
        tokens_in=record.tokens_in,
        tokens_out=record.tokens_out,
        cost_usd=record.cost_usd,
    )
