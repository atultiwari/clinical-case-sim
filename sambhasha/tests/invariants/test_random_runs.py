"""Invariants over random runs of the pilot (PLAN P1.10; SPEC §2).

Hypothesis draws random sequences of Attending actions, from real catalogue items and from
free text, and plays them through the full Scheduler. Every view any seat was shown, and the
whole Event Log, must keep the invariants.
"""

import hashlib
import json
import re
from typing import Final

from hypothesis import given
from hypothesis import strategies as st

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.leakscan import Lexicon, find_leaks
from sambhasha.domain.actions import (
    AskHistory,
    DifferentialItem,
    Examine,
    OrderTest,
    Refer,
    UpdateDifferential,
    Wait,
)
from sambhasha.domain.base import DomainModel
from sambhasha.domain.events import Answer, Event, Result
from sambhasha.domain.views import ServiceView
from sambhasha.engine.scheduler import RunResult
from sambhasha.engine.seats import render_view
from sambhasha.gatekeeper.lookup import fact_text, ledger_text, topics_named
from tests.invariants.harness import CATALOGUE, PILOT, ScriptedSeat, run_scripted

LEXICON: Final = Lexicon.from_bundle(PILOT, CatalogueNames.load())
FACTS: Final = {f.id: f for f in PILOT.facts}
LEDGER: Final = {r.id: r for r in PILOT.ledger}
NAMES: Final = {i.id: i.name for i in CATALOGUE.items}
H10: Final = FACTS["H10"]
CARRIED: Final = re.compile(r" \(result from day -?\d+\)$")
SERVICE_MATERIAL: Final = {m.findings for m in PILOT.raw_material} | {
    r.report_text for r in PILOT.reports if r.report_text
}
LEDGER_TEXTS: Final = {r.release_text or r.value.text for r in PILOT.ledger}

WORDS = [
    "pain",
    "fever",
    "rash",
    "stool",
    "urine",
    "cough",
    "weight",
    "sleep",
    "family",
    "travel",
    "work",
    "alcohol",
    "smoking",
    "supplements",
    "herbal",
    "tablets",
    "toxins",
    "diet",
    "bleeding",
    "vision",
    "numbness",
    "serum",
    "assay",
    "screen",
    "any",
]
SAFE_DIAGNOSES = [
    "Iron deficiency",
    "Warm AIHA",
    "Myelodysplasia",
    "Thalassaemia trait",
    "Anaemia of chronic disease",
]


def _names(kind: str) -> list[str]:
    return sorted({n for i in CATALOGUE.items if i.kind == kind for n in (i.name, *i.synonyms)})


free_text = st.lists(st.sampled_from(WORDS), min_size=1, max_size=5).map(" ".join)
history = st.one_of(st.sampled_from(_names("history")), free_text).map(
    lambda q: AskHistory(question=q)
)
exam = st.one_of(st.sampled_from(_names("exam")), free_text).map(lambda s: Examine(system=s))
order = st.one_of(st.sampled_from(_names("test")), free_text).map(
    lambda t: OrderTest(item=t, indication="work-up")
)
refer = st.sampled_from(["haematology", "clinical toxicology", "neurology", "cardiology"]).map(
    lambda s: Refer(specialty=s, question="Your opinion, please.")
)
differential = st.sampled_from(SAFE_DIAGNOSES).map(
    lambda d: UpdateDifferential(
        items=(
            DifferentialItem(diagnosis=d, probability=0.5, evidence_for=(), evidence_against=()),
        )
    )
)
action = st.one_of(history, history, exam, order, order, refer, st.just(Wait()), differential)
runs = st.lists(action, min_size=1, max_size=14)


def _leak_free(actions: list[DomainModel]) -> bool:
    text = " ".join(json.dumps(a.model_dump(mode="json")) for a in actions)
    return not find_leaks(text, LEXICON)


def _stored(event: Event) -> bool:
    """Every line is the stored text of a fact or ledger row the event names, used once."""
    payload = event.payload
    assert isinstance(payload, Answer | Result)
    expected = [fact_text(FACTS[i]) for i in payload.fact_ids]
    expected += [
        ledger_text(LEDGER[i], NAMES.get(LEDGER[i].target, LEDGER[i].target))
        for i in payload.ledger_ids
    ]
    lines = [CARRIED.sub("", line) for line in payload.text.split("\n")]
    return sorted(lines) == sorted(expected)


def _check(result: RunResult, seats: dict[str, ScriptedSeat]) -> None:
    events = result.events
    # I6: an unbroken, append-only log with a hash chain.
    previous = ""
    for n, event in enumerate(events):
        assert event.seq == n
        body = json.dumps(event.model_dump(mode="json", exclude={"run_id", "hash"}), sort_keys=True)
        previous = hashlib.sha256((previous + body).encode()).hexdigest()
        assert event.hash == previous
        if event.type == "llm_call":
            assert event.visibility == ()
        if event.type == "refusal":
            assert len(event.visibility) == 1
    # I4: whatever the Gatekeeper released is stored text (the intake posts the vignette).
    assert isinstance(events[0].payload, Answer)
    assert events[0].payload.text == PILOT.vignette
    for event in events[1:]:
        if event.seat == "gatekeeper" and event.type in ("answer", "result"):
            assert _stored(event), event
    # The hidden supplement comes out only after a question that names its topic.
    topics = H10.release_condition.requires_topics if H10.release_condition else ()
    questions: list[str] = []
    for event in events:
        if isinstance(event.payload, AskHistory):
            questions.append(event.payload.question)
        if isinstance(event.payload, Answer) and "H10" in event.payload.fact_ids:
            assert any(topics_named(q, topics or ()) for q in questions)
    # I8 and I1: no view holds the ground truth or names the diagnosis.
    truth = PILOT.ground_truth.final_dx.text
    for seat in seats.values():
        for view in seat.views:
            text = render_view(view)
            assert truth not in text
            assert not find_leaks(text, LEXICON), find_leaks(text, LEXICON)
            if isinstance(view, ServiceView):
                assert view.raw_material in SERVICE_MATERIAL or all(
                    line in LEDGER_TEXTS for line in view.raw_material.split("\n")
                ), view.raw_material


@given(runs)
def test_random_runs_keep_every_invariant(actions: list[DomainModel]) -> None:
    if not _leak_free(actions):
        return  # a seat that writes the diagnosis itself is not the Gatekeeper's leak
    result, seats = run_scripted(actions)

    assert result.run.status == "completed"
    _check(result, seats)


@given(runs)
def test_random_runs_repeat_exactly(actions: list[DomainModel]) -> None:
    first, _ = run_scripted(actions)
    second, _ = run_scripted(actions)

    assert first.event_hash == second.event_hash
