"""P0.2: case bundle models for schema 0.3 (Case Library SPEC §10)."""

from pathlib import Path
from typing import Any

import pytest

from sambhasha.domain.case_file import BundleError, CaseBundle, parse_bundle
from tests.unit.domain.bundle_factory import minimal_bundle, to_bytes

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
PUBLISHED = sorted(EXPORTS.glob("*.json"))
PILOT = EXPORTS / "PMC12949993@v1.r1.json"


def _rejection(bundle: dict[str, Any]) -> str:
    with pytest.raises(BundleError) as caught:
        parse_bundle(to_bytes(bundle))
    return str(caught.value)


# --- the published bundles ---


def test_the_case_library_has_published_bundles() -> None:
    assert len(PUBLISHED) >= 10


@pytest.mark.parametrize("path", PUBLISHED, ids=lambda p: p.name)
def test_every_published_bundle_validates(path: Path) -> None:
    bundle = parse_bundle(path.read_bytes())

    assert bundle.schema_version == "0.3"
    assert path.name == f"{bundle.bundle_id}.json"


def test_the_pilot_bundle_has_its_facts() -> None:
    pilot = parse_bundle(PILOT.read_bytes())

    assert pilot.bundle_id == "PMC12949993@v1.r1"
    assert len(pilot.facts) == 191
    assert sum(f.category == "history" for f in pilot.facts) == 10
    assert len(pilot.raw_material) == 3
    assert len(pilot.media) == 4
    assert len(pilot.gaps) == 20


def test_the_pilot_series_are_expanded_to_125_atomic_facts() -> None:
    pilot = parse_bundle(PILOT.read_bytes())

    points = pilot.series_points()

    assert len(points) == 125
    assert all(p.origin == "article" and p.day is not None for p in points)


def test_series_points_group_by_series_and_skip_derived_values() -> None:
    bundle = parse_bundle(to_bytes(minimal_bundle()))

    assert [p.id for p in bundle.series_points()] == ["S01.d0", "S01.d2"]


def test_the_bundle_is_immutable() -> None:
    bundle = parse_bundle(to_bytes(minimal_bundle()))

    with pytest.raises(ValueError, match="frozen"):
        bundle.facts[0].value = "changed"  # type: ignore[misc]
    assert isinstance(bundle.facts, tuple)


def test_ledger_values_are_numeric_or_text() -> None:
    bundle = parse_bundle(to_bytes(minimal_bundle()))

    numeric, text = bundle.ledger
    assert numeric.value.value == 140
    assert numeric.value.unit == "mmol/L"
    assert text.value.text == "No recent travel."


def test_conditions_parse_with_their_keyword_names() -> None:
    bundle = parse_bundle(to_bytes(minimal_bundle()))

    must_not = bundle.ground_truth.must_not_do
    assert must_not is not None
    condition = must_not[0].if_
    assert condition is not None
    assert condition.plan_before == ("ACT.TRANSFUSE", "LAB.HAEM.FILM")


# --- ids ---


@pytest.mark.parametrize(
    "collection", ["facts", "ledger", "reports", "consult_notes", "raw_material", "media", "gaps"]
)
def test_duplicate_ids_are_rejected(collection: str) -> None:
    bundle = minimal_bundle()
    bundle[collection].append(bundle[collection][0])

    message = _rejection(bundle)

    assert "duplicate" in message
    assert bundle[collection][0]["id"] in message


def test_a_malformed_bundle_id_is_rejected() -> None:
    bundle = minimal_bundle()
    bundle["bundle_id"] = "PMC1-v1"

    assert "bundle_id" in _rejection(bundle)


# --- invalid files, with clear messages ---


def test_a_source_without_a_licence_is_rejected() -> None:
    bundle = minimal_bundle()
    del bundle["source"]["licence"]

    message = _rejection(bundle)

    assert "source.licence" in message
    assert "required" in message.lower()


def test_a_figure_without_a_licence_is_rejected() -> None:
    bundle = minimal_bundle()
    del bundle["media"][0]["licence"]

    assert "media[0].licence" in _rejection(bundle)


def test_a_de_novo_case_has_no_source() -> None:
    bundle = minimal_bundle()
    bundle["source"] = None

    assert parse_bundle(to_bytes(bundle)).source is None


@pytest.mark.parametrize("release", ["team", "service", "service.Pathology", ""])
def test_an_unknown_release_value_is_rejected(release: str) -> None:
    bundle = minimal_bundle()
    bundle["facts"][1]["release"] = release

    message = _rejection(bundle)

    assert "facts[1].release" in message
    assert "vignette, chart, never or service.<department>" in message


def test_an_unknown_raw_material_release_is_rejected() -> None:
    bundle = minimal_bundle()
    bundle["raw_material"][0]["release"] = "pathology"

    assert "raw_material[0].release" in _rejection(bundle)


def test_an_unknown_fact_origin_is_rejected() -> None:
    bundle = minimal_bundle()
    bundle["facts"][0]["origin"] = "synthetic"

    message = _rejection(bundle)

    assert "facts[0].origin" in message
    assert "'article' or 'derived'" in message


def test_an_unknown_ledger_tier_is_rejected() -> None:
    bundle = minimal_bundle()
    bundle["ledger"][0]["tier"] = "guess"

    assert "ledger[0].tier" in _rejection(bundle)


def test_an_unsupported_schema_version_is_refused() -> None:
    bundle = minimal_bundle()
    bundle["schema_version"] = "0.2"

    message = _rejection(bundle)

    assert "schema_version" in message
    assert "0.3" in message


def test_an_unknown_field_is_rejected() -> None:
    bundle = minimal_bundle()
    bundle["facts"][0]["valeu"] = "typo"

    assert "facts[0].valeu" in _rejection(bundle)


def test_a_wrongly_typed_value_is_not_coerced() -> None:
    bundle = minimal_bundle()
    bundle["facts"][1]["day"] = "0"

    assert "facts[1].day" in _rejection(bundle)


def test_an_original_report_must_be_provisional() -> None:
    bundle = minimal_bundle()
    bundle["reports"][0]["status"] = "final"

    assert "reports[0]" in _rejection(bundle)


def test_a_report_finding_must_be_a_finding_id() -> None:
    bundle = minimal_bundle()
    bundle["reports"][0]["findings"] = ["target cells"]

    assert "reports[0].findings[0]" in _rejection(bundle)


def test_text_that_is_not_json_is_rejected() -> None:
    with pytest.raises(BundleError, match="not valid JSON"):
        parse_bundle(b"{not json")


def test_a_json_array_is_rejected() -> None:
    with pytest.raises(BundleError, match="object"):
        parse_bundle(b"[]")


def test_every_problem_is_listed_not_only_the_first() -> None:
    bundle = minimal_bundle()
    bundle["facts"][0]["origin"] = "synthetic"
    del bundle["media"][0]["licence"]

    message = _rejection(bundle)

    assert "facts[0].origin" in message
    assert "media[0].licence" in message


def test_parse_bundle_returns_a_case_bundle() -> None:
    assert isinstance(parse_bundle(to_bytes(minimal_bundle())), CaseBundle)
