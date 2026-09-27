"""P1.5: price and turnaround tables, generated from the catalogue (D-022; SPEC §10.4)."""

from pathlib import Path

import pytest

from sambhasha.catalogue import Catalogue
from sambhasha.engine.tables import (
    ACTION_TURNAROUND,
    PRICES_PATH,
    TURNAROUND_PATH,
    generate_tables,
    load_tables,
    render_tables,
)

CATALOGUE = Catalogue.load()


def test_test_prices_and_turnaround_come_from_the_catalogue() -> None:
    tables = generate_tables(CATALOGUE)

    cbc = tables.price("LAB.HAEM.CBC")
    assert (cbc.inr, cbc.estimated) == (300, False)
    assert tables.turnaround("LAB.HAEM.CBC") == 240
    assert tables.turnaround("LAB.TOX.BLOOD_LEAD") == 1440


def test_estimated_prices_are_flagged() -> None:
    tables = generate_tables(CATALOGUE)

    lead = tables.price("LAB.TOX.BLOOD_LEAD")
    assert lead.estimated is True


def test_actions_have_the_spec_defaults() -> None:
    tables = generate_tables(CATALOGUE)

    assert dict(ACTION_TURNAROUND) == {
        "ask_history": 5,
        "examine": 10,
        "bedside_test": 15,
        "consultant_session": 240,
    }
    assert tables.turnaround("ask_history") == 5


def test_an_item_outside_the_catalogue_gets_the_flagged_estimate() -> None:
    tables = generate_tables(CATALOGUE)

    unknown = tables.price("REQ:serum thallium")
    assert unknown.estimated is True
    assert unknown.inr == tables.unmatched_price
    assert tables.turnaround("REQ:serum thallium") == tables.unmatched_turnaround


def test_the_committed_files_match_the_catalogue() -> None:
    prices, turnaround = render_tables(generate_tables(CATALOGUE))

    assert PRICES_PATH.read_text(encoding="utf-8") == prices, (
        "configs/prices_inr.yaml is stale: run `uv run sambhasha tables generate`"
    )
    assert TURNAROUND_PATH.read_text(encoding="utf-8") == turnaround


def test_the_committed_files_load_to_the_same_tables() -> None:
    assert load_tables() == generate_tables(CATALOGUE)


def test_a_missing_table_is_a_clear_error(tmp_path: Path) -> None:
    from sambhasha.engine.tables import TablesError

    with pytest.raises(TablesError, match="generate"):
        load_tables(tmp_path / "prices.yaml", tmp_path / "turnaround.yaml")


def test_tables_are_written_and_read_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sambhasha.engine import tables as module

    monkeypatch.setattr(module, "PRICES_PATH", tmp_path / "prices.yaml")
    monkeypatch.setattr(module, "TURNAROUND_PATH", tmp_path / "turnaround.yaml")
    generated = generate_tables(CATALOGUE)

    prices, turnaround = module.write_tables(generated)

    assert module.load_tables(prices, turnaround) == generated


def test_malformed_tables_are_a_clear_error(tmp_path: Path) -> None:
    from sambhasha.engine.tables import TablesError

    (tmp_path / "p.yaml").write_text("items: {}\n", encoding="utf-8")
    (tmp_path / "t.yaml").write_text("minutes: {}\n", encoding="utf-8")

    with pytest.raises(TablesError, match="regenerate"):
        load_tables(tmp_path / "p.yaml", tmp_path / "t.yaml")
