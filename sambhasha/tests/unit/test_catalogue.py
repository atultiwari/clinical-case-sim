"""P1.2: the shared catalogue, read from `case-library/catalogue/` (Case Library SPEC §5)."""

from pathlib import Path

import pytest

from sambhasha.catalogue import Catalogue, CatalogueError, kind_of

CATALOGUE = Catalogue.load()


def test_every_file_is_read() -> None:
    kinds = {item.kind for item in CATALOGUE.items}

    assert kinds == {
        "history",
        "exam",
        "test",
        "component",
        "action",
        "referral",
        "diagnosis",
        "finding",
    }
    assert len(CATALOGUE.items) > 1500


def test_an_item_has_its_name_synonyms_and_loinc_field() -> None:
    cbc = CATALOGUE.get("LAB.HAEM.CBC")

    assert cbc.name == "Full blood count"
    assert "hemogram" in cbc.synonyms
    assert cbc.kind == "test"
    assert cbc.loinc is None or cbc.loinc


def test_an_unknown_id_is_a_clear_error() -> None:
    with pytest.raises(KeyError, match=r"LAB\.NOPE"):
        CATALOGUE.get("LAB.NOPE")


@pytest.mark.parametrize(
    ("item_id", "kind"),
    [
        ("HX.PC.PAIN_DETAILS", "history"),
        ("EX.ORAL.GUMS", "exam"),
        ("LAB.HAEM.CBC", "test"),
        ("IMG.XR.ABDOMEN", "test"),
        ("PROC.BM.ASPIRATE", "test"),
        ("CMP.HB", "component"),
        ("RX.CHELATION.SUCCIMER_ORAL", "action"),
        ("ACT.NOTIFY_PUBLIC_HEALTH", "action"),
        ("REF.TOXICOLOGY", "referral"),
        ("DX.LEAD_POISONING", "diagnosis"),
        ("FND.COARSE_BASOPHILIC_STIPPLING", "finding"),
    ],
)
def test_the_kind_follows_the_id_pattern(item_id: str, kind: str) -> None:
    assert kind_of(item_id) == kind


def test_an_id_outside_the_patterns_is_rejected() -> None:
    with pytest.raises(CatalogueError, match=r"XYZ\.A"):
        kind_of("XYZ.A")


def test_a_missing_folder_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(CatalogueError, match="not found"):
        Catalogue.load(tmp_path)
