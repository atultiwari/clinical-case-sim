"""P1.4: the Synthetic Findings Service, answering only requests outside the catalogue."""

import csv
import json
from pathlib import Path

import pytest

from sambhasha.catalogue import Catalogue, CatalogueItem
from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.domain.actions import OrderTest
from sambhasha.domain.case_file import parse_bundle
from sambhasha.domain.synthetic import SyntheticRow
from sambhasha.gatekeeper.coding import Coder, MissingRequestLog
from sambhasha.gatekeeper.policy import load_permissions
from sambhasha.gatekeeper.resolver import Gatekeeper, GatekeeperRequest, OutsideCatalogue, Released
from sambhasha.llm.config import ModelsConfig, load_models_config
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway
from sambhasha.storage.memory import InMemoryRepository
from sambhasha.synthetic.route import respond
from sambhasha.synthetic.service import (
    Generated,
    GenerationFailed,
    HeldForReviewer,
    SyntheticService,
)

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
BUNDLE_PATH = EXPORTS / "PMC12949993@v1.r3.json"
PILOT = parse_bundle(BUNDLE_PATH.read_bytes())
CATALOGUE = Catalogue.load()
THALLIUM = "serum thallium"
GOOD = json.dumps(
    {
        "result_text": "Serum thallium: below 2 ug/L (reference below 5 ug/L).",
        "rationale": "Nothing in the case suggests thallium exposure.",
        "confidence": 0.8,
    }
)
CONFIG = """
providers:
  local: {base_url: "http://localhost:11434/v1", api_key: ollama}
profiles:
  doctor: {provider: local, model: doctor-model, family: one}
  synth: {provider: local, model: synth-model, family: two}
roles: {attending: doctor, challenger: doctor, consultant: doctor, service: doctor,
        matcher: doctor, synthetic: synth, curator: doctor, evaluator: synth}
family_exception: tests use one scripted model
"""


def _reply(text: str) -> str:
    return json.dumps({"result_text": text, "rationale": "r", "confidence": 0.5})


class NoMatch:
    def choose(self, text: str, candidates: tuple[CatalogueItem, ...]) -> str | None:
        return None


@pytest.fixture
def config(tmp_path: Path) -> ModelsConfig:
    path = tmp_path / "models.yaml"
    path.write_text(CONFIG, encoding="utf-8")
    return load_models_config(path)


@pytest.fixture
def repo() -> InMemoryRepository:
    repo = InMemoryRepository()
    repo.add_bundle(PILOT, "0" * 64)
    return repo


def _service(
    config: ModelsConfig, repo: InMemoryRepository, *replies: str
) -> tuple[SyntheticService, FakeLLM]:
    fake = FakeLLM({"synthetic": list(replies)})
    gateway = LLMGateway(config, backend_for=lambda endpoint: fake)
    service = SyntheticService(PILOT, repo, gateway, CatalogueNames.load())
    return service, fake


def _gatekeeper(missing: MissingRequestLog) -> Gatekeeper:
    return Gatekeeper(
        PILOT,
        CATALOGUE,
        coder=Coder(CATALOGUE, missing=missing),
        matcher=NoMatch(),
        permissions=load_permissions(),
    )


def _order(item: str, day: int = 2) -> GatekeeperRequest:
    return GatekeeperRequest(seat="attending", action=OrderTest(item=item, indication="x"), day=day)


def test_a_catalogue_request_never_reaches_the_service(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, fake = _service(config, repo)
    missing = MissingRequestLog()

    outcome = respond(_gatekeeper(missing), service, _order("blood lead"))

    assert isinstance(outcome.result, Released)
    assert fake.requests == ()
    assert outcome.used_fallback is False


def test_an_outside_request_is_generated_and_flagged(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, fake = _service(config, repo, GOOD)

    outcome = respond(_gatekeeper(MissingRequestLog()), service, _order(THALLIUM))

    assert isinstance(outcome.result, Generated)
    assert outcome.result.text == "Serum thallium: below 2 ug/L (reference below 5 ug/L)."
    assert outcome.used_fallback is True
    assert len(fake.requests) == 1


def test_the_model_is_told_the_truth_the_day_and_the_request(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, fake = _service(config, repo, GOOD)

    service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=5, released=("Hb 72 g/L",))

    prompt = fake.requests[0].messages[-1].content
    assert PILOT.ground_truth.final_dx.text in prompt
    assert "Day: 5" in prompt
    assert THALLIUM in prompt
    assert "Hb 72 g/L" in prompt
    assert fake.requests[0].model == "synth-model"


def test_a_repeated_request_returns_the_same_ledger_row(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, fake = _service(config, repo, GOOD)
    request = OutsideCatalogue(query=THALLIUM, kind="test")

    first = service.answer(request, day=2)
    second = service.answer(OutsideCatalogue(query="Serum  Thallium", kind="test"), day=2)

    assert isinstance(first, Generated)
    assert isinstance(second, Generated)
    assert second.row == first.row
    assert (first.cached, second.cached) == (False, True)
    assert len(fake.requests) == 1


def test_another_day_is_another_row(config: ModelsConfig, repo: InMemoryRepository) -> None:
    service, fake = _service(config, repo, GOOD, GOOD)

    service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)
    service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=9)

    assert len(fake.requests) == 2


def test_a_contradicting_result_is_rejected_and_regenerated(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, fake = _service(config, repo, _reply("Haemoglobin 150 g/L; thallium low."), GOOD)

    outcome = service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)

    assert isinstance(outcome, Generated)
    assert outcome.text.startswith("Serum thallium")
    assert "contradicts" in fake.requests[1].messages[-1].content


def test_no_output_says_not_available(config: ModelsConfig, repo: InMemoryRepository) -> None:
    service, _ = _service(config, repo, _reply("Not available."), _reply("N/A"), GOOD)

    outcome = service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)

    assert isinstance(outcome, Generated)
    assert "available" not in outcome.text.lower()


def test_after_every_retry_fails_nothing_is_stored(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, _ = _service(config, repo, *[_reply("Not available.")] * 3)

    outcome = service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)

    assert isinstance(outcome, GenerationFailed)
    assert repo.synthetic_rows(PILOT.bundle_id) == ()


def test_g14_is_never_auto_generated(config: ModelsConfig, repo: InMemoryRepository) -> None:
    service, fake = _service(config, repo)

    outcome = service.answer(OutsideCatalogue(query="hair mercury and arsenic", kind="test"), day=2)

    assert isinstance(outcome, HeldForReviewer)
    assert outcome.gap_id == "G14"
    assert fake.requests == ()


def test_a_matched_gap_passes_its_guidance(config: ModelsConfig, repo: InMemoryRepository) -> None:
    service, fake = _service(config, repo, GOOD)

    service.answer(OutsideCatalogue(query="zinc protoporphyrin red cell assay", kind="test"), day=2)

    prompt = fake.requests[0].messages[-1].content
    guidance = next(g.guidance for g in PILOT.gaps if g.id == "G11")
    assert guidance
    assert guidance in prompt


def test_the_stored_row_records_its_generator(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, _ = _service(config, repo, GOOD)

    outcome = service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)

    assert isinstance(outcome, Generated)
    row = outcome.row
    assert (row.generator_model, row.prompt_version, row.review_status) == (
        "synth-model",
        "1",
        "pending",
    )
    assert row.query == THALLIUM
    assert row.checks == ("leak", "not_available", "consistency")


def test_the_export_lists_every_generated_request(
    config: ModelsConfig, repo: InMemoryRepository, tmp_path: Path
) -> None:
    missing = MissingRequestLog()
    gatekeeper = _gatekeeper(missing)
    service, _ = _service(config, repo, GOOD, _reply("Serum selenium: 1.1 umol/L (0.8-1.5)."))

    for item in (THALLIUM, "serum selenium estimation", THALLIUM):
        respond(gatekeeper, service, _order(item))

    rows = list(csv.DictReader(missing.write_csv(tmp_path / "missing.csv").open(encoding="utf-8")))
    assert sorted(r["query"] for r in rows) == ["serum selenium estimation", THALLIUM]


def test_a_model_that_never_replies_validly_fails_cleanly(
    config: ModelsConfig, repo: InMemoryRepository
) -> None:
    service, _ = _service(config, repo, "no", "still no", "never")

    outcome = service.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)

    assert isinstance(outcome, GenerationFailed)
    assert repo.synthetic_rows(PILOT.bundle_id) == ()


class RacingRepository(InMemoryRepository):
    """Another writer stores the same request between our lookup and our insert."""

    def __init__(self) -> None:
        super().__init__()
        self.first_lookup = True

    def get_synthetic(
        self, bundle_id: str, code: str, day_bucket: int | None
    ) -> SyntheticRow | None:
        if self.first_lookup:
            self.first_lookup = False
            return None
        return super().get_synthetic(bundle_id, code, day_bucket)


def test_when_another_writer_wins_its_row_is_the_answer(config: ModelsConfig) -> None:
    repo = RacingRepository()
    repo.add_bundle(PILOT, "0" * 64)
    theirs, _ = _service(config, repo, _reply("Serum thallium: 1 ug/L (below 5)."))
    theirs.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)  # uses the first lookup
    repo.first_lookup = True
    ours, _ = _service(config, repo, GOOD)

    outcome = ours.answer(OutsideCatalogue(query=THALLIUM, kind="test"), day=2)

    assert isinstance(outcome, Generated)
    assert outcome.cached is True
    assert outcome.text == "Serum thallium: 1 ug/L (below 5)."
