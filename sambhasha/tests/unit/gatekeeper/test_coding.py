"""P1.2: coding request text to catalogue ids with the catalogue's synonyms (D-022)."""

import csv
from pathlib import Path

import pytest

from sambhasha.catalogue import Catalogue
from sambhasha.gatekeeper.coding import Coder, MissingRequestLog, normalise

CATALOGUE = Catalogue.load()


@pytest.fixture
def log() -> MissingRequestLog:
    return MissingRequestLog()


@pytest.fixture
def coder(log: MissingRequestLog) -> Coder:
    return Coder(CATALOGUE, missing=log)


# --- the PLAN's acceptance cases ---


@pytest.mark.parametrize("text", ["CBC", "hemogram", "complete blood count"])
def test_blood_count_requests_resolve_to_one_id(coder: Coder, text: str) -> None:
    coding = coder.code(text, kinds=("test",))

    assert (coding.status, coding.ids) == ("exact", ("LAB.HAEM.CBC",))


@pytest.mark.parametrize("text", ["blood lead", "lead level", "Pb level"])
def test_blood_lead_requests_resolve_to_one_id(coder: Coder, text: str) -> None:
    coding = coder.code(text, kinds=("test",))

    assert (coding.status, coding.ids) == ("exact", ("LAB.TOX.BLOOD_LEAD",))


def test_unmatched_text_is_logged_for_the_case_library(
    coder: Coder, log: MissingRequestLog
) -> None:
    coding = coder.code("zqx frobnication assay", kinds=("test",), bundle_id="PMC1@v1.r1")

    assert (coding.status, coding.ids) == ("unmatched", ())
    (request,) = log.requests
    assert (request.query, request.kind, request.bundle_id, request.source) == (
        "zqx frobnication assay",
        "test",
        "PMC1@v1.r1",
        "sambhasha",
    )


def test_the_missing_requests_export_matches_the_case_vault_table(
    coder: Coder, log: MissingRequestLog, tmp_path: Path
) -> None:
    coder.code("zqx frobnication assay", kinds=("test",), bundle_id="PMC1@v1.r1")
    coder.code("wibble scan", kinds=("test",))

    path = log.write_csv(tmp_path / "missing.csv")

    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert list(rows[0]) == ["created_at", "source", "bundle_id", "kind", "query"]
    assert [(r["query"], r["bundle_id"]) for r in rows] == [
        ("zqx frobnication assay", "PMC1@v1.r1"),
        ("wibble scan", ""),
    ]


# --- normalisation ---


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Full Blood Count!", "full blood count"),
        ("Haemoglobin", "hemoglobin"),
        ("anaemia screen", "anemia screen"),
        ("Oesophageal biopsy", "esophageal biopsy"),
        ("Pb level, please", "lead"),
        ("  platelet   counts ", "platelet count"),
        ("CD55/CD59", "cd55 cd59"),
        ("Coombs' test", "coomb"),
    ],
)
def test_normalise(text: str, expected: str) -> None:
    assert normalise(text) == expected


def test_british_and_american_spellings_code_alike(coder: Coder) -> None:
    assert (
        coder.code("hemoglobin electrophoresis", kinds=("test",)).ids
        == coder.code("haemoglobin electrophoresis", kinds=("test",)).ids
    )


def test_word_order_does_not_matter(coder: Coder) -> None:
    coding = coder.code("blood count, complete", kinds=("test",))

    assert (coding.status, coding.ids) == ("exact", ("LAB.HAEM.CBC",))


# --- candidates for the matcher model ---


def test_close_text_gives_ranked_candidates(coder: Coder, log: MissingRequestLog) -> None:
    coding = coder.code("full blood picture", kinds=("test",))

    assert coding.status == "candidates"
    assert "LAB.HAEM.CBC" in coding.ids[:5]
    assert log.requests == ()  # candidates go to the matcher, not to the Case Library


def test_candidates_stay_within_the_requested_kinds(coder: Coder) -> None:
    coding = coder.code("lead", kinds=("referral",))

    assert all(i.startswith("REF.") for i in coding.ids)


def test_kinds_limit_exact_matches_too(coder: Coder) -> None:
    assert coder.code("toxicology", kinds=("referral",)).ids[0].startswith("REF.")


def test_an_item_id_itself_is_accepted(coder: Coder) -> None:
    coding = coder.code("LAB.TOX.BLOOD_LEAD", kinds=("test",))

    assert (coding.status, coding.ids) == ("exact", ("LAB.TOX.BLOOD_LEAD",))


def test_blank_text_is_unmatched_but_not_logged(coder: Coder, log: MissingRequestLog) -> None:
    assert coder.code("  ", kinds=("test",)).status == "unmatched"
    assert log.requests == ()


def test_most_items_code_to_themselves_by_name() -> None:
    coder = Coder(CATALOGUE, missing=MissingRequestLog())
    own = [
        item
        for item in CATALOGUE.items
        if coder.code(item.name, kinds=(item.kind,)).ids[:1] == (item.id,)
    ]

    assert len(own) / len(CATALOGUE.items) > 0.97


def test_normalising_adds_no_ambiguity_the_catalogue_lacks() -> None:
    from collections import defaultdict

    from sambhasha.gatekeeper.coding import _build_index

    for kind in (
        "history",
        "exam",
        "test",
        "component",
        "action",
        "referral",
        "diagnosis",
        "finding",
    ):
        items = [i for i in CATALOGUE.items if i.kind == kind]
        raw: defaultdict[str, set[str]] = defaultdict(set)
        for item in items:
            for phrase in (item.name, *item.synonyms):
                raw[" ".join(phrase.lower().split())].add(item.id)
        catalogue_own = {frozenset(ids) for ids in raw.values() if len(ids) > 1}
        ours = {ids for ids in _build_index(items).by_phrase.values() if len(ids) > 1}

        assert ours <= catalogue_own, kind


@pytest.mark.parametrize(
    ("text", "item_id"),
    [
        ("PT %", "LAB.HAEM.PT_PERCENT"),
        ("a CBC", "LAB.HAEM.CBC"),
        ("the blood lead", "LAB.TOX.BLOOD_LEAD"),
    ],
)
def test_percent_and_leading_articles(coder: Coder, text: str, item_id: str) -> None:
    assert coder.code(text, kinds=("test",)).ids == (item_id,)


def test_an_ambiguous_synonym_goes_to_the_matcher(coder: Coder) -> None:
    coding = coder.code("FDP", kinds=("test",))

    assert coding.status == "candidates"
    assert set(coding.ids[:2]) == {"LAB.HAEM.FDP", "LAB.HAEM.D_DIMER"}


def test_an_unknown_or_wrong_kind_item_id_is_not_taken_as_given(coder: Coder) -> None:
    assert coder.code("LAB.NOT_AN_ITEM", kinds=("test",)).status != "exact"
    assert coder.code("REF.TOXICOLOGY", kinds=("test",)).ids[:1] != ("REF.TOXICOLOGY",)
