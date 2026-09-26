"""P0.6: importing the pilot into the Postgres run database (milestone M0)."""

from pathlib import Path

import psycopg
import pytest

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.importer import DEVELOPMENT_ONLY, import_bundle, primary_bundles
from sambhasha.storage.postgres import PostgresRepository

pytestmark = pytest.mark.integration

PILOT_R1 = (
    Path(__file__).resolve().parents[3] / "case-library" / "exports" / "PMC12949993@v1.r1.json"
)


def test_the_pilot_imports_into_postgres(db: psycopg.Connection) -> None:
    repo = PostgresRepository(db)

    report = import_bundle(PILOT_R1, repo, CatalogueNames.load())

    counts = {
        table: db.execute(
            f"select count(*) from sambhasha.{table} where bundle_id = %s",  # noqa: S608
            (report.bundle_id,),
        ).fetchone()
        for table in ("fact", "ledger_row", "raw_material", "media", "gap")
    }
    assert {t: c[0] for t, c in counts.items() if c} == {
        "fact": 191,
        "ledger_row": 1109,
        "raw_material": 3,
        "media": 4,
        "gap": 20,
    }
    (record,) = repo.list_bundles()
    assert (record.primary_eligible, record.eligibility_reason) == (False, DEVELOPMENT_ONLY)
    assert primary_bundles(repo) == ()
    assert repo.get_bundle(report.bundle_id).bundle_id == "PMC12949993@v1.r1"
