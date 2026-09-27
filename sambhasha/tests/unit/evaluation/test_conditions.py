"""P1.8: evaluating the shared scoring conditions (Case Library SPEC §10.4)."""

import pytest

from sambhasha.domain.conditions import Condition
from sambhasha.evaluation.conditions import holds
from sambhasha.evaluation.encounter import Encounter

ENCOUNTER = Encounter(
    dx_id="DX.LEAD_POISONING",
    evidence_items=frozenset({"H10", "L26"}),
    released_items=frozenset({"H09", "H10", "L26"}),
    asked=frozenset({"HX.MEDS.SUPPLEMENTS"}),
    ordered=frozenset({"LAB.TOX.BLOOD_LEAD", "LAB.HAEM.FILM"}),
    referred=frozenset({"REF.TOXICOLOGY"}),
    plan=("ACT.STOP_SUSPECTED_SOURCE", "RX.CHELATION.SUCCIMER_ORAL", "REF.TOXICOLOGY"),
    findings=(("FND.COARSE_BASOPHILIC_STIPPLING", "LAB.HAEM.FILM"),),
)


def _holds(raw: dict[str, object]) -> bool:
    return holds(Condition.model_validate(raw), ENCOUNTER)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"dx_in": ["DX.LEAD_POISONING"]}, True),
        ({"dx_in": ["DX.WARM_AIHA"]}, False),
        ({"dx_in": ["DX.LEAD_*"]}, False),  # only ".*" is a wildcard
        ({"dx_in": ["DX.*"]}, True),
        ({"evidence_has": ["H10"]}, True),
        ({"evidence_has": ["H09"]}, False),
        ({"released_all": ["H09", "H10"]}, True),
        ({"released_all": ["H09", "X"]}, False),
        ({"released_any": ["X", "L26"]}, True),
        ({"asked_any": ["HX.MEDS.SUPPLEMENTS", "HX.X"]}, True),
        ({"ordered_any": ["LAB.TOX.*"]}, True),
        ({"ordered_all": ["LAB.TOX.BLOOD_LEAD", "LAB.CHEM.COPPER_CAERULOPLASMIN"]}, False),
        ({"referred_any": ["REF.TOXICOLOGY"]}, True),
        ({"plan_has": ["ACT.STOP_SUSPECTED_SOURCE", "RX.CHELATION.*"]}, True),
        ({"plan_has": ["ACT.NOTIFY_PUBLIC_HEALTH"]}, False),
        ({"plan_has_any": ["RX.IRON.ORAL", "RX.CHELATION.*"]}, True),
        ({"plan_before": ["ACT.STOP_SUSPECTED_SOURCE", "RX.CHELATION.*"]}, True),
        ({"plan_before": ["RX.CHELATION.*", "ACT.STOP_SUSPECTED_SOURCE"]}, False),
        ({"plan_before": ["ACT.NOTIFY_PUBLIC_HEALTH", "RX.CHELATION.*"]}, False),
        ({"finding_released": ["FND.COARSE_BASOPHILIC_STIPPLING"]}, True),
        (
            {
                "finding_released": ["FND.COARSE_BASOPHILIC_STIPPLING"],
                "from_tests": ["LAB.HAEM.FILM"],
            },
            True,
        ),
        (
            {
                "finding_released": ["FND.COARSE_BASOPHILIC_STIPPLING"],
                "from_tests": ["PROC.BM.ASPIRATE"],
            },
            False,
        ),
        (
            {
                "finding_released": {
                    "findings": ["FND.COARSE_BASOPHILIC_STIPPLING"],
                    "from_tests": ["LAB.HAEM.FILM"],
                }
            },
            True,
        ),
        ({"not": {"dx_in": ["DX.WARM_AIHA"]}}, True),
        ({"all": [{"dx_in": ["DX.LEAD_POISONING"]}, {"evidence_has": ["H10"]}]}, True),
        ({"all": [{"dx_in": ["DX.LEAD_POISONING"]}, {"evidence_has": ["H09"]}]}, False),
        ({"any": [{"dx_in": ["DX.X"]}, {"referred_any": ["REF.TOXICOLOGY"]}]}, True),
    ],
)
def test_conditions(raw: dict[str, object], expected: bool) -> None:
    assert _holds(raw) is expected


def test_two_keys_must_both_hold() -> None:
    assert _holds({"dx_in": ["DX.LEAD_POISONING"], "ordered_any": ["LAB.X"]}) is False


def test_no_diagnosis_matches_no_dx_condition() -> None:
    blank = ENCOUNTER.model_copy(update={"dx_id": None})

    assert holds(Condition.model_validate({"dx_in": ["DX.*"]}), blank) is False
