"""The Evaluator: scores a finished run against its case's ground truth (SPEC §13; D-014).

It maps the run's free text to catalogue ids (D-022), then applies the case's own conditions:
the rubric anchors give the diagnosis score (the first anchor that holds, else the default),
and must-do and must-not-do items are counted. It adds the process metrics, the rank of the
true diagnosis in the final differential, synthetic dependence (the share of the evidence
the commit cited whose source was synthetic) and the fallback flag (D-023). The Evaluator
reads the ground truth; nothing it produces goes back to a seat (I8).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final
from uuid import uuid5

from sambhasha.domain.actions import Commit, Refer, Report
from sambhasha.domain.case_file import CaseBundle
from sambhasha.domain.conditions import ScoredItem
from sambhasha.domain.events import Answer, Event, Result
from sambhasha.domain.orders import Order
from sambhasha.domain.runs import Run
from sambhasha.domain.scores import Score, ScoringMapping
from sambhasha.engine.costs import total_cost
from sambhasha.evaluation.conditions import holds, matches
from sambhasha.evaluation.encounter import Encounter
from sambhasha.evaluation.mapper import Mapper

ATTENDING_ACTIONS: Final = frozenset({"request", "order", "differential", "commit"})
MINUTES_PER_HOUR: Final = 60


@dataclass(frozen=True)
class ItemResult:
    text: str
    met: bool


@dataclass(frozen=True)
class Evaluation:
    score: Score
    mapping: ScoringMapping
    anchor: str | None  # the rubric anchor that set the diagnosis score
    must_do: tuple[ItemResult, ...]
    must_not_do: tuple[ItemResult, ...]
    encounter: Encounter


class Evaluator:
    def __init__(self, bundle: CaseBundle, mapper: Mapper) -> None:
        self._bundle = bundle
        self._mapper = mapper

    def evaluate(
        self,
        run: Run,
        events: Sequence[Event],
        orders: Sequence[Order],
        *,
        rater: str = "evaluator",
        rater_type: str = "llm",
        used_fallback: bool | None = None,
    ) -> Evaluation:
        """Score a run. `used_fallback` defaults to whether the Event Log shows a result from
        the Synthetic Findings Service (D-023)."""
        commit_event = next((e for e in reversed(events) if e.type == "commit"), None)
        if commit_event is None or not isinstance(commit_event.payload, Commit):
            raise ValueError(f"run {run.id} has no commit to score")
        commit = commit_event.payload
        mapping = self._map(commit, events, run, orders)
        encounter = self._encounter(commit, mapping, events, orders, run)
        truth = self._bundle.ground_truth
        score, anchor = self._diagnosis_score(encounter)
        must_do = _judge(truth.must_do or (), encounter)
        must_not = _judge(truth.must_not_do or (), encounter)
        dx_ids = (truth.final_dx.id, *(truth.final_dx.ids or ()))
        rank = next((n for n, dx in enumerate(mapping.differential, start=1) if dx in dx_ids), None)
        justified, missed = self._referrals(encounter)
        result = Score.model_validate(
            {
                "id": uuid5(run.id, f"score:{rater}"),
                "run_id": run.id,
                "rater": rater,
                "rater_type": rater_type,
                "dx_score": score,
                "dx_rank": rank,
                "must_do_hit": sum(r.met for r in must_do),
                "must_not_do_hit": sum(r.met for r in must_not),
                "cost_inr": total_cost(orders),
                "sim_hours": commit_event.sim_minutes / MINUTES_PER_HOUR,
                "turns": sum(
                    1 for e in events if e.seat == "attending" and e.type in ATTENDING_ACTIONS
                ),
                "unnecessary_tests": self._unnecessary(encounter),
                "referrals_justified": justified,
                "referrals_missed": missed,
                "safety_flags": tuple(r.text for r in must_not if r.met),
                "synthetic_dependence": _synthetic_dependence(commit, events),
                "used_fallback": used_fallback
                if used_fallback is not None
                else any(e.seat == "synthetic" and e.type in ("answer", "result") for e in events),
                "mapping": mapping,
            }
        )
        return Evaluation(result, mapping, anchor, must_do, must_not, encounter)

    def _map(
        self, commit: Commit, events: Sequence[Event], run: Run, orders: Sequence[Order]
    ) -> ScoringMapping:
        referrals = tuple(
            ref
            for e in events
            if isinstance(e.payload, Refer) and (ref := self._mapper.referral(e.payload.specialty))
        )
        findings = {
            e.payload.order_id: self._mapper.findings(e.payload.report_text)
            for e in events
            if isinstance(e.payload, Report)
        }
        return ScoringMapping(
            diagnosis=self._mapper.diagnosis(commit.final_diagnosis),
            differential=tuple(self._mapper.diagnosis(i.diagnosis) for i in commit.differential),
            plan=self._mapper.plan(commit.treatment_plan),
            referrals=tuple(dict.fromkeys(referrals)),
            report_findings=findings,
        )

    def _encounter(
        self,
        commit: Commit,
        mapping: ScoringMapping,
        events: Sequence[Event],
        orders: Sequence[Order],
        run: Run,
    ) -> Encounter:
        by_id = {e.event_id: e for e in events}
        cited = [by_id[i] for i in commit.evidence if i in by_id]
        team = [e for e in events if "team" in e.visibility]
        test_of = {o.id: o.code for o in orders}
        return Encounter(
            dx_id=mapping.diagnosis,
            evidence_items=_released(cited),
            released_items=_released(team),
            asked=frozenset(
                e.payload.item_id
                for e in team
                if isinstance(e.payload, Answer) and e.payload.item_id
            ),
            ordered=frozenset(o.code for o in orders if o.code and o.status != "cancelled"),
            referred=frozenset(mapping.referrals),
            plan=mapping.plan,
            findings=tuple(
                (finding, test_of.get(uuid5(run.id, label)))
                for label, ids in mapping.report_findings.items()
                for finding in ids
            ),
        )

    def _diagnosis_score(self, encounter: Encounter) -> tuple[int, str | None]:
        rubric = self._bundle.ground_truth.rubric
        if rubric is None:
            return 1, None
        for anchor in rubric.rubric:
            if holds(anchor.if_, encounter):
                return anchor.score, anchor.text
        return rubric.default_score, None

    def _unnecessary(self, encounter: Encounter) -> int:
        wasted = {
            u.test_item_id
            for u in self._bundle.test_utility
            if u.utility in ("unnecessary", "risky")
        }
        return len(encounter.ordered & wasted)

    def _referrals(self, encounter: Encounter) -> tuple[int, int]:
        efficient = {
            item
            for path in self._bundle.path_analysis
            if path.kind == "efficient"
            for item in path.items
            if item.startswith("REF.")
        }
        justified = sum(1 for ref in encounter.referred if ref in efficient)
        missed = sum(1 for ref in efficient if not any(matches(ref, r) for r in encounter.referred))
        return justified, missed


def _judge(items: Sequence[ScoredItem], encounter: Encounter) -> tuple[ItemResult, ...]:
    return tuple(
        ItemResult(text=item.text, met=item.if_ is not None and holds(item.if_, encounter))
        for item in items
    )


def _released(events: Sequence[Event]) -> frozenset[str]:
    return frozenset(
        item
        for e in events
        if isinstance(e.payload, Answer | Result)
        for item in (*e.payload.fact_ids, *e.payload.ledger_ids)
    )


def _synthetic_dependence(commit: Commit, events: Sequence[Event]) -> float | None:
    by_id = {e.event_id: e for e in events}
    cited = [by_id[i] for i in commit.evidence if i in by_id]
    if not cited:
        return None
    return sum(e.source == "synthetic" for e in cited) / len(cited)
