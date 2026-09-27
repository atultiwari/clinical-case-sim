"""P1.5: the Chart and what each seat sees (SPEC §5.5; invariants I3 and I8)."""

from decimal import Decimal
from uuid import uuid4

from sambhasha.domain.actions import AskHistory, OrderTest, Refer, Report
from sambhasha.domain.events import Answer, Event, Refusal, Result
from sambhasha.domain.views import Limits
from sambhasha.engine.chart import chart_entries
from sambhasha.engine.clock import SimClock
from sambhasha.engine.views import build_seat_view, build_service_view
from sambhasha.gatekeeper.resolver import ServiceRequest

RUN = uuid4()
LIMITS = Limits(turns_left=30, referrals_left=4, budget_left_inr=Decimal(5000), sim_minutes=0)


def _events() -> tuple[Event, ...]:
    rows = [
        ("attending", "request", AskHistory(question="Any supplements?"), ("team",), "seat", 0),
        (
            "gatekeeper",
            "answer",
            Answer(text="Herbal supplement from a friend."),
            ("team",),
            "article",
            5,
        ),
        ("attending", "order", OrderTest(item="blood lead", indication="x"), ("team",), "seat", 10),
        (
            "gatekeeper",
            "result",
            Result(order_id="O1", text="Blood lead 77.8 ug/dL"),
            ("team",),
            "article",
            1450,
        ),
        (
            "attending",
            "request",
            Refer(specialty="toxicology", question="Why?"),
            ("team",),
            "seat",
            20,
        ),
        (
            "gatekeeper",
            "refusal",
            Refusal(reason="Ask for one specific item."),
            ("attending",),
            "engine",
            25,
        ),
        (
            "service.pathology",
            "report",
            Report(order_id="O2", report_text="Coarse stippling.", impression="Toxic"),
            ("team",),
            "seat",
            30,
        ),
    ]
    return tuple(
        Event(
            run_id=RUN,
            seq=n,
            sim_minutes=t,
            seat=seat,
            type=kind,
            payload=payload,
            visibility=vis,
            source=source,
        )
        for n, (seat, kind, payload, vis, source, t) in enumerate(rows)
    )


def test_a_result_is_visible_only_after_its_turnaround() -> None:
    before = chart_entries(_events(), viewer="attending", now=SimClock(minutes=1449))
    after = chart_entries(_events(), viewer="attending", now=SimClock(minutes=1450))

    assert "E3" not in [e.event_id for e in before]
    assert "E3" in [e.event_id for e in after]


def test_entries_carry_readable_text_and_no_source() -> None:
    entries = chart_entries(_events(), viewer="attending", now=SimClock(minutes=2000))
    by_id = {e.event_id: e for e in entries}

    assert by_id["E0"].text == "Any supplements?"
    assert by_id["E1"].text == "Herbal supplement from a friend."
    assert by_id["E2"].text.startswith("Order: blood lead")
    assert by_id["E6"].text == "Coarse stippling.\nImpression: Toxic"
    assert all(not hasattr(e, "source") for e in entries)


def test_an_entry_for_one_seat_is_seen_by_that_seat_only() -> None:
    attending = chart_entries(_events(), viewer="attending", now=SimClock(minutes=2000))
    challenger = chart_entries(_events(), viewer="challenger", now=SimClock(minutes=2000))

    assert "E5" in [e.event_id for e in attending]
    assert "E5" not in [e.event_id for e in challenger]


def test_the_attending_view_has_the_chart_and_its_own_notes() -> None:
    view = build_seat_view(
        "attending",
        role_card="You lead.",
        events=_events(),
        now=SimClock(minutes=2000),
        limits=LIMITS,
        referred=frozenset(),
    )

    assert len(view.chart) == 7
    assert [e.event_id for e in view.own_notes] == ["E0", "E2", "E4"]


def test_a_consultant_sees_the_chart_only_after_referral() -> None:
    kwargs = {
        "role_card": "You advise.",
        "events": _events(),
        "now": SimClock(minutes=2000),
        "limits": LIMITS,
    }

    before = build_seat_view("consultant.toxicology", referred=frozenset(), **kwargs)  # type: ignore[arg-type]
    after = build_seat_view(
        "consultant.toxicology",
        referred=frozenset({"consultant.toxicology"}),
        **kwargs,  # type: ignore[arg-type]
    )

    assert before.chart == ()
    assert len(after.chart) == 6  # everything the team sees, not the Attending's own refusal


def test_a_service_view_holds_only_its_order_and_raw_material() -> None:
    request = ServiceRequest(
        item_id="LAB.HAEM.FILM",
        service="service.pathology",
        clinical_details="anaemia",
        findings="Coarse basophilic stippling.",
        raw_material_id="R01",
        media=("M01",),
    )

    view = build_service_view(
        request, order_id="O2", test_name="Blood film", role_card="You report."
    )

    assert view.model_dump() == {
        "seat_id": "service.pathology",
        "role_card": "You report.",
        "order_id": "O2",
        "test": "Blood film",
        "clinical_details": "anaemia",
        "raw_material": "Coarse basophilic stippling.",
        "media": ("M01",),
    }


def test_the_limits_show_the_clock() -> None:
    view = build_seat_view(
        "attending",
        role_card="You lead.",
        events=(),
        now=SimClock(minutes=90),
        limits=LIMITS,
        referred=frozenset(),
    )

    assert view.limits.sim_minutes == 90


def test_every_kind_of_event_renders_as_text() -> None:
    from sambhasha.domain.actions import (
        BedsideTest,
        Challenge,
        Commit,
        ConsultNote,
        DifferentialItem,
        Examine,
        UpdateDifferential,
    )
    from sambhasha.domain.events import LlmCall
    from sambhasha.engine.chart import render

    item = DifferentialItem(diagnosis="AIHA", probability=0.4, evidence_for=(), evidence_against=())
    assert render(Examine(system="mouth", manoeuvre="gums")) == "Examination: mouth (gums)"
    assert render(Examine(system="abdomen")) == "Examination: abdomen"
    assert render(BedsideTest(test="dipstick")) == "Bedside test: dipstick"
    assert (
        render(ConsultNote(findings="Pale", impression="Anaemia", recommendations=("blood lead",)))
        == "Findings: Pale\nImpression: Anaemia\nRecommendations: blood lead"
    )
    assert render(ConsultNote(findings="F", impression="I", recommendations=())) == (
        "Findings: F\nImpression: I"
    )
    assert (
        render(
            Report(order_id="O", report_text="T", impression="I", suggested_reflex_tests=("ZPP",))
        )
        == "T\nImpression: I\nSuggested tests: ZPP"
    )
    assert render(UpdateDifferential(items=(item,))) == "Differential: AIHA (40%)"
    assert render(Challenge(critique="Anchoring", alternatives=("toxin",))) == (
        "Anchoring\nAlternatives: toxin"
    )
    assert render(Challenge(critique="Anchoring", alternatives=())) == "Anchoring"
    assert (
        render(Commit(final_diagnosis="X", differential=(), treatment_plan="Y", evidence=()))
        == "Final diagnosis: X\nPlan: Y"
    )
    assert render(LlmCall(role="attending", request_hash="h")) == ""


def test_model_calls_are_never_on_the_chart() -> None:
    from sambhasha.domain.events import LlmCall

    call = Event(
        run_id=RUN,
        seq=0,
        sim_minutes=0,
        seat="attending",
        type="llm_call",
        payload=LlmCall(role="attending", request_hash="h"),
        visibility=("team",),
        source="engine",
    )

    assert chart_entries((call,), viewer="attending", now=SimClock(minutes=10)) == ()
