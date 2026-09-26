"""P0.5: the import-time leak scanner, Sambhasha's second line of defence (SPEC §9)."""

import re
from pathlib import Path

import pytest

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.leakscan import Lexicon, find_leaks, scan_bundle
from sambhasha.domain.case_file import CaseBundle, parse_bundle

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
PILOT = parse_bundle((EXPORTS / "PMC12949993@v1.r3.json").read_bytes())
PILOT_TERMS = ["lead poisoning", "plumbism", "saturnism", "lead toxicity"]
CATALOGUE = CatalogueNames.load()


def _newest(paths: list[Path]) -> list[Path]:
    newest: dict[str, tuple[tuple[int, int], Path]] = {}
    for path in paths:
        match = re.fullmatch(r"(.+)@v(\d+)\.r(\d+)\.json", path.name)
        assert match
        rank = (int(match[2]), int(match[3]))
        if match[1] not in newest or rank > newest[match[1]][0]:
            newest[match[1]] = (rank, path)
    return sorted(path for _, path in newest.values())


@pytest.fixture(scope="module")
def lexicon() -> Lexicon:
    return Lexicon.from_bundle(PILOT, CATALOGUE)


def test_the_lexicon_holds_the_diagnosis_and_its_synonyms(lexicon: Lexicon) -> None:
    assert set(PILOT_TERMS) <= set(lexicon.terms)


def test_the_lexicon_allows_catalogue_and_case_test_names(lexicon: Lexicon) -> None:
    assert {"blood lead", "lead level", "blood lead (venous)"} <= set(lexicon.allowed)


def test_the_lexicon_adds_the_catalogue_names_of_the_diagnosis(lexicon: Lexicon) -> None:
    names = CATALOGUE.diagnosis("DX.LEAD_POISONING")

    assert names
    assert {" ".join(n.lower().split()) for n in names} <= set(lexicon.terms)


# --- seeded leaks in the pilot ---


@pytest.mark.parametrize("term", PILOT_TERMS)
def test_a_leak_in_the_vignette_is_caught(term: str) -> None:
    seeded = PILOT.model_copy(update={"vignette": f"{PILOT.vignette} Query {term}."})

    findings = scan_bundle(seeded, Lexicon.from_bundle(seeded, CATALOGUE))

    assert [(f.location, f.term) for f in findings] == [("vignette", term)]


@pytest.mark.parametrize("term", PILOT_TERMS)
def test_a_leak_in_a_caption_is_caught(term: str) -> None:
    figure = PILOT.media[0].model_copy(update={"redacted_caption": f"Film consistent with {term}"})
    seeded = PILOT.model_copy(update={"media": (figure, *PILOT.media[1:])})

    findings = scan_bundle(seeded, Lexicon.from_bundle(seeded, CATALOGUE))

    assert [(f.location, f.row_id, f.term) for f in findings] == [("media", figure.id, term)]


@pytest.mark.parametrize("term", PILOT_TERMS)
def test_a_leak_in_a_synthetic_narrative_is_caught(term: str, lexicon: Lexicon) -> None:
    narrative = f"Marrow aspirate: ring sideroblasts, in keeping with {term.upper()}."

    assert [leak.term for leak in find_leaks(narrative, lexicon)] == [term]


# --- what is not a leak ---


@pytest.mark.parametrize(
    "text",
    [
        "Blood lead 77.8 µg/dL",
        "Please send a blood lead.",
        "Lead level requested",
        "Pb level pending",
        "The patient leads a quiet life.",
        "plumbing work at home",
    ],
)
def test_test_names_and_ordinary_words_are_not_leaks(text: str, lexicon: Lexicon) -> None:
    assert find_leaks(text, lexicon) == ()


def test_terms_match_across_case_and_line_breaks(lexicon: Lexicon) -> None:
    leaks = find_leaks("Suspect LEAD\n  Poisoning here", lexicon)

    assert [(leak.term, leak.start) for leak in leaks] == [("lead poisoning", 8)]


def test_every_occurrence_is_reported_with_its_place(lexicon: Lexicon) -> None:
    text = "Plumbism? Or saturnism."

    leaks = find_leaks(text, lexicon)

    assert [(text[leak.start : leak.end], leak.term) for leak in leaks] == [
        ("Plumbism", "plumbism"),
        ("saturnism", "saturnism"),
    ]


def test_case_specific_phrases_can_be_added() -> None:
    lexicon = Lexicon.from_bundle(PILOT, extra_terms=("Ayurvedic lead",))

    assert [leak.term for leak in find_leaks("an ayurvedic lead source", lexicon)] == [
        "ayurvedic lead"
    ]


def test_phrases_can_be_allowed() -> None:
    lexicon = Lexicon(terms=("lead poisoning",), allowed=("lead poisoning screen",))

    assert find_leaks("A lead poisoning screen was sent.", lexicon) == ()
    assert len(find_leaks("Lead poisoning is likely.", lexicon)) == 1


def test_a_blank_term_is_ignored() -> None:
    lexicon = Lexicon(terms=("", "  ", "plumbism"), allowed=())

    assert lexicon.terms == ("plumbism",)


# --- what the scan covers ---


def test_confirmatory_facts_and_unreleased_facts_are_not_scanned(lexicon: Lexicon) -> None:
    blood_lead = next(f for f in PILOT.facts if f.release == "chart")
    confirmatory = blood_lead.model_copy(update={"value": "lead poisoning", "reveals_dx": True})
    never = blood_lead.model_copy(update={"id": "X1", "value": "plumbism", "release": "never"})
    seeded = PILOT.model_copy(update={"facts": (*PILOT.facts, confirmatory, never)})

    assert scan_bundle(seeded, lexicon) == ()


def test_the_ground_truth_is_never_scanned() -> None:
    # It names the diagnosis by design, and no seat ever sees it (invariant I8).
    assert scan_bundle(PILOT) == ()


@pytest.mark.parametrize("path", _newest(sorted(EXPORTS.glob("*.json"))), ids=lambda p: p.name)
def test_every_published_bundle_scans_clean(path: Path) -> None:
    bundle: CaseBundle = parse_bundle(path.read_bytes())

    assert scan_bundle(bundle, Lexicon.from_bundle(bundle, CATALOGUE)) == ()
