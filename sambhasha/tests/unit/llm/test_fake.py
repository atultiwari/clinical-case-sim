"""P1.1: the scripted FakeLLM that every test uses instead of a paid API."""

import pytest

from sambhasha.llm.fake import FakeLLM, FakeScriptExhaustedError
from sambhasha.llm.types import ChatMessage, LLMRequest


def _request(role: str) -> LLMRequest:
    return LLMRequest(
        role=role, model="m", messages=(ChatMessage(role="user", content="x"),), max_tokens=10
    )


def test_replies_follow_each_roles_script_in_order() -> None:
    fake = FakeLLM({"attending": ["a1", "a2"], "challenger": ["c1"]})

    replies = [fake.complete(_request(r)).content for r in ("attending", "challenger", "attending")]

    assert replies == ["a1", "c1", "a2"]
    assert [r.role for r in fake.requests] == ["attending", "challenger", "attending"]


def test_an_exhausted_script_is_an_error_naming_the_role() -> None:
    fake = FakeLLM({"attending": ["a1"]})
    fake.complete(_request("attending"))

    with pytest.raises(FakeScriptExhaustedError, match="attending"):
        fake.complete(_request("attending"))
