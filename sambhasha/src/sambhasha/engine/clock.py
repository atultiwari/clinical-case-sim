"""The simulated clock, in minutes from day 0 (SPEC §5.2, §10.4)."""

from dataclasses import dataclass
from typing import Final

MINUTES_PER_DAY: Final = 24 * 60


@dataclass(frozen=True)
class SimClock:
    minutes: int = 0

    @property
    def day(self) -> int:
        return self.minutes // MINUTES_PER_DAY

    def advance(self, minutes: int) -> "SimClock":
        if minutes < 0:
            raise ValueError("the simulated clock never runs backwards")
        return SimClock(self.minutes + minutes)
