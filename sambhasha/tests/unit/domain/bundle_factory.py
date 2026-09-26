"""A small, invented schema 0.3 bundle for tests that corrupt one field at a time.

It holds no real case content, so tests can print it freely.
"""

import copy
import json
from typing import Any


def minimal_bundle() -> dict[str, Any]:
    """Return a fresh, valid bundle as plain JSON data."""
    return copy.deepcopy(_MINIMAL)


def to_bytes(bundle: dict[str, Any]) -> bytes:
    return json.dumps(bundle).encode()


_MINIMAL: dict[str, Any] = {
    "bundle_id": "PMC1@v1.r1",
    "schema_version": "0.3",
    "catalogue_version": 2,
    "case": {
        "slug": "c-abcde",
        "display_title": "Tired for a month",
        "display_tags": ["anaemia"],
        "specialty": "haematology",
        "lab_profile": {
            "age_years": 40,
            "sex": "female",
            "components": {"CMP.HB": {"low": 120, "high": 150, "unit": "g/L"}},
        },
    },
    "source": {
        "citation": "Invented, 2026",
        "pmcid": "PMC1",
        "licence": "CC BY 4.0",
        "attribution": "Invented authors",
        "production_ok": True,
        "public_release_ok": True,
    },
    "clock": {"day_0": "2026-01-01", "day_0_label": "Admission"},
    "vignette": "A 40-year-old woman has felt tired for a month.",
    "opening_statement_lay": "I've been so tired.",
    "facts": [
        {
            "id": "H01",
            "category": "history",
            "item": "Presenting complaint",
            "catalogue_ref": "HX.PC.ONSET_DURATION",
            "released_by": ["HX.PC.ONSET_DURATION"],
            "value": "Tired for a month",
            "day": None,
            "kind": "raw",
            "origin": "article",
            "release": "vignette",
            "release_condition": None,
        },
        {
            "id": "S01.d0",
            "category": "lab",
            "item": "Haemoglobin",
            "catalogue_ref": "CMP.HB",
            "value_num": 72,
            "unit": "g/L",
            "ref_range": "120-150",
            "flag": "L",
            "day": 0,
            "kind": "raw",
            "origin": "article",
            "release": "chart",
        },
        {
            "id": "S01.d2",
            "category": "lab",
            "item": "Haemoglobin",
            "catalogue_ref": "CMP.HB",
            "value_num": 80.5,
            "unit": "g/L",
            "day": 2,
            "kind": "raw",
            "origin": "article",
            "release": "chart",
        },
        {
            "id": "D.MCH.d0",
            "category": "lab",
            "item": "MCH",
            "catalogue_ref": "CMP.MCH",
            "value_num": 30,
            "day": 0,
            "kind": "raw",
            "origin": "derived",
            "formula": "hb / rbc",
            "release": "chart",
        },
    ],
    "ledger": [
        {
            "id": "LG1",
            "target": "CMP.NA",
            "day_bucket": None,
            "tier": "normal",
            "value": {"value": 140, "unit": "mmol/L", "ref_range": "135-145"},
        },
        {
            "id": "LG2",
            "target": "HX.SOCIAL.TRAVEL",
            "day_bucket": None,
            "tier": "rule",
            "value": {"text": "No recent travel."},
        },
    ],
    "reports": [
        {
            "id": "RP1",
            "test_item_id": "LAB.HAEM.FILM",
            "variant": "original",
            "status": "provisional",
            "status_line": "Provisional report",
            "findings": ["FND.TARGET_CELLS"],
            "report_text": "Target cells are seen.",
            "origins": ["article"],
        }
    ],
    "consult_notes": [
        {
            "id": "CN1",
            "specialty": "haematology",
            "variant": 1,
            "condition": {"released_any": ["LAB.HAEM.FILM"]},
            "note_text": "Please review the film.",
            "origin": "affected",
        }
    ],
    "raw_material": [
        {
            "id": "R01",
            "test": "Blood film",
            "release": "service.pathology",
            "day": 0,
            "findings": "Target cells.",
        }
    ],
    "media": [
        {
            "id": "M1",
            "licence": "CC BY 4.0",
            "production_ok": True,
            "public_release_ok": True,
            "has_annotations": False,
            "production_decision": "use",
        }
    ],
    "gaps": [{"id": "G01", "item": "Ferritin", "auto_generate": True}],
    "ground_truth": {
        "final_dx": {"id": "DX.INVENTED", "text": "Invented diagnosis"},
        "accepted_differential": ["Another invented diagnosis"],
        "rubric": {
            "default_score": 1,
            "rubric": [{"score": 5, "text": "Names it", "if": {"dx_in": ["DX.INVENTED"]}}],
        },
        "must_do": [{"text": "Review the film", "if": {"ordered_any": ["LAB.HAEM.FILM"]}}],
        "must_not_do": [
            {
                "text": "Transfuse before the film",
                "if": {"plan_before": ["ACT.TRANSFUSE", "LAB.HAEM.FILM"]},
            }
        ],
        "treatment_given": None,
        "outcome": None,
    },
    "test_utility": [{"test_item_id": "LAB.HAEM.FILM", "utility": "essential"}],
    "path_analysis": [
        {"path_id": "P1", "kind": "efficient", "name": "Film first", "items": ["LAB.HAEM.FILM"]}
    ],
}
