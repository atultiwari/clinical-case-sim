"""P1.6: seats and role cards (SPEC §10.3; invariant I3: LLM and human seats see the same)."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from sambhasha.domain.actions import (
    AskHistory,
    Challenge,
    Commit,
    ConsultNote,
    OrderTest,
    Report,
)
from sambhasha.domain.views import ChartEntry, Limits, SeatView, ServiceView
from sambhasha.engine.seats import (
    ALLOWED_ACTIONS,
    HumanSeat,
    LLMSeat,
    SeatInputError,
    load_role_card,
    render_view,
    role_of,
)
from sambhasha.llm.config import ModelsConfig, load_models_config
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway, LLMOutputError

CONFIG = """
providers:
  local: {base_url: "http://localhost:11434/v1", api_key: ollama}
profiles:
  p: {provider: local, model: m, family: f}
roles: {attending: p, challenger: p, consultant: p, service: p, matcher: p, synthetic: p,
        curator: p, evaluator: p}
family_exception: tests use one scripted model
"""
LIMITS = Limits(turns_left=29, referrals_left=4, budget_left_inr=Decimal(4700), sim_minutes=1510)
CHART = (
    ChartEntry(
        event_id="E0",
        sim_minutes=0,
        seat="gatekeeper",
        type="answer",
        text="49-year-old woman with abdominal pain for three weeks.",
    ),
    ChartEntry(
        event_id="E3",
        sim_minutes=1450,
        seat="gatekeeper",
        type="result",
        text="Blood lead (venous): 77.8 ug/dL [H]",
    ),
)


@pytest.fixture
def config(tmp_path: Path) -> ModelsConfig:
    path = tmp_path / "models.yaml"
    path.write_text(CONFIG, encoding="utf-8")
    return load_models_config(path)


def _view(seat: str) -> SeatView:
    return SeatView(
        seat_id=seat,
        role_card=load_role_card(seat).text,
        chart=CHART,
        own_notes=CHART[:1] if seat == "attending" else (),
        limits=LIMITS,
    )


SERVICE_VIEW = ServiceView(
    seat_id="service.pathology",
    role_card=load_role_card("service.pathology").text,
    order_id="O2",
    test="Blood film",
    clinical_details="Anaemia; weak DAT on IVIG.",
    raw_material="Coarse basophilic stippling in a proportion of red cells.",
)


def _seat(config: ModelsConfig, seat: str, *replies: object) -> tuple[LLMSeat, FakeLLM]:
    fake = FakeLLM({role_of(seat): [json.dumps({"turn": r}) for r in replies]})
    return LLMSeat(seat, LLMGateway(config, backend_for=lambda e: fake)), fake


# --- each seat acts from a fixture view ---

CASES = [
    (
        "attending",
        {"action": "order_test", "item": "zinc protoporphyrin", "indication": "lead"},
        OrderTest,
    ),
    (
        "attending",
        {
            "action": "commit",
            "final_diagnosis": "X",
            "differential": [],
            "treatment_plan": "Y",
            "evidence": ["E3"],
        },
        Commit,
    ),
    (
        "challenger",
        {"action": "challenge", "critique": "Anchoring on AIHA.", "alternatives": ["a toxin"]},
        Challenge,
    ),
    ("consultant.haematology", {"action": "ask_history", "question": "Any remedies?"}, AskHistory),
    (
        "consultant.haematology",
        {
            "action": "consult_note",
            "findings": "Pale",
            "impression": "Toxic",
            "recommendations": ["blood lead"],
        },
        ConsultNote,
    ),
]


@pytest.mark.parametrize(
    ("seat", "reply", "kind"), CASES, ids=lambda c: getattr(c, "__name__", str(c))[:30]
)
def test_each_seat_produces_a_valid_action(
    config: ModelsConfig, seat: str, reply: dict[str, object], kind: type
) -> None:
    llm_seat, fake = _seat(config, seat, reply)

    action = llm_seat.act(_view(seat))

    assert isinstance(action, kind)
    assert fake.requests[0].role == role_of(seat)


def test_a_service_reports_from_its_own_view(config: ModelsConfig) -> None:
    reply = {
        "action": "report",
        "order_id": "O2",
        "report_text": "Coarse stippling.",
        "impression": "Consistent with a toxic cause.",
    }
    seat, fake = _seat(config, "service.pathology", reply)

    action = seat.act(SERVICE_VIEW)

    assert isinstance(action, Report)
    assert fake.requests[0].messages[0].content == SERVICE_VIEW.role_card


def test_an_action_outside_the_role_is_invalid_and_retried(config: ModelsConfig) -> None:
    seat, fake = _seat(
        config,
        "challenger",
        {"action": "order_test", "item": "blood lead", "indication": "x"},
        {"action": "challenge", "critique": "c", "alternatives": []},
    )

    assert isinstance(seat.act(_view("challenger")), Challenge)
    assert len(fake.requests) == 2


def test_a_seat_that_never_gives_a_valid_action_raises(config: ModelsConfig) -> None:
    seat, _ = _seat(
        config, "attending", *[{"action": "challenge", "critique": "x", "alternatives": []}] * 3
    )

    with pytest.raises(LLMOutputError):
        seat.act(_view("attending"))


# --- the allowed actions come from configs/permissions.yaml ---


def test_allowed_actions_follow_the_permission_matrix() -> None:
    assert {k: sorted(v) for k, v in ALLOWED_ACTIONS.items()} == {
        "attending": [
            "ask_history",
            "commit",
            "examine",
            "order_test",
            "refer",
            "update_differential",
            "wait",
        ],
        "challenger": ["challenge"],
        "consultant": ["ask_history", "bedside_test", "consult_note", "examine"],
        "service": ["report"],
    }


# --- role cards ---


@pytest.mark.parametrize(
    "seat",
    [
        "attending",
        "challenger",
        "consultant.clinical_toxicology",
        "service.pathology",
        "service.radiology",
    ],
)
def test_every_card_has_a_version_and_names_its_actions(seat: str) -> None:
    card = load_role_card(seat)

    assert card.version == ("2" if seat == "attending" else "1")
    for action in ALLOWED_ACTIONS[role_of(seat)]:
        assert action in card.text, action


def test_the_consultant_card_names_its_specialty() -> None:
    card = load_role_card("consultant.clinical_toxicology")

    assert "You are the clinical toxicology Consultant" in card.text
    assert "{{" not in card.text


def test_a_seat_without_a_card_is_a_clear_error() -> None:
    from sambhasha.prompts import PromptError

    with pytest.raises(PromptError, match="service_microbiology"):
        load_role_card("service.microbiology")


# --- the human seat sees exactly what the model sees (I3) ---


def test_a_human_seat_is_shown_the_same_view_as_a_model(config: ModelsConfig) -> None:
    reply = {"action": "ask_history", "question": "Any herbal remedies?"}
    llm_seat, fake = _seat(config, "attending", reply)
    shown: list[str] = []
    human = HumanSeat("attending", read=lambda: json.dumps(reply), write=shown.append)
    view = _view("attending")

    from_model = llm_seat.act(view)
    from_human = human.act(view)

    assert from_model == from_human
    sent = fake.requests[0].messages
    assert (sent[0].content, sent[1].content) == (view.role_card, render_view(view))
    assert shown[:2] == [view.role_card, render_view(view)]


def test_a_human_seat_asks_again_after_an_invalid_action() -> None:
    answers = iter(
        [
            "not json",
            json.dumps({"action": "commit"}),
            json.dumps({"action": "ask_history", "question": "Pain?"}),
        ]
    )
    shown: list[str] = []
    human = HumanSeat("attending", read=lambda: next(answers), write=shown.append)

    action = human.act(_view("attending"))

    assert isinstance(action, AskHistory)
    assert sum("not a valid action" in s for s in shown) == 2


def test_a_human_seat_gives_up_after_repeated_invalid_input() -> None:
    human = HumanSeat("attending", read=lambda: "nonsense", write=lambda s: None)

    with pytest.raises(SeatInputError):
        human.act(_view("attending"))


# --- rendering ---


def test_the_rendered_view_shows_time_limits_and_chart() -> None:
    text = render_view(_view("attending"))

    assert "Day 1, 01:10" in text
    assert "Turns left: 29" in text
    assert "Budget left: INR 4700" in text
    assert "[E3 · day 1 00:10 · gatekeeper · result] Blood lead (venous): 77.8 ug/dL [H]" in text


def test_the_rendered_service_view_holds_only_the_order() -> None:
    text = render_view(SERVICE_VIEW)

    assert "Order O2: Blood film" in text
    assert "Anaemia; weak DAT on IVIG." in text
    assert "Coarse basophilic stippling" in text
    assert "E3" not in text


def test_a_service_view_lists_its_images() -> None:
    view = SERVICE_VIEW.model_copy(update={"media": ("M01", "M04")})

    assert "Images: M01, M04" in render_view(view)


# --- found in live pilot run A1: a flat schema and worked examples ---


def test_the_model_gets_a_flat_schema_listing_the_allowed_actions(config: ModelsConfig) -> None:
    seat, fake = _seat(config, "attending", {"action": "wait"})

    seat.act(_view("attending"))

    schema = json.loads(fake.requests[0].response_format or "{}")["json_schema"]["schema"]
    turn = schema["properties"]["turn"]
    assert turn["type"] == "object"
    assert sorted(turn["properties"]["action"]["enum"]) == sorted(ALLOWED_ACTIONS["attending"])
    assert {"question", "item", "indication", "items", "final_diagnosis"} <= set(turn["properties"])
    assert "oneOf" not in json.dumps(turn)
    assert "discriminator" not in json.dumps(turn)


def test_a_reply_is_still_checked_strictly_against_its_action(config: ModelsConfig) -> None:
    mixed = {
        "action": "order_test",
        "items": [
            {"diagnosis": "x", "probability": 0.5, "evidence_for": [], "evidence_against": []}
        ],
    }
    seat, fake = _seat(config, "attending", mixed, mixed, {"action": "wait"})

    assert seat.act(_view("attending")).model_dump()["action"] == "wait"
    assert len(fake.requests) == 3


@pytest.mark.parametrize("seat", ["attending", "challenger", "consultant.haematology"])
def test_the_view_ends_with_an_example_for_every_allowed_action(seat: str) -> None:
    from sambhasha.engine.seats import action_type_for

    text = render_view(_view(seat))

    examples = [line for line in text.splitlines() if line.startswith('{"action": ')]
    assert sorted(json.loads(e)["action"] for e in examples) == sorted(
        ALLOWED_ACTIONS[role_of(seat)]
    )
    for example in examples:  # every example is itself a valid action for the seat
        action_type_for(role_of(seat)).validate_json(example)


def test_the_service_view_shows_the_report_format() -> None:
    text = render_view(SERVICE_VIEW)

    assert '{"action": "report", "order_id": "O2"' in text
