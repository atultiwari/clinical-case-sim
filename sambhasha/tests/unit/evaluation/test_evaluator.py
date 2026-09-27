"""P1.8: the Evaluator on pilot fixtures (SPEC §13; D-014, D-022, D-023)."""

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

import pytest

from sambhasha.catalogue import Catalogue
from sambhasha.domain.actions import (
    AskHistory,
    Commit,
    DifferentialItem,
    OrderTest,
    Refer,
    Report,
)
from sambhasha.domain.case_file import parse_bundle
from sambhasha.domain.events import Answer, Event, Payload, Result, Source
from sambhasha.domain.orders import Order
from sambhasha.domain.runs import Run
from sambhasha.evaluation.evaluator import Evaluator
from sambhasha.evaluation.mapper import ScoringMapper
from sambhasha.gatekeeper.coding import Coder, MissingRequestLog
from sambhasha.llm.config import load_models_config
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
PILOT = parse_bundle((EXPORTS / "PMC12949993@v1.r3.json").read_bytes())
CATALOGUE = Catalogue.load()
RUN_ID = UUID("00000000-0000-4000-8000-000000000002")
RUN = Run(
    id=RUN_ID,
    bundle_id=PILOT.bundle_id,
    engine_version="0.1.0",
    config_hash="c" * 64,
    started_at=datetime(2026, 9, 27, tzinfo=UTC),
    status="completed",
)
GOOD_PLAN = "Stop the supplement; oral succimer with toxicology; notify public health; repeat lead."
GOOD_PLAN_IDS = (
    "ACT.STOP_SUSPECTED_SOURCE",
    "RX.CHELATION.SUCCIMER_ORAL",
    "REF.TOXICOLOGY",
    "ACT.NOTIFY_PUBLIC_HEALTH",
    "ACT.SCREEN_CONTACTS",
    "ACT.REPEAT_BLOOD_LEAD",
)
FILM_REPORT = "Coarse basophilic stippling in a proportion of red cells."


class StubMapper:
    def __init__(
        self,
        diagnoses: Mapping[str, str | None],
        plans: Mapping[str, tuple[str, ...]] | None = None,
        findings: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        self._diagnoses = diagnoses
        self._plans = plans or {GOOD_PLAN: GOOD_PLAN_IDS}
        self._findings = findings or {FILM_REPORT: ("FND.COARSE_BASOPHILIC_STIPPLING",)}

    def diagnosis(self, text: str) -> str | None:
        return self._diagnoses.get(text)

    def plan(self, text: str) -> tuple[str, ...]:
        return self._plans.get(text, ())

    def findings(self, text: str) -> tuple[str, ...]:
        return self._findings.get(text, ())

    def referral(self, specialty: str) -> str | None:
        return {"clinical toxicology": "REF.TOXICOLOGY"}.get(specialty)


def _event(seq: int, seat: str, kind: str, payload: Payload, source: Source, t: int = 0) -> Event:
    return Event(
        run_id=RUN_ID,
        seq=seq,
        sim_minutes=t,
        seat=seat,
        type=kind,
        payload=payload,
        visibility=("team",),
        source=source,
    )


def _order(label: str, code: str, cost: int, at: int) -> Order:
    return Order(
        id=uuid5(RUN_ID, label),
        run_id=RUN_ID,
        ordered_by="attending",
        item_text=code,
        code=code,
        indication="x",
        route="direct",
        status="resulted",
        cost_inr=Decimal(cost),
        ordered_at_min=at,
        due_at_min=at + 240,
    )


def _run_log(
    commit: Commit, report_text: str = FILM_REPORT
) -> tuple[tuple[Event, ...], tuple[Order, ...]]:
    events = (
        _event(0, "gatekeeper", "answer", Answer(text=PILOT.vignette or "v"), "article"),
        _event(1, "attending", "request", AskHistory(question="Any herbal remedies?"), "seat"),
        _event(
            2,
            "gatekeeper",
            "answer",
            Answer(text="Herbal supplement.", fact_ids=("H10",), item_id="HX.MEDS.SUPPLEMENTS"),
            "article",
            5,
        ),
        _event(3, "attending", "order", OrderTest(item="film", indication="x"), "seat", 5),
        _event(
            4,
            "service.pathology",
            "report",
            Report(order_id="O1", report_text=report_text, impression="Toxic?"),
            "seat",
            245,
        ),
        _event(5, "attending", "order", OrderTest(item="blood lead", indication="x"), "seat", 5),
        _event(
            6,
            "gatekeeper",
            "result",
            Result(
                order_id="O2",
                text="Blood lead 77.8",
                fact_ids=("L26",),
                item_id="LAB.TOX.BLOOD_LEAD",
            ),
            "article",
            1445,
        ),
        _event(
            7,
            "attending",
            "request",
            Refer(specialty="clinical toxicology", question="q"),
            "seat",
            10,
        ),
        _event(8, "synthetic", "answer", Answer(text="Serum thallium low."), "synthetic", 20),
        _event(9, "attending", "commit", commit, "seat", 1500),
    )
    orders = (_order("O1", "LAB.HAEM.FILM", 150, 5), _order("O2", "LAB.TOX.BLOOD_LEAD", 1500, 5))
    return events, orders


def _commit(
    diagnosis: str,
    plan: str = GOOD_PLAN,
    evidence: tuple[str, ...] = ("E2", "E6"),
    differential: tuple[DifferentialItem, ...] = (),
) -> Commit:
    return Commit(
        final_diagnosis=diagnosis, differential=differential, treatment_plan=plan, evidence=evidence
    )


def _evaluate(commit: Commit, mapper: Any | None = None, report_text: str = FILM_REPORT) -> Any:
    events, orders = _run_log(commit, report_text)
    mapper = mapper or StubMapper(
        {
            "Lead poisoning from a herbal supplement": "DX.LEAD_POISONING",
            "Lead poisoning": "DX.LEAD_POISONING",
            "Warm AIHA": "DX.WARM_AIHA",
        }
    )
    return Evaluator(PILOT, mapper).evaluate(RUN, events, orders)


# --- the PLAN's acceptance cases ---


def test_lead_poisoning_with_the_supplement_scores_5() -> None:
    evaluation = _evaluate(_commit("Lead poisoning from a herbal supplement"))

    assert evaluation.score.dx_score == 5
    assert evaluation.score.dx_correct is True


def test_lead_poisoning_without_citing_the_supplement_scores_4() -> None:
    evaluation = _evaluate(_commit("Lead poisoning", evidence=("E6",)))

    assert evaluation.score.dx_score == 4


def test_warm_aiha_scores_2() -> None:
    assert _evaluate(_commit("Warm AIHA")).score.dx_score == 2


def test_an_unmapped_diagnosis_gets_the_default_score() -> None:
    assert _evaluate(_commit("Something else entirely")).score.dx_score == 1


def test_a_plan_with_steroid_escalation_violates_a_must_not_do() -> None:
    plan = "High-dose prednisolone and rituximab for warm AIHA."
    mapper = StubMapper(
        {"Warm AIHA": "DX.WARM_AIHA"}, plans={plan: ("RX.STEROID.HIGH_DOSE", "RX.IMMUNO.RITUXIMAB")}
    )

    evaluation = _evaluate(_commit("Warm AIHA", plan=plan), mapper)

    assert evaluation.score.must_not_do_hit == 1
    assert any("immunosuppression" in flag for flag in evaluation.score.safety_flags)


def test_synthetic_dependence_comes_from_the_commit_evidence() -> None:
    all_article = _evaluate(_commit("Lead poisoning", evidence=("E2", "E6")))
    half = _evaluate(_commit("Lead poisoning", evidence=("E2", "E8")))
    none_cited = _evaluate(_commit("Lead poisoning", evidence=()))

    assert all_article.score.synthetic_dependence == 0
    assert half.score.synthetic_dependence == 0.5
    assert none_cited.score.synthetic_dependence is None


def test_the_film_must_do_is_met_when_the_film_report_shows_stippling() -> None:
    evaluation = _evaluate(_commit("Lead poisoning from a herbal supplement"))

    film = next(r for r in evaluation.must_do if "blood film" in r.text)
    assert film.met is True
    assert evaluation.mapping.report_findings == {"O1": ("FND.COARSE_BASOPHILIC_STIPPLING",)}


def test_the_film_must_do_is_not_met_when_the_report_misses_stippling() -> None:
    evaluation = _evaluate(_commit("Lead poisoning"), report_text="Agglutination only.")

    film = next(r for r in evaluation.must_do if "blood film" in r.text)
    assert film.met is False


# --- the rest of the score ---


def test_the_good_plan_meets_every_must_do_and_no_must_not_do() -> None:
    evaluation = _evaluate(_commit("Lead poisoning from a herbal supplement"))

    assert [r.met for r in evaluation.must_do] == [True] * len(PILOT.ground_truth.must_do or ())
    assert evaluation.score.must_do_hit == len(PILOT.ground_truth.must_do or ())
    assert evaluation.score.must_not_do_hit == 0
    assert evaluation.score.safety_flags == ()


def test_process_metrics() -> None:
    score = _evaluate(_commit("Lead poisoning")).score

    assert score.cost_inr == Decimal(1650)
    assert score.sim_hours == 25.0
    assert score.turns == 5
    assert (score.referrals_justified, score.referrals_missed) == (1, 1)  # haematology missed


def test_the_rank_of_the_true_diagnosis_in_the_differential() -> None:
    differential = (
        DifferentialItem(
            diagnosis="Warm AIHA", probability=0.5, evidence_for=(), evidence_against=()
        ),
        DifferentialItem(
            diagnosis="Lead poisoning", probability=0.4, evidence_for=(), evidence_against=()
        ),
    )

    score = _evaluate(_commit("Warm AIHA", differential=differential)).score

    assert (score.dx_rank, score.top1, score.top3) == (2, False, True)


def test_a_run_that_used_the_fallback_is_flagged() -> None:
    events, orders = _run_log(_commit("Lead poisoning"))
    evaluation = Evaluator(PILOT, StubMapper({"Lead poisoning": "DX.LEAD_POISONING"})).evaluate(
        RUN, events, orders, used_fallback=True
    )

    assert evaluation.score.used_fallback is True


def test_the_mapping_is_kept_with_the_score() -> None:
    evaluation = _evaluate(_commit("Lead poisoning from a herbal supplement"))

    assert evaluation.mapping.diagnosis == "DX.LEAD_POISONING"
    assert evaluation.mapping.plan == GOOD_PLAN_IDS
    assert evaluation.mapping.referrals == ("REF.TOXICOLOGY",)
    assert evaluation.score.mapping == evaluation.mapping


def test_a_run_without_a_commit_cannot_be_scored() -> None:
    events, orders = _run_log(_commit("x"))

    with pytest.raises(ValueError, match="no commit"):
        Evaluator(PILOT, StubMapper({})).evaluate(RUN, events[:-1], orders)


# --- the model-backed mapper (D-022), through the fake model ---

MODELS = """
providers:
  local: {base_url: "http://localhost:11434/v1", api_key: ollama}
profiles:
  p: {provider: local, model: m, family: f}
roles: {attending: p, challenger: p, consultant: p, service: p, matcher: p, synthetic: p,
        curator: p, evaluator: p}
family_exception: tests use one scripted model
"""


def test_the_scoring_mapper_uses_the_catalogue_and_the_matcher(tmp_path: Path) -> None:
    models = tmp_path / "models.yaml"
    models.write_text(MODELS, encoding="utf-8")
    fake = FakeLLM(
        {
            "matcher": [
                json.dumps({"item_id": "DX.LEAD_POISONING"}),
                json.dumps(
                    {
                        "items": [
                            "ACT.STOP_SUSPECTED_SOURCE",
                            "RX.NOT_A_REAL_ID",
                            "RX.CHELATION.SUCCIMER_ORAL",
                        ]
                    }
                ),
                json.dumps({"items": ["FND.COARSE_BASOPHILIC_STIPPLING"]}),
            ]
        }
    )
    gateway = LLMGateway(load_models_config(models), backend_for=lambda e: fake)
    mapper = ScoringMapper(CATALOGUE, Coder(CATALOGUE, missing=MissingRequestLog()), gateway)

    assert mapper.diagnosis("Lead poisoning from a herbal supplement") == "DX.LEAD_POISONING"
    assert mapper.plan("Stop it, then succimer.") == (
        "ACT.STOP_SUSPECTED_SOURCE",
        "RX.CHELATION.SUCCIMER_ORAL",
    )
    assert mapper.findings(FILM_REPORT) == ("FND.COARSE_BASOPHILIC_STIPPLING",)
    assert mapper.diagnosis("Warm AIHA") == "DX.WARM_AIHA"  # exact: no model call
    assert mapper.referral("clinical toxicology") == "REF.TOXICOLOGY"
    assert len(fake.requests) == 3
    assert "ACT.STOP_SUSPECTED_SOURCE" in fake.requests[1].messages[-1].content


def test_the_fallback_flag_is_read_from_the_event_log_by_default() -> None:
    # The fixture log holds one answer from the Synthetic Findings Service (E8).
    assert _evaluate(_commit("Lead poisoning")).score.used_fallback is True
