"""The real catalogue in catalogue/ meets PLAN L0.4's acceptance criteria.

It is clean (every test has a component, every component a unit or normal text
and a range with a source, every item two synonyms), and every item on the
pilot's paths exists (cases/PMC12949993/ANALYSIS.md).
"""

import re
from functools import cache
from pathlib import Path

import pytest

from scripts import catalogue as cat

CASE_LIBRARY = Path(__file__).resolve().parents[1]
ANALYSIS = CASE_LIBRARY / "cases" / "PMC12949993" / "ANALYSIS.md"
ID_IN_TEXT = re.compile(r"\b(?:HX|EX|LAB|IMG|PROC|CMP|RX|ACT|REF|DX|FND)\.[A-Z0-9_.]*[A-Z0-9_*]")

# The laboratory results the pilot article reports (gold case file series and single results).
PILOT_COMPONENTS = (
    "CMP.HB",
    "CMP.HCT",
    "CMP.RBC",
    "CMP.RETIC_ABS",
    "CMP.MCV",
    "CMP.WBC",
    "CMP.NEUT",
    "CMP.LYMPH",
    "CMP.MONO",
    "CMP.EOS",
    "CMP.BASO",
    "CMP.NRBC",
    "CMP.PLT",
    "CMP.BILI_TOTAL",
    "CMP.ALP",
    "CMP.AST",
    "CMP.ALT",
    "CMP.GGT",
    "CMP.LDH",
    "CMP.IRON",
    "CMP.TRANSFERRIN",
    "CMP.TIBC",
    "CMP.TSAT",
    "CMP.FERRITIN",
    "CMP.CRP",
    "CMP.B12",
    "CMP.HOLOTC",
    "CMP.FOLATE",
    "CMP.CHOL_TOTAL",
    "CMP.CK",
    "CMP.MG",
    "CMP.HAPTOGLOBIN",
    "CMP.DAT_IGG",
    "CMP.DAT_C3D",
    "CMP.ABO_GROUP",
    "CMP.RHD",
    "CMP.IGG",
    "CMP.IGA",
    "CMP.IGM",
    "CMP.FLC_KAPPA",
    "CMP.FLC_LAMBDA",
    "CMP.FLC_RATIO",
    "CMP.COLD_AGGLUTININ_TITRE",
    "CMP.PB_BLOOD",
)
PILOT_TESTS = (
    "LAB.HAEM.CBC",
    "LAB.HAEM.RETIC",
    "LAB.CHEM.LFT",
    "LAB.CHEM.RENAL",
    "LAB.CHEM.LDH",
    "LAB.CHEM.HAPTOGLOBIN",
    "LAB.TBS.DAT",
    "LAB.TBS.ANTIBODY_SCREEN",
    "LAB.TBS.BLOOD_GROUP",
    "LAB.CHEM.IRON_STUDIES",
    "LAB.CHEM.FERRITIN",
    "LAB.CHEM.CRP",
    "LAB.IMM.SPEP",
    "LAB.IMM.IFE",
    "LAB.IMM.IMMUNOGLOBULINS",
    "LAB.IMM.FLC",
    "LAB.URINE.HAEMOSIDERIN",
    "LAB.TBS.COLD_AGGLUTININ",
    "LAB.SERO.MYCOPLASMA",
    "LAB.SERO.EBV",
)


@cache
def _catalogue() -> cat.Catalogue:
    return cat.read_catalogue(cat.DEFAULT_DIR)


def _ids() -> set[str]:
    catalogue = _catalogue()
    return {row["id"] for _, row in catalogue.items()} | {
        row["id"] for row in catalogue.rows("components.csv")
    }


def _pilot_ids() -> list[str]:
    return sorted(set(ID_IN_TEXT.findall(ANALYSIS.read_text(encoding="utf-8"))))


def test_the_catalogue_is_clean() -> None:
    assert cat.check(_catalogue()) == []


def test_the_catalogue_is_near_its_v0_size() -> None:
    sizes = dict.fromkeys(cat.ITEM_FILES.values(), 0)
    for kind, _ in _catalogue().items():
        sizes[kind] += 1
    minimum = {
        "history": 100,
        "exam": 60,
        "test": 180,
        "action": 80,
        "referral": 15,
        "diagnosis": 250,
        "finding": 50,
    }
    assert all(sizes[kind] >= n for kind, n in minimum.items()), sizes


def test_every_item_on_the_pilot_paths_exists() -> None:
    ids = _ids()
    missing = []
    for pilot_id in _pilot_ids():
        if pilot_id.endswith("*"):
            if not any(i.startswith(pilot_id[:-1]) for i in ids):
                missing.append(pilot_id)
        elif pilot_id not in ids:
            missing.append(pilot_id)
    assert missing == []


def test_the_analysis_names_enough_ids_to_be_a_real_check() -> None:
    assert len(_pilot_ids()) > 100


@pytest.mark.parametrize("item_id", PILOT_COMPONENTS + PILOT_TESTS)
def test_the_pilot_laboratory_results_have_a_home(item_id: str) -> None:
    assert item_id in _ids()


def test_supplement_question_carries_the_pilot_synonyms() -> None:
    row = next(r for r in _catalogue().rows("history.csv") if r["id"] == "HX.MEDS.SUPPLEMENTS")
    synonyms = {s.casefold() for s in cat.split_list(row["synonyms"])}
    wanted = {
        "supplements",
        "vitamins",
        "herbal",
        "ayurvedic medicine",
        "traditional medicine",
        "chinese medicine",
        "home remedies",
        "tonics",
        "over-the-counter",
        "alternative medicine",
        "imported medicines",
    }
    assert wanted <= synonyms


def test_exogenous_drug_levels_are_not_detected_by_default() -> None:
    components = {r["id"]: r for r in _catalogue().rows("components.csv")}
    for cid in ("CMP.DIGOXIN", "CMP.LITHIUM", "CMP.PARACETAMOL", "CMP.SALICYLATE", "CMP.ETHANOL"):
        assert components[cid]["normal_text"] == "Not detected"
        assert components[cid]["unit_si"] == ""


def test_v0_prices_are_all_flagged_as_estimates() -> None:
    # Until L0.5 matches them against the CGHS rate list (catalogue/README.md).
    assert {r["price_source"] for r in _catalogue().rows("tests.csv")} == {"estimate"}
