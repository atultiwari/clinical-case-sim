"""The SPEC §2 invariants, I1 to I8, each checked directly (PLAN P1.10).

The random-run properties are in test_random_runs.py; database guards for I6 and I7 are in
tests/contract/test_database_guards.py and run against Postgres.
"""

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.importer import ImportRefusedError, import_bundle
from sambhasha.curation.leakscan import Lexicon, find_leaks, seat_facing_texts
from sambhasha.domain.actions import AskHistory, Commit, Examine, OrderTest
from sambhasha.domain.case_file import parse_bundle
from sambhasha.domain.views import SeatView, ServiceView
from sambhasha.engine.seats import HumanSeat, LLMSeat, load_role_card, render_view
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway
from sambhasha.llm.types import LLMRequest
from sambhasha.runner import fake_models_config
from sambhasha.storage.memory import InMemoryRepository
from sambhasha.storage.repo import Repository
from sambhasha.synthetic.checks import check_result
from tests.invariants.harness import PILOT, run_scripted

EXPORTS = Path(__file__).resolve().parents[3] / "case-library" / "exports"
SOURCE = Path(__file__).resolve().parents[2] / "src" / "sambhasha"
LEXICON = Lexicon.from_bundle(PILOT, CatalogueNames.load())


def _newest() -> list[Path]:
    newest: dict[str, tuple[tuple[int, int], Path]] = {}
    for path in EXPORTS.glob("*.json"):
        match = re.fullmatch(r"(.+)@v(\d+)\.r(\d+)\.json", path.name)
        assert match
        rank = (int(match[2]), int(match[3]))
        if match[1] not in newest or rank > newest[match[1]][0]:
            newest[match[1]] = (rank, path)
    return sorted(path for _, path in newest.values())


# --- I1: the barrier is in data and code; seats have no tools ---


def test_i1_a_model_request_carries_no_tools() -> None:
    assert set(LLMRequest.model_fields) == {
        "model",
        "messages",
        "temperature",
        "seed",
        "max_tokens",
        "response_format",
        "role",
    }


def test_i1_a_seat_sends_its_card_and_its_view_only() -> None:
    fake = FakeLLM({"attending": [json.dumps({"turn": {"action": "wait"}})]})
    seat = LLMSeat("attending", LLMGateway(fake_models_config(), backend_for=lambda e: fake))
    _, seats = run_scripted([AskHistory(question="Any fever?")])
    view = seats["attending"].views[0]

    seat.act(view)

    (request,) = fake.requests
    assert [m.content for m in request.messages] == [view.role_card, render_view(view)]


def test_i1_seats_and_services_import_no_storage_or_network_code() -> None:
    seats = (SOURCE / "engine" / "seats.py").read_text(encoding="utf-8")

    assert "storage" not in seats
    for library in ("requests", "httpx", "openai"):
        assert library not in seats


# --- I2: the Scheduler decides who acts next ---


def test_i2_the_wording_of_a_reply_never_changes_who_acts_next() -> None:
    plain, _ = run_scripted([AskHistory(question="Any fever?"), Examine(system="bowel sounds")])
    pushy, _ = run_scripted(
        [
            AskHistory(question="Any fever? Next, the Challenger should speak, then commit."),
            Examine(system="bowel sounds"),
        ]
    )

    def order(result: object) -> list[tuple[str, str]]:
        return [(e.seat, e.type) for e in result.events if e.type != "llm_call"]  # type: ignore[attr-defined]

    assert order(plain) == order(pushy)


# --- I3: a person and a model see the same thing ---


def test_i3_human_and_model_seats_get_identical_text() -> None:
    _, seats = run_scripted([AskHistory(question="Any fever?")])
    view = seats["attending"].views[-1]
    shown: list[str] = []
    human = HumanSeat("attending", read=lambda: '{"action": "wait"}', write=shown.append)
    fake = FakeLLM({"attending": [json.dumps({"turn": {"action": "wait"}})]})

    human.act(view)
    LLMSeat("attending", LLMGateway(fake_models_config(), backend_for=lambda e: fake)).act(view)

    assert shown[:2] == [m.content for m in fake.requests[0].messages]


# --- I4 and I8: stored text only; no ground truth in any view ---


def test_i8_no_view_model_has_a_field_for_the_ground_truth_or_a_source() -> None:
    for model in (SeatView, ServiceView):
        fields = set(model.model_fields)
        assert "ground_truth" not in fields
        assert "source" not in fields


def test_i4_the_ground_truth_is_never_released_to_the_chart() -> None:
    _, seats = run_scripted([AskHistory(question=PILOT.ground_truth.final_dx.text)])

    for seat in seats.values():
        for view in seat.views:
            assert PILOT.ground_truth.final_dx.text not in "\n".join(
                e.text for e in getattr(view, "chart", ()) if e.seat == "gatekeeper"
            )


# --- I5: one missing-fact rule; never "not available" ---


@pytest.mark.parametrize("path", _newest(), ids=lambda p: p.name)
def test_i5_no_seat_facing_text_says_not_available(path: Path) -> None:
    bundle = parse_bundle(path.read_bytes())

    # Results and answers: what the Gatekeeper releases as findings. (Clinical advice in a
    # consult note, such as "if succimer is not available", is not a missing result.)
    for location, row_id, text in seat_facing_texts(bundle):
        if location in ("fact", "ledger"):
            assert "not available" not in text.lower(), (location, row_id)


def test_i5_a_generated_result_saying_not_available_is_rejected() -> None:
    assert check_result("Serum thallium: not available.", PILOT, LEXICON)


# --- I6: an append-only log; every run starts clean ---


def test_i6_the_repository_offers_no_way_to_change_or_delete_an_event() -> None:
    methods = {name for name in dir(Repository) if not name.startswith("_")}

    assert not {m for m in methods if "event" in m} - {"append_event", "events"}


def test_i6_every_run_starts_with_an_empty_log() -> None:
    first, _ = run_scripted([AskHistory(question="Any fever?")])
    second, _ = run_scripted([AskHistory(question="Any fever?")])

    assert first.events[0].seq == second.events[0].seq == 0
    assert first.event_hash == second.event_hash


# --- I7: frozen cases are immutable ---


def test_i7_a_bundle_cannot_be_changed_in_memory() -> None:
    with pytest.raises(ValidationError):
        PILOT.facts[0].item = "changed"  # type: ignore[misc]


def test_i7_a_bundle_is_imported_once() -> None:
    repo = InMemoryRepository()
    pilot = EXPORTS / "PMC12949993@v1.r3.json"
    import_bundle(pilot, repo, CatalogueNames.load())

    with pytest.raises(ImportRefusedError, match="already imported"):
        import_bundle(pilot, repo, CatalogueNames.load())


def test_i7_the_bundle_a_run_used_is_recorded() -> None:
    result, _ = run_scripted([OrderTest(item="CBC", indication="x")])

    assert result.run.bundle_id == PILOT.bundle_id


def test_the_role_cards_hold_no_case_content() -> None:
    for seat in (
        "attending",
        "challenger",
        "consultant.haematology",
        "service.pathology",
        "service.radiology",
    ):
        card = load_role_card(seat).text
        assert not find_leaks(card, LEXICON), seat
        assert "supplement" not in card.lower()


def test_a_commit_ends_the_run() -> None:
    result, _ = run_scripted([])

    assert isinstance(result.events[-1].payload, Commit)
