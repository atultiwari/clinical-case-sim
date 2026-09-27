"""The Scheduler: runs one case from the vignette to the commit (SPEC §10.1-10.2; I2, I6).

Code, not a model, decides who acts next:

- Intake: the vignette goes onto the Chart.
- Each Attending turn: one action. Questions and examinations go to the Gatekeeper; orders
  are priced and their results recorded at the time they are ready; interpretive orders go
  to the Diagnostic Service, whose report is recorded at the same time; a referral opens a
  Consultant session of a few actions that ends in a consult note; `wait` moves the clock to
  the next pending result.
- The first time the Attending proposes to commit, the Challenger speaks, and the Attending
  then commits or carries on. The Challenger may also speak every N turns.
- The turn and budget limits force a commit.

Every step, model calls included, is appended to the Event Log. Each event carries a hash
chained to the previous one, so the same configuration and the same replies give the same
final hash on a rerun.
"""

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Final
from uuid import UUID, uuid5

from sambhasha import __version__
from sambhasha.catalogue import Catalogue
from sambhasha.domain.actions import (
    AskHistory,
    BedsideTest,
    Challenge,
    Commit,
    ConsultNote,
    Examine,
    OrderTest,
    Refer,
    Report,
    UpdateDifferential,
    Wait,
)
from sambhasha.domain.base import DomainModel
from sambhasha.domain.case_file import CaseBundle
from sambhasha.domain.events import Answer, Event, EventType, Payload, Refusal, Result, Source
from sambhasha.domain.orders import Order, Route
from sambhasha.domain.runs import Run
from sambhasha.domain.views import Limits
from sambhasha.engine.clock import SimClock
from sambhasha.engine.config import RunConfig
from sambhasha.engine.costs import budget_left, place_order, total_cost
from sambhasha.engine.seats import Seat, load_role_card
from sambhasha.engine.tables import Tables
from sambhasha.engine.views import build_seat_view, build_service_view
from sambhasha.gatekeeper.policy import Permissions
from sambhasha.gatekeeper.resolver import (
    Gatekeeper,
    GatekeeperRequest,
    Refused,
    Released,
    ServiceRequest,
)
from sambhasha.llm.gateway import call_event
from sambhasha.llm.types import LlmCallRecord
from sambhasha.storage.repo import Repository
from sambhasha.synthetic.route import respond
from sambhasha.synthetic.service import Generated, SyntheticService

FORCED_COMMIT_ATTEMPTS: Final = 2
_CALL_SEATS: Final = {"matcher": "gatekeeper", "synthetic": "synthetic"}
_ACTION_EVENTS: Final[dict[type, EventType]] = {
    OrderTest: "order",
    UpdateDifferential: "differential",
    Commit: "commit",
    Challenge: "challenge",
    ConsultNote: "consult_note",
    Report: "report",
}
_TEAM: Final = ("team",)


class CallRecorder:
    """Collects the gateway's call records until the Scheduler logs them."""

    def __init__(self) -> None:
        self._pending: tuple[LlmCallRecord, ...] = ()

    def __call__(self, record: LlmCallRecord) -> None:
        self._pending = (*self._pending, record)

    def drain(self) -> tuple[LlmCallRecord, ...]:
        drained, self._pending = self._pending, ()
        return drained


@dataclass(frozen=True)
class RunResult:
    run: Run
    events: tuple[Event, ...]
    commit: Commit | None
    forced_commit: bool
    used_fallback: bool
    event_hash: str


@dataclass
class _State:
    """One run's moving parts. Private to a single `Scheduler.run` call."""

    run_id: UUID
    clock: SimClock = field(default_factory=SimClock)
    events: list[Event] = field(default_factory=list)
    orders: dict[str, Order] = field(default_factory=dict)
    referred: set[str] = field(default_factory=set)
    turns_used: int = 0
    challenged: bool = False
    used_fallback: bool = False
    last_hash: str = ""


class Scheduler:
    def __init__(
        self,
        *,
        config: RunConfig,
        bundle: CaseBundle,
        catalogue: Catalogue,
        repo: Repository,
        gatekeeper: Gatekeeper,
        synthetic: SyntheticService,
        permissions: Permissions,
        tables: Tables,
        seat_for: Callable[[str], Seat],
        recorder: CallRecorder,
        engine_version: str = __version__,
    ) -> None:
        if config.bundle != bundle.bundle_id:
            raise ValueError(f"the config names {config.bundle}, not {bundle.bundle_id}")
        self._config = config
        self._bundle = bundle
        self._catalogue = catalogue
        self._repo = repo
        self._gatekeeper = gatekeeper
        self._synthetic = synthetic
        self._refusals = permissions.refusals
        self._tables = tables
        self._seat_for = seat_for
        self._recorder = recorder
        self._engine_version = engine_version

    # --- the run ---

    def run(self, run_id: UUID, *, started_at: datetime | None = None) -> RunResult:
        run = Run(
            id=run_id,
            bundle_id=self._bundle.bundle_id,
            engine_version=self._engine_version,
            config_hash=self._config.config_hash(),
            started_at=started_at or datetime.now(UTC),
            status="running",
        )
        self._repo.add_run(run)
        state = _State(run_id=run_id)
        self._intake(state)
        commit, forced = self._attending_loop(state)
        finished = self._repo.finish_run(
            run_id, status="completed" if commit else "aborted", ended_at=datetime.now(UTC)
        )
        return RunResult(
            run=finished,
            events=self._repo.events(run_id),
            commit=commit,
            forced_commit=forced,
            used_fallback=state.used_fallback,
            event_hash=state.last_hash,
        )

    def _intake(self, state: _State) -> None:
        vignette_facts = tuple(f.id for f in self._bundle.facts if f.release == "vignette")
        text = self._bundle.vignette or "A new admission."
        self._post(
            state,
            "gatekeeper",
            "answer",
            Answer(text=text, fact_ids=vignette_facts),
            _TEAM,
            "article",
        )

    def _attending_loop(self, state: _State) -> tuple[Commit | None, bool]:
        limits = self._config.limits
        while state.turns_used < limits.attending_turns and not self._over_budget(state):
            action = self._act("attending", state)
            state.turns_used += 1
            commit = self._attending_action(action, state)
            if commit is not None:
                return commit, False
            every = self._config.challenger.every_n_turns
            if every and state.turns_used % every == 0:
                self._challenge(state)
        return self._forced_commit(state), True

    def _attending_action(self, action: DomainModel, state: _State) -> Commit | None:
        match action:
            case Commit() if self._config.challenger.before_commit and not state.challenged:
                self._post_action("attending", action, state)
                self._challenge(state)
                state.challenged = True
            case Commit():
                self._post_action("attending", action, state)
                return action
            case OrderTest():
                self._order(action, state)
            case Refer():
                self._refer(action, state)
            case Wait():
                self._wait(action, state)
            case UpdateDifferential():
                self._post_action("attending", action, state)
            case AskHistory() | Examine():
                self._question("attending", action, state)
            case _:
                self._refuse(
                    state,
                    "attending",
                    self._refusals.not_permitted.format(role="attending", action="do that"),
                )
        return None

    def _forced_commit(self, state: _State) -> Commit | None:
        self._refuse(state, "attending", "Limits reached: commit your diagnosis and plan now.")
        for _attempt in range(FORCED_COMMIT_ATTEMPTS):
            action = self._act("attending", state, turns_left=0)
            if isinstance(action, Commit):
                self._post_action("attending", action, state)
                return action
            self._refuse(state, "attending", "Only a commit is possible now.")
        return None

    # --- steps ---

    def _question(
        self, seat: str, action: AskHistory | Examine | BedsideTest, state: _State
    ) -> None:
        self._post_action(seat, action, state)
        response = respond(
            self._gatekeeper,
            self._synthetic,
            self._request(seat, action, state),
            released=self._released_texts(state),
        )
        self._log_calls(seat, state)
        state.used_fallback |= response.used_fallback
        result = response.result
        match result:
            case Released():
                self._post(
                    state,
                    "gatekeeper",
                    "answer",
                    Answer(
                        text=result.text,
                        fact_ids=result.fact_ids,
                        ledger_ids=result.ledger_ids,
                        item_id=result.item_id,
                    ),
                    _TEAM,
                    "article" if result.fact_ids else "synthetic",
                )
            case Generated():
                self._post(
                    state, "synthetic", "answer", Answer(text=result.text), _TEAM, "synthetic"
                )
            case Refused():
                self._refuse(state, seat, result.reason, violation=result.violation)
            case _:
                self._refuse(state, seat, self._refusals.not_understood)
        key = "bedside_test" if isinstance(action, BedsideTest) else action.action
        state.clock = state.clock.advance(self._tables.turnaround(key))

    def _order(self, action: OrderTest, state: _State) -> None:
        self._post_action("attending", action, state)
        response = respond(
            self._gatekeeper,
            self._synthetic,
            self._request("attending", action, state),
            released=self._released_texts(state),
        )
        self._log_calls("attending", state)
        state.used_fallback |= response.used_fallback
        result = response.result
        match result:
            case Released():
                order = self._place(result.item_id, action, "direct", "resulted", state)
                self._post_result(order, result, state)
            case ServiceRequest():
                route: Route = result.service  # type: ignore[assignment]
                order = self._place(result.item_id, action, route, "reported", state)
                if result.released is not None:
                    self._post_result(order, result.released, state)
                self._service_report(order, result, state)
            case Generated():
                order = self._place(None, action, "direct", "resulted", state)
                self._post(
                    state,
                    "synthetic",
                    "result",
                    Result(order_id=_label(order, state), text=result.text),
                    _TEAM,
                    "synthetic",
                    at=order.due_at_min,
                )
            case Refused():
                self._refuse(state, "attending", result.reason, violation=result.violation)
            case _:
                self._refuse(state, "attending", self._refusals.not_understood)

    def _place(
        self, item_id: str | None, action: OrderTest, route: Route, status: str, state: _State
    ) -> Order:
        label = f"O{len(state.orders) + 1}"
        placed = place_order(
            self._tables,
            run_id=state.run_id,
            item_id=item_id,
            item_text=action.item,
            indication=action.indication,
            route=route,
            clock=state.clock,
        )
        order = placed.model_copy(update={"id": uuid5(state.run_id, label), "status": status})
        state.orders[label] = order
        self._repo.put_order(order)
        return order

    def _post_result(self, order: Order, released: Released, state: _State) -> None:
        self._post(
            state,
            "gatekeeper",
            "result",
            Result(
                order_id=_label(order, state),
                text=released.text,
                fact_ids=released.fact_ids,
                ledger_ids=released.ledger_ids,
                item_id=released.item_id,
            ),
            _TEAM,
            "article" if released.fact_ids else "synthetic",
            at=order.due_at_min,
        )

    def _service_report(self, order: Order, request: ServiceRequest, state: _State) -> None:
        label = _label(order, state)
        view = build_service_view(
            request,
            order_id=label,
            test_name=self._catalogue.get(request.item_id).name,
            role_card=load_role_card(request.service).text,
        )
        report = self._seat_for(request.service).act(view)
        self._log_calls(request.service, state)
        if not isinstance(report, Report):
            self._refuse(state, "attending", f"The {request.service} report was not filed.")
            return
        filed = report.model_copy(update={"order_id": label})
        self._post(state, request.service, "report", filed, _TEAM, "seat", at=order.due_at_min)

    def _refer(self, action: Refer, state: _State) -> None:
        self._post_action("attending", action, state)
        specialty = re.sub(r"[^a-z0-9]+", "_", action.specialty.lower()).strip("_")
        seat = f"consultant.{specialty}"
        if len(state.referred) >= self._config.limits.referrals:
            self._refuse(state, "attending", "No referrals left.")
            return
        if specialty not in self._config.consultants:
            self._refuse(state, "attending", f"No {action.specialty} Consultant is available.")
            return
        state.referred.add(seat)
        self._consultation(seat, state)
        state.clock = state.clock.advance(self._tables.turnaround("consultant_session"))

    def _consultation(self, seat: str, state: _State) -> None:
        allowed = self._config.consultant_session_actions
        for used in range(allowed):
            action = self._act(seat, state, turns_left=allowed - used)
            match action:
                case ConsultNote():
                    self._post_action(seat, action, state)
                    return
                case AskHistory() | Examine() | BedsideTest():
                    self._question(seat, action, state)
                case _:
                    self._refuse(
                        state,
                        seat,
                        self._refusals.not_permitted.format(role="consultant", action="do that"),
                    )
        self._refuse(state, "attending", "The consultation ended without a consult note.")

    def _wait(self, action: Wait, state: _State) -> None:
        self._post_action("attending", action, state)
        pending = [e.sim_minutes for e in state.events if e.sim_minutes > state.clock.minutes]
        if not pending:
            self._refuse(state, "attending", "Nothing is pending.")
            return
        state.clock = SimClock(min(pending))

    def _challenge(self, state: _State) -> None:
        action = self._act("challenger", state)
        if isinstance(action, Challenge):
            self._post_action("challenger", action, state)
        else:
            self._refuse(state, "challenger", "Only a challenge is possible.")

    # --- plumbing ---

    def _act(self, seat: str, state: _State, *, turns_left: int | None = None) -> DomainModel:
        limits = self._config.limits
        view = build_seat_view(
            seat,
            role_card=load_role_card(seat).text,
            events=state.events,
            now=state.clock,
            limits=Limits(
                turns_left=turns_left
                if turns_left is not None
                else max(limits.attending_turns - state.turns_used, 0),
                referrals_left=max(limits.referrals - len(state.referred), 0),
                budget_left_inr=budget_left(limits.budget_inr, state.orders.values()),
                sim_minutes=state.clock.minutes,
            ),
            referred=frozenset(state.referred),
        )
        action = self._seat_for(seat).act(view)
        self._log_calls(seat, state)
        return action

    def _request(
        self, seat: str, action: AskHistory | Examine | BedsideTest | OrderTest, state: _State
    ) -> GatekeeperRequest:
        return GatekeeperRequest(
            seat=seat, action=action, day=state.clock.day, referred=frozenset(state.referred)
        )

    def _over_budget(self, state: _State) -> bool:
        return total_cost(state.orders.values()) >= Decimal(self._config.limits.budget_inr)

    def _released_texts(self, state: _State) -> tuple[str, ...]:
        return tuple(
            e.payload.text  # type: ignore[union-attr]
            for e in state.events
            if e.type in ("answer", "result") and e.sim_minutes <= state.clock.minutes
        )

    def _post_action(self, seat: str, action: DomainModel, state: _State) -> None:
        kind = _ACTION_EVENTS.get(type(action), "request")
        self._post(state, seat, kind, action, _TEAM, "seat")  # type: ignore[arg-type]

    def _refuse(self, state: _State, seat: str, reason: str, *, violation: bool = False) -> None:
        self._post(
            state,
            "gatekeeper",
            "refusal",
            Refusal(reason=reason, violation=violation),
            (seat,),
            "engine",
        )

    def _log_calls(self, seat: str, state: _State) -> None:
        for record in self._recorder.drain():
            caller = _CALL_SEATS.get(record.role, seat)
            event = call_event(
                record,
                run_id=state.run_id,
                seq=len(state.events),
                sim_minutes=state.clock.minutes,
                seat=caller,
            )
            self._append(state, event)

    def _post(
        self,
        state: _State,
        seat: str,
        kind: EventType,
        payload: Payload,
        visibility: tuple[str, ...],
        source: Source,
        *,
        at: int | None = None,
    ) -> None:
        event = Event(
            run_id=state.run_id,
            seq=len(state.events),
            sim_minutes=state.clock.minutes if at is None else at,
            seat=seat,
            type=kind,
            payload=payload,
            visibility=visibility,
            source=source,
        )
        self._append(state, event)

    def _append(self, state: _State, event: Event) -> None:
        body = json.dumps(event.model_dump(mode="json", exclude={"run_id", "hash"}), sort_keys=True)
        digest = hashlib.sha256((state.last_hash + body).encode()).hexdigest()
        hashed = event.model_copy(update={"hash": digest})
        self._repo.append_event(hashed)
        state.events.append(hashed)
        state.last_hash = digest


def _label(order: Order, state: _State) -> str:
    """The short order id seats see ("O2"), which keeps event hashes free of random ids."""
    return next(label for label, placed in state.orders.items() if placed.id == order.id)
