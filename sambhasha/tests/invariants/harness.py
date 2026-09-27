"""A harness for the invariant tests: the pilot run by scripted seats that record their views.

Seats play a fixed list of actions and keep every view they are given. The model behind the
Gatekeeper's matcher always chooses the first candidate; the Synthetic Findings Service always
returns the same clean result. Nothing touches the network.
"""

import json
import re
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sambhasha.catalogue import Catalogue
from sambhasha.domain.actions import Challenge, Commit, ConsultNote, Report
from sambhasha.domain.base import DomainModel
from sambhasha.domain.case_file import parse_bundle
from sambhasha.domain.views import SeatView, ServiceView
from sambhasha.engine.config import RunConfig, load_run_config
from sambhasha.engine.scheduler import CallRecorder, RunResult
from sambhasha.gatekeeper.coding import MissingRequestLog
from sambhasha.llm.gateway import LLMGateway
from sambhasha.llm.types import LLMRequest, LLMResponse
from sambhasha.runner import build_scheduler, fake_models_config
from sambhasha.storage.memory import InMemoryRepository

EXPORTS = Path(__file__).resolve().parents[3] / "case-library" / "exports"
PILOT = parse_bundle((EXPORTS / "PMC12949993@v1.r3.json").read_bytes())
CATALOGUE = Catalogue.load()
RUN_ID = UUID("00000000-0000-4000-8000-00000000000a")
SYNTHETIC_TEXT = "Serum trace element screen: within the reference range."
FINAL = Commit(
    final_diagnosis="Undetermined anaemia", differential=(), treatment_plan="Observe.", evidence=()
)


class AlwaysModel:
    """The model behind the matcher and the Synthetic Findings Service in these tests."""

    def complete(self, request: LLMRequest) -> LLMResponse:
        prompt = request.messages[-1].content
        if request.role == "matcher":
            first = re.search(r"^1\. (\S+):", prompt, re.MULTILINE)
            reply: dict[str, Any] = {"item_id": first.group(1) if first else None}
        else:
            reply = {"result_text": SYNTHETIC_TEXT, "rationale": "r", "confidence": 0.5}
        return LLMResponse(content=json.dumps(reply), model=request.model, cost_usd=Decimal(0))


class ScriptedSeat:
    """Plays its actions in order, then a closing action; keeps every view it was shown."""

    def __init__(self, seat_id: str, actions: Sequence[DomainModel], closing: DomainModel) -> None:
        self.seat_id = seat_id
        self._actions = list(actions)
        self._closing = closing
        self.views: list[SeatView | ServiceView] = []

    def act(self, view: SeatView | ServiceView) -> DomainModel:
        self.views.append(view)
        forced = isinstance(view, SeatView) and view.limits.turns_left == 0
        if forced and isinstance(self._closing, Commit):
            return self._closing  # a sensible Attending commits when the limits say so
        if self._actions:
            return self._actions.pop(0)
        if isinstance(view, ServiceView) and isinstance(self._closing, Report):
            return self._closing.model_copy(update={"order_id": view.order_id})
        return self._closing


def run_scripted(
    attending: Sequence[DomainModel],
    *,
    config: RunConfig | None = None,
    consultant: Sequence[DomainModel] = (),
) -> tuple[RunResult, dict[str, ScriptedSeat]]:
    seats: dict[str, ScriptedSeat] = {}

    def seat_for(seat: str) -> ScriptedSeat:
        if seat not in seats:
            if seat == "attending":
                seats[seat] = ScriptedSeat(seat, attending, FINAL)
            elif seat == "challenger":
                seats[seat] = ScriptedSeat(
                    seat, (), Challenge(critique="Consider others.", alternatives=())
                )
            elif seat.startswith("consultant."):
                seats[seat] = ScriptedSeat(
                    seat,
                    consultant,
                    ConsultNote(findings="Seen.", impression="Unclear.", recommendations=()),
                )
            else:
                seats[seat] = ScriptedSeat(
                    seat,
                    (),
                    Report(order_id="?", report_text="Material reviewed.", impression="See text."),
                )
        return seats[seat]

    recorder = CallRecorder()
    repo = InMemoryRepository()
    repo.add_bundle(PILOT, "0" * 64)
    scheduler = build_scheduler(
        config=config or load_run_config(),
        bundle=PILOT,
        repo=repo,
        gateway=LLMGateway(
            fake_models_config(), backend_for=lambda e: AlwaysModel(), on_call=recorder
        ),
        recorder=recorder,
        missing=MissingRequestLog(),
        catalogue=CATALOGUE,
        seat_for=seat_for,
    )
    return scheduler.run(RUN_ID), seats
