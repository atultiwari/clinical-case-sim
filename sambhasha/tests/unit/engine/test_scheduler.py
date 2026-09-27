"""P1.7: the Scheduler runs the pilot with the scripted fake model (SPEC §10; I2, I6)."""

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from sambhasha.catalogue import Catalogue
from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.domain.actions import Commit
from sambhasha.domain.case_file import parse_bundle
from sambhasha.domain.events import Answer, Event, Refusal, Result
from sambhasha.engine.config import RunConfig, load_run_config
from sambhasha.engine.scheduler import CallRecorder, RunResult, Scheduler
from sambhasha.engine.seats import LLMSeat
from sambhasha.engine.tables import load_tables
from sambhasha.gatekeeper.coding import Coder, MissingRequestLog
from sambhasha.gatekeeper.matcher import LLMMatcher
from sambhasha.gatekeeper.policy import load_permissions
from sambhasha.gatekeeper.resolver import Gatekeeper
from sambhasha.llm.config import load_models_config
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway
from sambhasha.storage.memory import InMemoryRepository
from sambhasha.storage.repo import Repository
from sambhasha.synthetic.service import SyntheticService

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
PILOT = parse_bundle((EXPORTS / "PMC12949993@v1.r3.json").read_bytes())
CATALOGUE = Catalogue.load()
NAMES = CatalogueNames.load()
RUN_ID = UUID("00000000-0000-4000-8000-000000000001")
MODELS = """
providers:
  local: {base_url: "http://localhost:11434/v1", api_key: ollama}
profiles:
  p: {provider: local, model: m, family: f}
roles: {attending: p, challenger: p, consultant: p, service: p, matcher: p, synthetic: p,
        curator: p, evaluator: p}
"""


def turn(**action: Any) -> str:
    return json.dumps({"turn": action})


COMMIT = {
    "action": "commit",
    "final_diagnosis": "Lead poisoning from a herbal supplement",
    "differential": [],
    "treatment_plan": "Stop the supplement; chelation; notify public health.",
    "evidence": ["E2"],
}
EFFICIENT_PATH: dict[str, list[str]] = {
    "attending": [
        turn(action="ask_history", question="Do you take any herbal or dietary supplements?"),
        turn(action="order_test", item="peripheral blood film", indication="anaemia; weak DAT"),
        turn(action="order_test", item="blood lead", indication="stippling; supplement"),
        turn(action="refer", specialty="clinical toxicology", question="Lead exposure?"),
        turn(action="wait", reason="blood lead pending"),
        turn(
            action="update_differential",
            items=[
                {
                    "diagnosis": "Lead poisoning",
                    "probability": 0.8,
                    "evidence_for": ["E2"],
                    "evidence_against": [],
                },
                {
                    "diagnosis": "Warm AIHA",
                    "probability": 0.1,
                    "evidence_for": [],
                    "evidence_against": ["E2"],
                },
            ],
        ),
        turn(**COMMIT),
        turn(**COMMIT),
    ],
    "matcher": [json.dumps({"item_id": "HX.MEDS.SUPPLEMENTS"})],
    "service": [
        turn(
            action="report",
            order_id="x",
            report_text="Coarse basophilic stippling.",
            impression="Suggests a toxic cause; blood lead advised.",
        )
    ],
    "consultant": [
        turn(
            action="consult_note",
            findings="History of an unlabelled supplement.",
            impression="Likely lead toxicity from the supplement.",
            recommendations=["Stop the supplement", "Chelation"],
        )
    ],
    "challenger": [
        turn(
            action="challenge",
            critique="Exclude warm AIHA and MDS.",
            alternatives=["warm AIHA", "MDS with ring sideroblasts"],
        )
    ],
}


def _run(
    script: Mapping[str, Sequence[str]],
    tmp_path: Path,
    config: RunConfig | None = None,
    repo: Repository | None = None,
) -> tuple[RunResult, FakeLLM]:
    models = tmp_path / "models.yaml"
    models.write_text(MODELS, encoding="utf-8")
    fake = FakeLLM(script)
    recorder = CallRecorder()
    gateway = LLMGateway(load_models_config(models), backend_for=lambda e: fake, on_call=recorder)
    repo = repo or InMemoryRepository()
    repo.add_bundle(PILOT, "0" * 64)
    permissions = load_permissions()
    scheduler = Scheduler(
        config=config or load_run_config(),
        bundle=PILOT,
        catalogue=CATALOGUE,
        repo=repo,
        gatekeeper=Gatekeeper(
            PILOT,
            CATALOGUE,
            coder=Coder(CATALOGUE, missing=MissingRequestLog()),
            matcher=LLMMatcher(gateway),
            permissions=permissions,
        ),
        synthetic=SyntheticService(PILOT, repo, gateway, NAMES),
        permissions=permissions,
        tables=load_tables(),
        seat_for=lambda seat: LLMSeat(seat, gateway),
        recorder=recorder,
    )
    return scheduler.run(RUN_ID), fake


def _reasons(result: RunResult) -> list[str]:
    return [e.payload.reason for e in result.events if isinstance(e.payload, Refusal)]


def _types(result: RunResult) -> list[str]:
    return [e.type for e in result.events if e.type != "llm_call"]


def _config(**changes: Any) -> RunConfig:
    data = load_run_config().model_dump()
    for key, value in changes.items():
        data[key] = {**data[key], **value} if isinstance(value, dict) else value
    return RunConfig.model_validate(data)


# --- the PLAN's acceptance cases ---


def test_the_efficient_path_gives_the_expected_sequence(tmp_path: Path) -> None:
    result, fake = _run(EFFICIENT_PATH, tmp_path)

    assert _types(result) == [
        "answer",  # the vignette
        "request",
        "answer",  # supplements: H10
        "order",
        "report",  # blood film, reported by Pathology
        "order",
        "result",  # blood lead
        "request",
        "consult_note",  # referral to clinical toxicology
        "request",  # wait
        "differential",
        "commit",
        "challenge",  # proposal, then the Challenger
        "commit",  # confirmed
    ]
    assert result.commit is not None
    assert result.commit.final_diagnosis.startswith("Lead poisoning")
    assert (result.forced_commit, result.used_fallback) == (False, False)
    assert result.run.status == "completed"
    assert len([e for e in result.events if e.type == "llm_call"]) == len(fake.requests)


def test_the_efficient_path_releases_the_right_facts_at_the_right_times(tmp_path: Path) -> None:
    result, _ = _run(EFFICIENT_PATH, tmp_path)
    by_type: dict[str, list[Event]] = {}
    for event in result.events:
        by_type.setdefault(event.type, []).append(event)

    supplement = by_type["answer"][1].payload
    lead = by_type["result"][0]
    report = by_type["report"][0]
    assert isinstance(supplement, Answer)
    assert supplement.fact_ids == ("H10",)
    assert isinstance(lead.payload, Result)
    assert "77.8" in lead.payload.text
    assert lead.sim_minutes == 5 + 1440  # ordered after the 5-minute history question
    assert report.sim_minutes == 5 + 240
    assert report.payload.model_dump()["order_id"] == "O1"
    wait_done = next(e for e in result.events if e.type == "differential")
    assert wait_done.sim_minutes == lead.sim_minutes  # the wait moved the clock to the result


def test_a_rerun_gives_an_identical_event_hash(tmp_path: Path) -> None:
    first, _ = _run(EFFICIENT_PATH, tmp_path)
    second, _ = _run(EFFICIENT_PATH, tmp_path)

    assert first.event_hash == second.event_hash
    assert first.events[-1].hash == first.event_hash
    assert len({e.hash for e in first.events}) == len(first.events)


def test_a_different_reply_changes_the_hash(tmp_path: Path) -> None:
    changed = {
        **EFFICIENT_PATH,
        "attending": [
            turn(action="ask_history", question="Do you take any herbal or dietary supplements?"),
            *EFFICIENT_PATH["attending"][2:],
        ],
    }
    first, _ = _run(EFFICIENT_PATH, tmp_path)
    second, _ = _run(changed, tmp_path)

    assert first.event_hash != second.event_hash


def test_the_turn_limit_forces_a_commit(tmp_path: Path) -> None:
    script = {
        "attending": [
            turn(action="examine", system="bowel sounds"),
            turn(action="examine", system="bowel sounds"),
            turn(**COMMIT),
        ]
    }

    result, _ = _run(script, tmp_path, _config(limits={"attending_turns": 2}))

    assert result.forced_commit is True
    assert isinstance(result.commit, Commit)
    forced = [e for e in result.events if e.type == "refusal"][-1].payload
    assert isinstance(forced, Refusal)
    assert "Limits reached" in forced.reason


def test_the_budget_forces_a_commit(tmp_path: Path) -> None:
    script = {"attending": [turn(action="order_test", item="CBC", indication="x"), turn(**COMMIT)]}

    result, _ = _run(script, tmp_path, _config(limits={"budget_inr": Decimal(100)}))

    assert result.forced_commit is True
    assert _types(result)[-1] == "commit"


def test_a_run_that_never_commits_is_aborted(tmp_path: Path) -> None:
    script = {"attending": [turn(action="examine", system="bowel sounds")] * 3}

    result, _ = _run(script, tmp_path, _config(limits={"attending_turns": 1}))

    assert result.commit is None
    assert result.run.status == "aborted"


# --- the rest of the state machine ---


def test_the_challenger_can_speak_every_n_turns(tmp_path: Path) -> None:
    script = {
        "attending": [turn(action="examine", system="bowel sounds")] * 2 + [turn(**COMMIT)],
        "challenger": [turn(action="challenge", critique="c", alternatives=[])] * 2,
    }
    config = _config(challenger={"before_commit": False, "every_n_turns": 2})

    result, _ = _run(script, tmp_path, config)

    assert _types(result).count("challenge") == 1
    assert _types(result)[-1] == "commit"


def test_a_consultation_without_a_note_is_reported_to_the_attending(tmp_path: Path) -> None:
    script = {
        "attending": [turn(action="refer", specialty="haematology", question="q"), turn(**COMMIT)],
        "consultant": [turn(action="examine", system="bowel sounds")] * 4,
    }
    config = _config(challenger={"before_commit": False, "every_n_turns": 0})

    result, _ = _run(script, tmp_path, config)

    assert any("without a consult note" in reason for reason in _reasons(result))


@pytest.mark.parametrize(
    ("specialty", "message"),
    [("cardiology", "No cardiology Consultant is available.")],
)
def test_a_referral_to_a_specialty_not_offered_is_refused(
    tmp_path: Path, specialty: str, message: str
) -> None:
    script = {
        "attending": [turn(action="refer", specialty=specialty, question="q"), turn(**COMMIT)]
    }
    config = _config(challenger={"before_commit": False, "every_n_turns": 0})

    result, _ = _run(script, tmp_path, config)

    reasons = _reasons(result)
    assert message in reasons


def test_referrals_run_out(tmp_path: Path) -> None:
    note = turn(action="consult_note", findings="f", impression="i", recommendations=[])
    script = {
        "attending": [turn(action="refer", specialty="haematology", question="q")] * 2
        + [turn(**COMMIT)],
        "consultant": [note],
    }
    config = _config(
        limits={"referrals": 1}, challenger={"before_commit": False, "every_n_turns": 0}
    )

    result, _ = _run(script, tmp_path, config)

    reasons = _reasons(result)
    assert "No referrals left." in reasons


def test_waiting_with_nothing_pending_is_refused(tmp_path: Path) -> None:
    script = {"attending": [turn(action="wait"), turn(**COMMIT)]}
    config = _config(challenger={"before_commit": False, "every_n_turns": 0})

    result, _ = _run(script, tmp_path, config)

    reasons = _reasons(result)
    assert "Nothing is pending." in reasons


def test_refusals_are_shown_only_to_the_seat_refused(tmp_path: Path) -> None:
    script = {
        "attending": [turn(action="ask_history", question="What is the diagnosis?"), turn(**COMMIT)]
    }
    config = _config(challenger={"before_commit": False, "every_n_turns": 0})

    result, _ = _run(script, tmp_path, config)

    refusal = next(e for e in result.events if e.type == "refusal")
    assert refusal.visibility == ("attending",)
    assert isinstance(refusal.payload, Refusal)
    assert refusal.payload.violation is True


def test_model_calls_are_logged_and_never_visible(tmp_path: Path) -> None:
    result, _ = _run(EFFICIENT_PATH, tmp_path)

    calls = [e for e in result.events if e.type == "llm_call"]
    assert calls
    assert all(e.visibility == () for e in calls)
    assert {e.seat for e in calls} >= {"attending", "gatekeeper", "service.pathology"}


def test_the_config_must_name_the_bundle(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="names"):
        _run({}, tmp_path, _config(bundle="PMC1@v1.r1"))


# --- the fallback and off-script seats ---

SYNTHETIC = json.dumps(
    {
        "result_text": "Serum thallium: below 2 ug/L (reference below 5 ug/L).",
        "rationale": "No exposure.",
        "confidence": 0.8,
    }
)
NO_CHOICE = json.dumps({"item_id": None})
NO_CHALLENGE = _config(challenger={"before_commit": False, "every_n_turns": 0})


def test_an_order_outside_the_catalogue_is_answered_and_flagged(tmp_path: Path) -> None:
    script = {
        "attending": [
            turn(action="order_test", item="serum thallium", indication="x"),
            turn(**COMMIT),
        ],
        "matcher": [NO_CHOICE],
        "synthetic": [SYNTHETIC],
    }

    result, _ = _run(script, tmp_path, NO_CHALLENGE)

    generated = next(e for e in result.events if e.type == "result")
    assert generated.source == "synthetic"
    assert generated.seat == "synthetic"
    assert result.used_fallback is True


def test_a_question_outside_the_catalogue_is_answered_and_flagged(tmp_path: Path) -> None:
    script = {
        "attending": [
            turn(action="ask_history", question="Serum thallium exposure at work?"),
            turn(**COMMIT),
        ],
        "matcher": [NO_CHOICE],
        "synthetic": [SYNTHETIC],
    }

    result, _ = _run(script, tmp_path, NO_CHALLENGE)

    answer = [e for e in result.events if e.type == "answer"][-1]
    assert answer.source == "synthetic"
    assert result.used_fallback is True


def test_a_request_the_service_cannot_answer_is_refused_neutrally(tmp_path: Path) -> None:
    script = {
        "attending": [
            turn(action="order_test", item="hair mercury and arsenic", indication="x"),
            turn(**COMMIT),
        ],
        "matcher": [NO_CHOICE],
    }

    result, _ = _run(script, tmp_path, NO_CHALLENGE)

    assert "The request was not understood; please rephrase it." in _reasons(result)


class OffScript:
    """A seat that answers with an action its caller cannot use."""

    def __init__(self, seat_id: str, action: Any) -> None:
        self.seat_id = seat_id
        self._action = action

    def act(self, view: Any) -> Any:
        return self._action


def _run_with(
    tmp_path: Path, attending: Sequence[str], others: Mapping[str, Any], config: RunConfig
) -> RunResult:
    models = tmp_path / "models.yaml"
    models.write_text(MODELS, encoding="utf-8")
    fake = FakeLLM({"attending": list(attending)})
    recorder = CallRecorder()
    gateway = LLMGateway(load_models_config(models), backend_for=lambda e: fake, on_call=recorder)
    repo = InMemoryRepository()
    repo.add_bundle(PILOT, "0" * 64)
    permissions = load_permissions()

    def seat_for(seat: str) -> Any:
        return OffScript(seat, others[seat]) if seat in others else LLMSeat(seat, gateway)

    scheduler = Scheduler(
        config=config,
        bundle=PILOT,
        catalogue=CATALOGUE,
        repo=repo,
        gatekeeper=Gatekeeper(
            PILOT,
            CATALOGUE,
            coder=Coder(CATALOGUE, missing=MissingRequestLog()),
            matcher=LLMMatcher(gateway),
            permissions=permissions,
        ),
        synthetic=SyntheticService(PILOT, repo, gateway, NAMES),
        permissions=permissions,
        tables=load_tables(),
        seat_for=seat_for,
        recorder=recorder,
    )
    return scheduler.run(RUN_ID)


def test_off_script_seats_are_refused_not_obeyed(tmp_path: Path) -> None:
    from sambhasha.domain.actions import Challenge, Wait

    wrong = Wait()
    result = _run_with(
        tmp_path,
        [
            turn(action="order_test", item="peripheral blood film", indication="x"),
            turn(action="refer", specialty="haematology", question="q"),
            turn(**COMMIT),
            turn(**COMMIT),
        ],
        {"service.pathology": wrong, "consultant.haematology": wrong, "challenger": wrong},
        load_run_config(),
    )

    reasons = _reasons(result)
    assert "The service.pathology report was not filed." in reasons
    assert "Only a challenge is possible." in reasons
    assert any("consultant does not do that" in r for r in reasons)
    assert not any(isinstance(e.payload, Challenge) for e in result.events)


def test_an_attending_action_outside_its_role_is_refused(tmp_path: Path) -> None:
    from sambhasha.domain.actions import Challenge

    result = _run_with(
        tmp_path,
        [],
        {"attending": Challenge(critique="c", alternatives=())},
        _config(limits={"attending_turns": 1}),
    )

    assert any("attending does not do that" in r for r in _reasons(result))
    assert result.commit is None
