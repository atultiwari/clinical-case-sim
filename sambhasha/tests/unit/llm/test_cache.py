"""P1.1: the record-and-replay cache (SPEC §11: reruns are identical)."""

from pathlib import Path

import pytest

from sambhasha.llm.cache import CacheMiss, RecordReplayCache
from sambhasha.llm.types import ChatMessage, LLMRequest, LLMResponse

REQUEST = LLMRequest(
    model="vendor/model-a",
    messages=(ChatMessage(role="user", content="Hello"),),
    temperature=0,
    seed=1,
    max_tokens=100,
)
RESPONSE = LLMResponse(content='{"ok": true}', model="vendor/model-a", tokens_in=5, tokens_out=3)


def test_a_stored_response_comes_back(tmp_path: Path) -> None:
    cache = RecordReplayCache(tmp_path)
    cache.put(REQUEST, RESPONSE)

    assert cache.get(REQUEST) == RESPONSE


def test_a_different_request_misses(tmp_path: Path) -> None:
    cache = RecordReplayCache(tmp_path)
    cache.put(REQUEST, RESPONSE)
    other = REQUEST.model_copy(update={"temperature": 0.5})

    assert cache.get(other) is None


def test_the_key_is_stable_and_names_the_file(tmp_path: Path) -> None:
    cache = RecordReplayCache(tmp_path)
    cache.put(REQUEST, RESPONSE)

    key = REQUEST.cache_key()
    assert key == REQUEST.model_copy().cache_key()
    assert (tmp_path / key[:2] / f"{key}.json").is_file()


def test_replay_only_refuses_a_miss(tmp_path: Path) -> None:
    cache = RecordReplayCache(tmp_path, replay_only=True)

    with pytest.raises(CacheMiss):
        cache.get(REQUEST)


def test_a_corrupt_entry_is_treated_as_a_miss(tmp_path: Path) -> None:
    cache = RecordReplayCache(tmp_path)
    cache.put(REQUEST, RESPONSE)
    key = REQUEST.cache_key()
    (tmp_path / key[:2] / f"{key}.json").write_text("{not json")

    assert cache.get(REQUEST) is None
