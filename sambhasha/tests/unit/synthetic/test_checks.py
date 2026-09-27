"""P1.4: checks on generated results (SPEC §8: consistency, leaks, never "not available")."""

from pathlib import Path

import pytest

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.leakscan import Lexicon
from sambhasha.domain.case_file import parse_bundle
from sambhasha.synthetic.checks import check_result

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
PILOT = parse_bundle((EXPORTS / "PMC12949993@v1.r3.json").read_bytes())
LEXICON = Lexicon.from_bundle(PILOT, CatalogueNames.load())


def _problems(text: str) -> tuple[str, ...]:
    return check_result(text, PILOT, LEXICON)


def test_a_plausible_result_passes() -> None:
    assert _problems("Serum thallium: below 2 ug/L (reference below 5 ug/L).") == ()


@pytest.mark.parametrize(
    "text",
    ["Not available.", "Result unavailable", "Test not performed", "N/A", "not done"],
)
def test_not_available_and_its_cousins_fail(text: str) -> None:
    assert any("not available" in p for p in _problems(text))


@pytest.mark.parametrize("term", ["lead poisoning", "plumbism"])
def test_a_leak_fails(term: str) -> None:
    assert any("leak" in p for p in _problems(f"Findings suggest {term}."))


def test_a_value_contradicting_a_stored_fact_fails() -> None:
    problems = _problems("Haemoglobin 150 g/L on repeat.")

    assert any("contradicts" in p and "Haemoglobin" in p for p in problems)


def test_a_stored_value_repeated_is_not_a_contradiction() -> None:
    assert _problems("Haemoglobin 72 g/L, as before.") == ()


def test_an_analyte_named_without_a_number_is_not_a_contradiction() -> None:
    assert _problems("Haemoglobin was not rechecked for this assay; the assay is normal.") == ()
