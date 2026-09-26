"""The repository contract (SPEC §12; PLAN P0.3). Every implementation must pass all of it."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from sambhasha.domain.actions import AskHistory, OrderTest
from sambhasha.domain.case_file import CaseBundle
from sambhasha.domain.events import Answer, Event
from sambhasha.domain.orders import Order
from sambhasha.domain.runs import Run
from sambhasha.domain.scores import Score
from sambhasha.storage.repo import DuplicateError, NotFoundError, Repository, SequenceError

STARTED = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def _run(bundle_id: str = "PMC12949993@v1.r3") -> Run:
    return Run(
        id=uuid4(),
        bundle_id=bundle_id,
        engine_version="0.1.0",
        config_hash="c" * 64,
        started_at=STARTED,
        status="running",
    )


def _event(run_id: UUID, seq: int) -> Event:
    return Event(
        run_id=run_id,
        seq=seq,
        sim_minutes=seq * 5,
        seat="attending" if seq % 2 == 0 else "gatekeeper",
        type="request" if seq % 2 == 0 else "answer",
        payload=AskHistory(question="Any supplements?")
        if seq % 2 == 0
        else Answer(text="No known toxin exposure.", fact_ids=("H09",)),
        visibility=("team",),
        source="seat" if seq % 2 == 0 else "article",
    )


def _stored(repo: Repository, pilot: CaseBundle, sha256: str) -> Run:
    repo.add_bundle(pilot, sha256)
    run = _run(pilot.bundle_id)
    repo.add_run(run)
    return run


# --- cases ---


def test_a_bundle_round_trips_unchanged(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    repo.add_bundle(pilot, pilot_sha256)

    assert repo.get_bundle(pilot.bundle_id) == pilot


def test_a_bundle_is_recorded_with_its_revision_and_hash(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    repo.add_bundle(pilot, pilot_sha256)

    (record,) = repo.list_bundles()

    assert record.bundle_id == "PMC12949993@v1.r3"
    assert record.case_version_id == "PMC12949993@v1"
    assert record.revision == 3
    assert record.catalogue_version == pilot.catalogue_version
    assert record.sha256 == pilot_sha256


def test_a_bundle_is_imported_once(repo: Repository, pilot: CaseBundle, pilot_sha256: str) -> None:
    repo.add_bundle(pilot, pilot_sha256)

    with pytest.raises(DuplicateError):
        repo.add_bundle(pilot, pilot_sha256)


def test_an_unknown_bundle_is_not_found(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.get_bundle("PMC1@v1.r1")


def test_a_bundle_is_not_eligible_for_primary_results_by_default(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    repo.add_bundle(pilot, pilot_sha256)

    (record,) = repo.list_bundles()

    assert record.primary_eligible is False


def test_eligibility_can_be_recorded_with_a_reason(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    repo.add_bundle(pilot, pilot_sha256)

    repo.set_eligibility(pilot.bundle_id, eligible=True, reason="reviewed item by item")
    repo.set_eligibility(pilot.bundle_id, eligible=False, reason="S-010: development-only")

    (record,) = repo.list_bundles()
    assert record.primary_eligible is False
    assert record.eligibility_reason == "S-010: development-only"


def test_eligibility_needs_a_known_bundle(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.set_eligibility("PMC1@v1.r1", eligible=False, reason="x")


# --- runs and the Event Log ---


def test_a_run_round_trips(repo: Repository, pilot: CaseBundle, pilot_sha256: str) -> None:
    run = _stored(repo, pilot, pilot_sha256)

    assert repo.get_run(run.id) == run


def test_a_run_needs_a_known_bundle(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.add_run(_run("PMC1@v1.r1"))


def test_finishing_a_run_returns_a_new_record(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    ended = datetime(2026, 9, 26, 13, 0, tzinfo=UTC)

    finished = repo.finish_run(run.id, status="completed", ended_at=ended)

    assert finished.status == "completed"
    assert finished.ended_at == ended
    assert run.status == "running"
    assert repo.get_run(run.id) == finished


def test_events_come_back_in_order(repo: Repository, pilot: CaseBundle, pilot_sha256: str) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    events = [_event(run.id, seq) for seq in range(4)]

    for event in events:
        repo.append_event(event)

    assert repo.events(run.id) == tuple(events)


def test_an_event_keeps_its_audit_fields(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    event = _event(run.id, 0).model_copy(
        update={
            "model": "profile.attending",
            "prompt_version": "3",
            "tokens_in": 120,
            "tokens_out": 30,
            "cost_usd": Decimal("0.0012"),
            "hash": "h" * 64,
        }
    )

    repo.append_event(event)

    assert repo.events(run.id) == (event,)


def test_events_must_be_appended_in_sequence(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    repo.append_event(_event(run.id, 0))

    with pytest.raises(SequenceError):
        repo.append_event(_event(run.id, 0))
    with pytest.raises(SequenceError):
        repo.append_event(_event(run.id, 2))


def test_an_event_needs_a_known_run(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.append_event(_event(uuid4(), 0))


def test_every_run_starts_clean(repo: Repository, pilot: CaseBundle, pilot_sha256: str) -> None:
    first = _stored(repo, pilot, pilot_sha256)
    repo.append_event(_event(first.id, 0))
    second = _run(pilot.bundle_id)
    repo.add_run(second)

    assert repo.events(second.id) == ()


# --- orders and scores ---


def _order(run_id: UUID) -> Order:
    return Order(
        id=uuid4(),
        run_id=run_id,
        ordered_by="attending",
        item_text="blood film",
        code="LAB.HAEM.FILM",
        indication="anaemia",
        route="service.pathology",
        status="placed",
        cost_inr=Decimal("150"),
        ordered_at_min=30,
        due_at_min=270,
    )


def test_an_order_is_stored_and_its_status_updated(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    order = _order(run.id)
    repo.put_order(order)

    reported = order.model_copy(update={"status": "reported"})
    repo.put_order(reported)

    assert repo.orders(run.id) == (reported,)


def test_an_order_needs_a_known_run(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.put_order(_order(uuid4()))


def test_scores_are_kept_per_rater(repo: Repository, pilot: CaseBundle, pilot_sha256: str) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    llm = Score(id=uuid4(), run_id=run.id, rater="evaluator", rater_type="llm", dx_score=5)
    human = Score(
        id=uuid4(),
        run_id=run.id,
        rater="atul",
        rater_type="human",
        dx_score=4,
        dx_rank=1,
        plan_rating="appropriate",
        cost_inr=Decimal("2450.50"),
        safety_flags=("steroid escalation",),
        synthetic_dependence=0.25,
    )

    repo.add_score(llm)
    repo.add_score(human)

    assert set(repo.scores(run.id)) == {llm, human}


def test_an_order_placed_before_the_run_is_listed_with_it(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    other = _run(pilot.bundle_id)
    repo.add_run(other)
    repo.put_order(_order(other.id))

    assert repo.orders(run.id) == ()


def test_a_score_needs_a_known_run(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.add_score(Score(id=uuid4(), run_id=uuid4(), rater="x", rater_type="llm", dx_score=1))


def test_finishing_an_unknown_run_is_not_found(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.finish_run(uuid4(), status="aborted", ended_at=STARTED)


def test_an_unknown_run_is_not_found(repo: Repository) -> None:
    with pytest.raises(NotFoundError):
        repo.get_run(uuid4())


def test_a_run_is_created_once(repo: Repository, pilot: CaseBundle, pilot_sha256: str) -> None:
    run = _stored(repo, pilot, pilot_sha256)

    with pytest.raises(DuplicateError):
        repo.add_run(run)


def test_an_order_route_for_a_direct_test(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    order = _order(run.id).model_copy(update={"route": "direct", "code": None})
    repo.put_order(order)

    assert repo.orders(run.id) == (order,)


def test_an_order_event_payload_round_trips(
    repo: Repository, pilot: CaseBundle, pilot_sha256: str
) -> None:
    run = _stored(repo, pilot, pilot_sha256)
    event = Event(
        run_id=run.id,
        seq=0,
        sim_minutes=0,
        seat="attending",
        type="order",
        payload=OrderTest(item="blood lead", indication="anaemia", urgency="urgent"),
        visibility=("team", "consultant.haematology"),
        source="seat",
    )

    repo.append_event(event)

    assert repo.events(run.id) == (event,)
