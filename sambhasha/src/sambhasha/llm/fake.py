"""A scripted model for tests: fixed replies per role, in order (SPEC §11).

Tests never call a paid API; they give the gateway a FakeLLM instead of a real backend.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from sambhasha.llm.types import LLMRequest, LLMResponse


class FakeScriptExhaustedError(LookupError):
    """The test script has no more replies for this role."""


class FakeLLM:
    def __init__(
        self,
        script: Mapping[str, Sequence[str]],
        *,
        cost_usd: Decimal = Decimal(0),
        tokens: tuple[int, int] = (0, 0),
    ) -> None:
        self._script = {role: tuple(replies) for role, replies in script.items()}
        self._next = dict.fromkeys(self._script, 0)
        self._cost = cost_usd
        self._tokens = tokens
        self._requests: tuple[LLMRequest, ...] = ()

    @property
    def requests(self) -> tuple[LLMRequest, ...]:
        """Every request received, in order."""
        return self._requests

    def complete(self, request: LLMRequest) -> LLMResponse:
        self._requests = (*self._requests, request)
        replies = self._script.get(request.role, ())
        index = self._next.get(request.role, 0)
        if index >= len(replies):
            raise FakeScriptExhaustedError(
                f"the script has no reply {index + 1} for role {request.role!r}"
            )
        self._next[request.role] = index + 1
        return LLMResponse(
            content=replies[index],
            model=request.model,
            tokens_in=self._tokens[0],
            tokens_out=self._tokens[1],
            cost_usd=self._cost,
        )
