"""The Chart: the events a seat may see, as of the simulated time (SPEC §5.5, §12).

An event is on a seat's Chart when its time has come (results are recorded at the time they
are ready, so a result appears only after its turnaround) and its visibility names the team
or that seat. Model calls are never shown, and neither is an event's source (I8).
"""

from collections.abc import Iterable

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
)
from sambhasha.domain.events import Answer, Event, Payload, Refusal, Result
from sambhasha.domain.seats import is_consultant
from sambhasha.domain.views import ChartEntry
from sambhasha.engine.clock import SimClock


def visible_to(event: Event, viewer: str) -> bool:
    if event.type == "llm_call":
        return False
    return viewer in event.visibility or "team" in event.visibility


def chart_entries(events: Iterable[Event], *, viewer: str, now: SimClock) -> tuple[ChartEntry, ...]:
    return tuple(
        ChartEntry(
            event_id=e.event_id,
            sim_minutes=e.sim_minutes,
            seat=e.seat,
            type=e.type,
            text=render(e.payload),
        )
        for e in sorted(events, key=lambda e: (e.sim_minutes, e.seq))
        if e.sim_minutes <= now.minutes and visible_to(e, viewer)
    )


def render(payload: Payload) -> str:
    """The text a seat reads for an event."""
    match payload:
        case AskHistory(question=question):
            return question
        case Examine(system=system, manoeuvre=manoeuvre):
            return f"Examination: {system}" + (f" ({manoeuvre})" if manoeuvre else "")
        case BedsideTest(test=test):
            return f"Bedside test: {test}"
        case OrderTest(item=item, indication=indication, urgency=urgency):
            return f"Order: {item} ({urgency}). Clinical details: {indication}"
        case Refer(specialty=specialty, question=question):
            return f"Referral to {specialty}: {question}"
        case ConsultNote(findings=findings, impression=impression, recommendations=recs):
            text = f"Findings: {findings}\nImpression: {impression}"
            return text + (f"\nRecommendations: {'; '.join(recs)}" if recs else "")
        case Report(report_text=text, impression=impression, suggested_reflex_tests=reflex):
            out = f"{text}\nImpression: {impression}"
            return out + (f"\nSuggested tests: {'; '.join(reflex)}" if reflex else "")
        case UpdateDifferential(items=items):
            return "Differential: " + "; ".join(
                f"{i.diagnosis} ({i.probability:.0%})" for i in items
            )
        case Challenge(critique=critique, alternatives=alternatives):
            return critique + (f"\nAlternatives: {'; '.join(alternatives)}" if alternatives else "")
        case Commit(final_diagnosis=diagnosis, treatment_plan=plan):
            return f"Final diagnosis: {diagnosis}\nPlan: {plan}"
        case Answer(text=text) | Result(text=text):
            return text
        case Refusal(reason=reason):
            return reason
    return ""


def referral_needed(seat: str, referred: frozenset[str]) -> bool:
    return is_consultant(seat) and seat not in referred
