"""P1.11 preparation: pacing to the free tier's rate limits, and counting the time waited."""

from types import SimpleNamespace
from typing import Any

import httpx
import openai
import pytest

from sambhasha.llm.backend import OpenAIBackend
from sambhasha.llm.config import Endpoint
from sambhasha.llm.ratelimit import DailyQuotaError, RateLimiter, WaitLedger, retry_delay
from sambhasha.llm.types import ChatMessage, LLMRequest

REQUEST = LLMRequest(
    role="attending",
    model="gemini-3.8-flash",
    messages=(ChatMessage(role="user", content="Hi"),),
    max_tokens=10,
)


class FakeTime:
    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def _limiter(rpm: int | None, rpd: int | None = None) -> tuple[RateLimiter, WaitLedger, FakeTime]:
    time = FakeTime()
    ledger = WaitLedger()
    return (
        RateLimiter(rpm, rpd, model="m", ledger=ledger, clock=time.clock, sleep=time.sleep),
        ledger,
        time,
    )


def test_requests_within_the_limit_do_not_wait() -> None:
    limiter, ledger, time = _limiter(rpm=10)

    for _ in range(10):
        limiter.acquire()

    assert time.slept == []
    assert ledger.total_seconds == 0


def test_the_request_over_the_limit_waits_for_the_window() -> None:
    limiter, ledger, time = _limiter(rpm=10)
    for _ in range(10):
        limiter.acquire()
        time.now += 1  # one request a second

    limiter.acquire()

    assert time.slept == [pytest.approx(50.5)]  # until the first request is a minute old
    assert ledger.total_seconds == pytest.approx(50.5)
    assert ledger.pauses == 1
    assert ledger.by_reason() == {"pacing": pytest.approx(50.5)}


def test_the_daily_quota_stops_requests() -> None:
    limiter, _, _ = _limiter(rpm=None, rpd=2)
    limiter.acquire()
    limiter.acquire()

    with pytest.raises(DailyQuotaError, match="daily"):
        limiter.acquire()


def test_no_limits_means_no_waiting() -> None:
    limiter, ledger, _ = _limiter(rpm=None)

    for _ in range(100):
        limiter.acquire()

    assert ledger.total_seconds == 0


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"error": {"details": [{"retryDelay": "31s"}]}}', 31.0),
        ("'retryDelay': '7.5s'", 7.5),
        ("no hint here", None),
    ],
)
def test_the_retry_delay_is_read_from_the_error(text: str, expected: float | None) -> None:
    assert retry_delay(text) == expected


def test_the_ledger_summarises_in_minutes() -> None:
    ledger = WaitLedger()
    ledger.add("gemini-3.8-flash", 90, "pacing")
    ledger.add("gemini-3.5-flash-lite", 45.5, "rate limited")

    assert ledger.summary() == {
        "waited_seconds": 135.5,
        "pauses": 2,
        "by_model": {"gemini-3.8-flash": 90.0, "gemini-3.5-flash-lite": 45.5},
        "by_reason": {"pacing": 90.0, "rate limited": 45.5},
    }
    assert WaitLedger.describe(135.5) == "2 min 16 s"


# --- the backend: waits, retries after a 429, stops on the daily quota ---


def _rate_error(body: str) -> openai.RateLimitError:
    request = httpx.Request("POST", "https://example.invalid")
    response = httpx.Response(429, request=request, text=body)
    return openai.RateLimitError(body, response=response, body=None)


class Flaky:
    def __init__(self, errors: list[Exception]) -> None:
        self.errors = errors
        self.calls = 0

    def __call__(self, **kwargs: Any) -> Any:
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))], usage=None
        )


def _backend(errors: list[Exception]) -> tuple[OpenAIBackend, Flaky, WaitLedger, FakeTime]:
    time = FakeTime()
    ledger = WaitLedger()
    flaky = Flaky(errors)
    endpoint = Endpoint(
        base_url="https://x.invalid",
        api_key="k",
        reports_cost=False,
        model="gemini-3.8-flash",
        rpm=10,
        rpd=250,
        sdk_retries=0,
    )
    backend = OpenAIBackend(
        endpoint, create=flaky, ledger=ledger, clock=time.clock, sleep=time.sleep
    )
    return backend, flaky, ledger, time


def test_a_429_waits_the_delay_google_gives_and_retries() -> None:
    backend, flaky, ledger, _ = _backend([_rate_error('{"retryDelay": "12s"}')])

    backend.complete(REQUEST)

    assert flaky.calls == 2
    assert ledger.by_reason() == {"rate limited": 12.0}


def test_a_429_without_a_hint_backs_off() -> None:
    backend, flaky, ledger, _ = _backend([_rate_error("slow down"), _rate_error("slow down")])

    backend.complete(REQUEST)

    assert flaky.calls == 3
    assert ledger.by_reason()["rate limited"] == pytest.approx(15 + 30)


def test_a_used_up_daily_quota_stops_at_once() -> None:
    error = _rate_error('quotaId: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"')
    backend, flaky, _, _ = _backend([error])

    with pytest.raises(DailyQuotaError, match="midnight Pacific"):
        backend.complete(REQUEST)
    assert flaky.calls == 1


def test_too_many_429s_give_up() -> None:
    from sambhasha.llm.backend import LLMCallError

    backend, _, _, _ = _backend([_rate_error('{"retryDelay": "1s"}')] * 10)

    with pytest.raises(LLMCallError, match="rate limited"):
        backend.complete(REQUEST)


def _server_error() -> openai.InternalServerError:
    request = httpx.Request("POST", "https://example.invalid")
    return openai.InternalServerError(
        "oops", response=httpx.Response(500, request=request), body=None
    )


def test_a_temporary_server_error_is_retried_after_a_pause() -> None:
    backend, flaky, ledger, _ = _backend([_server_error(), _server_error()])

    backend.complete(REQUEST)

    assert flaky.calls == 3
    assert ledger.by_reason() == {"server error": pytest.approx(5 + 10)}


def test_a_server_that_keeps_failing_gives_up() -> None:
    from sambhasha.llm.backend import LLMCallError

    backend, _, _, _ = _backend([_server_error()] * 10)

    with pytest.raises(LLMCallError, match="InternalServerError"):
        backend.complete(REQUEST)
