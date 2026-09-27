"""Pacing to a provider's rate limits, and counting every second spent waiting (P1.11).

The pilot runs on the free Gemini API, which limits requests per minute (RPM) and per day
(RPD) for each model. The limiter spaces requests so that no more than `rpm` fall within any
60 seconds, and refuses a request beyond `rpd` for the day. Every wait, whether pacing or
backing off after a 429, goes into the WaitLedger, so a run can report how much time a paid
tier would have saved.
"""

import re
import time as _time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Final

WINDOW_SECONDS: Final = 60.0
MARGIN_SECONDS: Final = 0.5  # a little extra, so a request lands just after the window
_RETRY_DELAY: Final = re.compile(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s")


class DailyQuotaError(RuntimeError):
    """The model's requests for today are used up."""


def retry_delay(text: str) -> float | None:
    """The delay a provider asked for in a 429 error, in seconds, if it gave one."""
    match = _RETRY_DELAY.search(text)
    return float(match.group(1)) if match else None


@dataclass
class WaitLedger:
    """Every pause, by model and reason. Shared by all the backends of one run."""

    _pauses: list[tuple[str, float, str]] = field(default_factory=list)

    def add(self, model: str, seconds: float, reason: str) -> None:
        if seconds > 0:
            self._pauses.append((model, float(seconds), reason))

    @property
    def total_seconds(self) -> float:
        return sum(seconds for _, seconds, _ in self._pauses)

    @property
    def pauses(self) -> int:
        return len(self._pauses)

    def by_reason(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for _, seconds, reason in self._pauses:
            totals[reason] = totals.get(reason, 0.0) + seconds
        return totals

    def by_model(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for model, seconds, _ in self._pauses:
            totals[model] = totals.get(model, 0.0) + seconds
        return totals

    def summary(self) -> dict[str, object]:
        return {
            "waited_seconds": round(self.total_seconds, 1),
            "pauses": self.pauses,
            "by_model": {k: round(v, 1) for k, v in self.by_model().items()},
            "by_reason": {k: round(v, 1) for k, v in self.by_reason().items()},
        }

    @staticmethod
    def describe(seconds: float) -> str:
        whole = round(seconds)
        hours, rest = divmod(whole, 3600)
        minutes, secs = divmod(rest, 60)
        parts = [f"{hours} h"] if hours else []
        return " ".join([*parts, f"{minutes} min", f"{secs} s"])


class RateLimiter:
    def __init__(
        self,
        rpm: int | None,
        rpd: int | None,
        *,
        model: str,
        ledger: WaitLedger,
        clock: Callable[[], float] = _time.monotonic,
        sleep: Callable[[float], None] = _time.sleep,
    ) -> None:
        self._rpm = rpm
        self._rpd = rpd
        self._model = model
        self._ledger = ledger
        self._clock = clock
        self._sleep = sleep
        self._recent: deque[float] = deque()
        self._today = 0

    def acquire(self) -> None:
        """Wait until a request is allowed, then count it."""
        if self._rpd is not None and self._today >= self._rpd:
            raise DailyQuotaError(
                f"{self._model}: the daily quota of {self._rpd} requests is used up; it resets"
                " at midnight Pacific time"
            )
        if self._rpm is not None:
            self._drop_old()
            if len(self._recent) >= self._rpm:
                wait = WINDOW_SECONDS - (self._clock() - self._recent[0]) + MARGIN_SECONDS
                self.pause(wait, "pacing")
                self._drop_old()
        self._recent.append(self._clock())
        self._today += 1

    def pause(self, seconds: float, reason: str) -> None:
        if seconds > 0:
            self._sleep(seconds)
            self._ledger.add(self._model, seconds, reason)

    def _drop_old(self) -> None:
        now = self._clock()
        while self._recent and now - self._recent[0] >= WINDOW_SECONDS:
            self._recent.popleft()
