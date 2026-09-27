"""P1.1: the openai-SDK backend, against a stub (no test touches the network)."""

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import openai
import pytest

from sambhasha.llm.backend import LLMCallError, OpenAIBackend
from sambhasha.llm.config import Endpoint
from sambhasha.llm.types import ChatMessage, LLMRequest

REQUEST = LLMRequest(
    role="attending",
    model="vendor/doctor",
    messages=(ChatMessage(role="user", content="Hi"),),
    temperature=0,
    seed=7,
    max_tokens=100,
    response_format='{"type": "json_object"}',
)


def _completion(content: str | None, usage: Any) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=usage
    )


class Recorder:
    def __init__(self, reply: Any) -> None:
        self.reply = reply
        self.kwargs: dict[str, Any] = {}

    def __call__(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def _backend(reports_cost: bool, reply: Any) -> tuple[OpenAIBackend, Recorder]:
    recorder = Recorder(reply)
    endpoint = Endpoint(base_url="https://x.invalid/v1", api_key="k", reports_cost=reports_cost)
    return OpenAIBackend(endpoint, create=recorder), recorder


def test_the_request_is_sent_as_given() -> None:
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=2, cost=0.0004)
    backend, recorder = _backend(True, _completion("{}", usage))

    response = backend.complete(REQUEST)

    assert recorder.kwargs["model"] == "vendor/doctor"
    assert recorder.kwargs["messages"] == [{"role": "user", "content": "Hi"}]
    assert (recorder.kwargs["temperature"], recorder.kwargs["seed"]) == (0, 7)
    assert recorder.kwargs["response_format"] == {"type": "json_object"}
    assert recorder.kwargs["extra_body"] == {"usage": {"include": True}}
    assert (response.tokens_in, response.tokens_out, response.cost_usd) == (
        10,
        2,
        Decimal("0.0004"),
    )


def test_a_local_model_costs_nothing() -> None:
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=2)
    backend, recorder = _backend(False, _completion("{}", usage))

    response = backend.complete(REQUEST)

    assert "extra_body" not in recorder.kwargs
    assert response.cost_usd == Decimal(0)


def test_missing_usage_and_content_are_zero_and_empty() -> None:
    backend, _ = _backend(True, _completion(None, None))

    response = backend.complete(REQUEST)

    assert (response.content, response.tokens_in, response.cost_usd) == ("", 0, None)


def test_an_api_error_is_reported_without_the_key() -> None:
    error = openai.APIConnectionError(request=None)  # type: ignore[arg-type]
    backend, _ = _backend(True, error)

    with pytest.raises(LLMCallError, match="vendor/doctor") as caught:
        backend.complete(REQUEST)

    assert "k" not in str(caught.value).split()


def test_without_a_stub_the_backend_builds_a_real_client_offline() -> None:
    endpoint = Endpoint(base_url="http://localhost:9/v1", api_key="k", reports_cost=False)

    backend = OpenAIBackend(endpoint)  # constructing the client makes no request

    assert isinstance(backend, OpenAIBackend)


def test_the_gateway_default_backend_is_the_openai_one(tmp_path: object) -> None:
    from sambhasha.llm.gateway import LLMGateway
    from sambhasha.runner import fake_models_config

    gateway = LLMGateway(fake_models_config())
    endpoint = Endpoint(base_url="http://localhost:9/v1", api_key="k", reports_cost=False)

    assert isinstance(gateway._backend_for(endpoint), OpenAIBackend)
