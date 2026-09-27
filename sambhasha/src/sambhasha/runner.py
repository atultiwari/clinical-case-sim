"""Assembling one run: the Gatekeeper, the services, the seats and the Scheduler (P1.9)."""

from collections.abc import Callable
from typing import Final

from sambhasha.catalogue import Catalogue
from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.domain.case_file import CaseBundle
from sambhasha.engine.config import RunConfig
from sambhasha.engine.scheduler import CallRecorder, Scheduler
from sambhasha.engine.seats import LLMSeat, Seat
from sambhasha.engine.tables import load_tables
from sambhasha.gatekeeper.coding import Coder, MissingRequestLog
from sambhasha.gatekeeper.matcher import LLMMatcher
from sambhasha.gatekeeper.policy import load_permissions
from sambhasha.gatekeeper.resolver import Gatekeeper
from sambhasha.llm.config import ROLES, ModelsConfig
from sambhasha.llm.gateway import LLMGateway
from sambhasha.storage.repo import Repository
from sambhasha.synthetic.service import SyntheticService

FAKE_MODEL: Final = "fake/scripted"


def fake_models_config() -> ModelsConfig:
    """Every role played by the scripted FakeLLM, so a fake run names no real model."""
    return ModelsConfig.model_validate(
        {
            "providers": {"fake": {"base_url": "http://fake.invalid/v1", "api_key": "fake"}},
            "profiles": {"fake": {"provider": "fake", "model": FAKE_MODEL, "family": "fake"}},
            "roles": dict.fromkeys(ROLES, "fake"),
            "family_exception": "a fake run plays scripted replies; no model is involved",
        }
    )


def build_scheduler(
    *,
    config: RunConfig,
    bundle: CaseBundle,
    repo: Repository,
    gateway: LLMGateway,
    recorder: CallRecorder,
    missing: MissingRequestLog,
    catalogue: Catalogue | None = None,
    seat_for: Callable[[str], Seat] | None = None,
) -> Scheduler:
    catalogue = catalogue or Catalogue.load()
    permissions = load_permissions()
    return Scheduler(
        config=config,
        bundle=bundle,
        catalogue=catalogue,
        repo=repo,
        gatekeeper=Gatekeeper(
            bundle,
            catalogue,
            coder=Coder(catalogue, missing=missing),
            matcher=LLMMatcher(gateway),
            permissions=permissions,
        ),
        synthetic=SyntheticService(bundle, repo, gateway, CatalogueNames.load()),
        permissions=permissions,
        tables=load_tables(),
        seat_for=seat_for or (lambda seat: LLMSeat(seat, gateway)),
        recorder=recorder,
    )
