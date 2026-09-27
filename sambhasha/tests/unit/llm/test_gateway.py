"""P1.1: structured output with validation and retries, caching and call logging (SPEC §11)."""

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import BaseModel

from sambhasha.llm.cache import RecordReplayCache
from sambhasha.llm.config import ModelsConfig
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import MAX_RETRIES, LLMGateway, LLMOutputError, call_event
from sambhasha.llm.types import ChatMessage, LlmCallRecord

MESSAGES = (
    ChatMessage(role="system", content="You are the Attending Physician."),
    ChatMessage(role="user", content="Ask one question."),
)
VALID = '{"question": "Any herbal remedies?"}'


class Question(BaseModel):
    question: str


def _gateway(
    config: ModelsConfig, fake: FakeLLM, cache: RecordReplayCache | None = None
) -> tuple[LLMGateway, list[LlmCallRecord]]:
    calls: list[LlmCallRecord] = []
    gateway = LLMGateway(
        config, backend_for=lambda endpoint: fake, cache=cache, on_call=calls.append
    )
    return gateway, calls


def test_a_valid_reply_is_parsed_and_logged_once(config: ModelsConfig) -> None:
    fake = FakeLLM({"attending": [VALID]})
    gateway, calls = _gateway(config, fake)

    result = gateway.structured("attending", MESSAGES, Question, prompt_version="3")

    assert result.value == Question(question="Any herbal remedies?")
    assert len(calls) == 1
    assert (calls[0].role, calls[0].model, calls[0].prompt_version) == (
        "attending",
        "vendor/doctor",
        "3",
    )
    assert calls[0].valid is True


def test_the_request_carries_the_profile_and_the_json_schema(config: ModelsConfig) -> None:
    fake = FakeLLM({"attending": [VALID]})
    gateway, _ = _gateway(config, fake)

    gateway.structured("attending", MESSAGES, Question, prompt_version="3")

    (request,) = fake.requests
    assert (request.model, request.temperature, request.seed, request.max_tokens) == (
        "vendor/doctor",
        0,
        7,
        500,
    )
    response_format = json.loads(request.response_format or "{}")
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["schema"]["required"] == ["question"]


def test_json_object_mode_puts_the_schema_in_the_prompt(config: ModelsConfig) -> None:
    fake = FakeLLM({"synthetic": [VALID]})
    gateway, _ = _gateway(config, fake)

    gateway.structured("synthetic", MESSAGES, Question, prompt_version="1")

    (request,) = fake.requests
    assert json.loads(request.response_format or "{}") == {"type": "json_object"}
    assert '"question"' in request.messages[-1].content


def test_an_invalid_reply_is_retried_with_the_error(config: ModelsConfig) -> None:
    fake = FakeLLM({"attending": ['{"asked": "x"}', VALID]})
    gateway, calls = _gateway(config, fake)

    result = gateway.structured("attending", MESSAGES, Question, prompt_version="3")

    assert result.value.question == "Any herbal remedies?"
    assert [c.valid for c in calls] == [False, True]
    retry = fake.requests[1].messages
    assert retry[-2] == ChatMessage(role="assistant", content='{"asked": "x"}')
    assert retry[-1].role == "user"
    assert "question" in retry[-1].content


def test_a_reply_in_a_code_fence_is_accepted(config: ModelsConfig) -> None:
    fake = FakeLLM({"attending": [f"```json\n{VALID}\n```"]})
    gateway, _ = _gateway(config, fake)

    assert gateway.structured("attending", MESSAGES, Question, prompt_version="3").value.question


def test_after_two_retries_the_gateway_gives_up(config: ModelsConfig) -> None:
    fake = FakeLLM({"attending": ["nonsense"] * (MAX_RETRIES + 1)})
    gateway, calls = _gateway(config, fake)

    with pytest.raises(LLMOutputError) as caught:
        gateway.structured("attending", MESSAGES, Question, prompt_version="3")

    assert MAX_RETRIES == 2
    assert len(calls) == 3
    assert len(caught.value.calls) == 3
    assert "attending" in str(caught.value)


def test_a_second_identical_request_is_served_from_the_cache(
    config: ModelsConfig, tmp_path: Path
) -> None:
    fake = FakeLLM({"attending": [VALID]})
    gateway, calls = _gateway(config, fake, RecordReplayCache(tmp_path))

    first = gateway.structured("attending", MESSAGES, Question, prompt_version="3")
    second = gateway.structured("attending", MESSAGES, Question, prompt_version="3")

    assert first.value == second.value
    assert len(fake.requests) == 1  # no second network call
    assert [c.cached for c in calls] == [False, True]
    assert calls[1].cost_usd == Decimal(0)


def test_a_rerun_with_a_fresh_gateway_replays_from_disk(
    config: ModelsConfig, tmp_path: Path
) -> None:
    first_gateway, _ = _gateway(
        config, FakeLLM({"attending": [VALID]}), RecordReplayCache(tmp_path)
    )
    first_gateway.structured("attending", MESSAGES, Question, prompt_version="3")
    unused = FakeLLM({})
    rerun, calls = _gateway(config, unused, RecordReplayCache(tmp_path, replay_only=True))

    result = rerun.structured("attending", MESSAGES, Question, prompt_version="3")

    assert result.value.question == "Any herbal remedies?"
    assert unused.requests == ()
    assert calls[0].cached is True


def test_cost_and_tokens_are_logged(config: ModelsConfig) -> None:
    fake = FakeLLM({"attending": [VALID]}, cost_usd=Decimal("0.0021"), tokens=(120, 18))
    gateway, calls = _gateway(config, fake)

    gateway.structured("attending", MESSAGES, Question, prompt_version="3")

    (call,) = calls
    assert (call.tokens_in, call.tokens_out, call.cost_usd) == (120, 18, Decimal("0.0021"))
    assert call.request_hash == fake.requests[0].cache_key()


def test_a_call_becomes_an_llm_call_event() -> None:
    record = LlmCallRecord(
        role="attending",
        model="vendor/doctor",
        prompt_version="3",
        request_hash="a" * 64,
        tokens_in=120,
        tokens_out=18,
        cost_usd=Decimal("0.0021"),
        cached=False,
        valid=True,
    )
    run_id = uuid4()

    event = call_event(record, run_id=run_id, seq=4, sim_minutes=30, seat="attending")

    assert (event.type, event.source, event.visibility) == ("llm_call", "engine", ())
    assert (event.model, event.prompt_version, event.tokens_in, event.cost_usd) == (
        "vendor/doctor",
        "3",
        120,
        Decimal("0.0021"),
    )
    assert event.payload.model_dump()["request_hash"] == "a" * 64


# --- the spending cap for live runs (P1.9) ---


def test_calls_stop_once_the_spending_cap_is_reached(config: ModelsConfig) -> None:
    from sambhasha.llm.gateway import LLMBudgetExceededError

    fake = FakeLLM({"attending": [VALID] * 3}, cost_usd=Decimal("0.40"))
    gateway = LLMGateway(config, backend_for=lambda e: fake, spend_cap_usd=Decimal("0.75"))

    gateway.structured("attending", MESSAGES, Question, prompt_version="3")
    gateway.structured(
        "attending",
        (*MESSAGES, ChatMessage(role="user", content="again")),
        Question,
        prompt_version="3",
    )
    with pytest.raises(LLMBudgetExceededError, match=r"0\.80"):
        gateway.structured(
            "attending",
            (*MESSAGES, ChatMessage(role="user", content="more")),
            Question,
            prompt_version="3",
        )

    assert gateway.spent_usd == Decimal("0.80")
    assert len(fake.requests) == 2  # the third call was never made


def test_cached_replies_cost_nothing_against_the_cap(config: ModelsConfig, tmp_path: Path) -> None:
    fake = FakeLLM({"attending": [VALID]}, cost_usd=Decimal("0.40"))
    gateway = LLMGateway(
        config,
        backend_for=lambda e: fake,
        cache=RecordReplayCache(tmp_path),
        spend_cap_usd=Decimal("0.50"),
    )

    for _ in range(3):
        gateway.structured("attending", MESSAGES, Question, prompt_version="3")

    assert gateway.spent_usd == Decimal("0.40")
