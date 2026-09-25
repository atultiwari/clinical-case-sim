"""scripts/catalogue.py: reading, checking and building the catalogue (PLAN L0.4)."""

import csv
import json
import shutil
from pathlib import Path

import pytest

from scripts import catalogue as cat

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "catalogue"


@pytest.fixture
def cat_dir(tmp_path: Path) -> Path:
    """A writable copy of the fixture catalogue."""
    target = tmp_path / "catalogue"
    shutil.copytree(FIXTURE, target)
    return target


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _rewrite(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _edit(cat_dir: Path, file: str, row_id: str, **changes: str) -> None:
    rows = _rows(cat_dir / file)
    key = next(iter(rows[0]))
    _rewrite(cat_dir / file, [{**r, **changes} if r[key] == row_id else r for r in rows])


def _append(cat_dir: Path, file: str, **row: str) -> None:
    rows = _rows(cat_dir / file)
    _rewrite(cat_dir / file, [*rows, {k: row.get(k, "") for k in rows[0]}])


def _problems(cat_dir: Path) -> list[str]:
    return cat.check(cat.read_catalogue(cat_dir))


def test_the_fixture_catalogue_is_clean() -> None:
    assert _problems(FIXTURE) == []


def test_missing_file_is_reported(cat_dir: Path) -> None:
    (cat_dir / "findings.csv").unlink()
    with pytest.raises(cat.CatalogueError, match=r"findings\.csv"):
        cat.read_catalogue(cat_dir)


def test_wrong_header_is_reported(cat_dir: Path) -> None:
    text = (cat_dir / "exam.csv").read_text(encoding="utf-8").replace("specialty_scope", "scope")
    (cat_dir / "exam.csv").write_text(text, encoding="utf-8")
    with pytest.raises(cat.CatalogueError, match=r"exam\.csv.*header"):
        cat.read_catalogue(cat_dir)


@pytest.mark.parametrize(
    ("file", "row_id", "changes", "expected"),
    [
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"id": "HX.occupation"}, "id"),
        ("exam.csv", "EX.ORAL.GUMS", {"id": "HX.ORAL.GUMS"}, "id"),
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"synonyms": "job"}, "two synonyms"),
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"synonyms": "Occupation|job"}, "name"),
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"synonyms": "job|Job|work"}, "duplicate"),
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"name": ""}, "name"),
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"category": ""}, "category"),
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"specialty_scope": "nurse"}, "scope"),
        ("history.csv", "HX.EXPOSURE.OCCUPATION", {"specialty_scope": "consultant.ent"}, "scope"),
        ("tests.csv", "LAB.HAEM.CBC", {"route": "lab"}, "route"),
        ("tests.csv", "LAB.HAEM.CBC", {"price_inr": "cheap"}, "price_inr"),
        ("tests.csv", "LAB.HAEM.CBC", {"price_inr": "-1"}, "price_inr"),
        ("tests.csv", "LAB.HAEM.CBC", {"price_source": "guess"}, "price_source"),
        ("tests.csv", "LAB.HAEM.CBC", {"tat_minutes": "4h"}, "tat_minutes"),
        ("tests.csv", "LAB.HAEM.CBC", {"invasive": "no"}, "invasive"),
        ("tests.csv", "LAB.HAEM.CBC", {"components": ""}, "component"),
        ("tests.csv", "LAB.HAEM.CBC", {"components": "CMP.HB|CMP.NOPE"}, "CMP.NOPE"),
        ("tests.csv", "LAB.HAEM.CBC", {"components": "CMP.HB|CMP.HB|CMP.RBC|CMP.MCH"}, "twice"),
        ("components.csv", "CMP.RBC", {"unit_si": ""}, "unit"),
        ("components.csv", "CMP.RBC", {"decimals": ""}, "decimals"),
        ("components.csv", "CMP.RBC", {"decimals": "9"}, "decimals"),
        ("components.csv", "CMP.HB", {"conv_factor": ""}, "conv_factor"),
        ("components.csv", "CMP.HIV_AG_AB", {"normal_text": ""}, "normal_text"),
        ("diagnoses.csv", "DX.LEAD_POISONING", {"icd10": "lead"}, "icd10"),
        ("diagnoses.csv", "DX.LEAD_POISONING", {"icd11": "x"}, "icd11"),
        ("diagnoses.csv", "DX.LEAD_POISONING", {"codes_verified": "maybe"}, "codes_verified"),
        ("findings.csv", "FND.COARSE_BASOPHILIC_STIPPLING", {"shown_by": ""}, "shown_by"),
        ("findings.csv", "FND.COARSE_BASOPHILIC_STIPPLING", {"shown_by": "LAB.NOPE"}, "LAB.NOPE"),
        ("normal_templates.csv", "EX.ORAL.GUMS", {"template": ""}, "template"),
        ("normal_templates.csv", "EX.ORAL.GUMS", {"item_id": "LAB.HAEM.CBC"}, "template"),
        ("normal_templates.csv", "EX.ORAL.GUMS", {"review_status": "ok"}, "review_status"),
        ("value_rules.csv", "R.MCH", {"kind": "product"}, "kind"),
        ("value_rules.csv", "R.MCH", {"inputs": "CMP.HB"}, "inputs"),
        ("value_rules.csv", "R.MCH", {"target": "CMP.NOPE"}, "CMP.NOPE"),
        ("value_rules.csv", "R.MCH", {"factor": "one"}, "factor"),
    ],
)
def test_bad_values_are_reported(
    cat_dir: Path, file: str, row_id: str, changes: dict[str, str], expected: str
) -> None:
    _edit(cat_dir, file, row_id, **changes)
    problems = _problems(cat_dir)
    assert any(expected in p for p in problems), problems


@pytest.mark.parametrize(
    ("row_id", "changes", "expected"),
    [
        ("CMP.MCH", {"sex": "X"}, "sex"),
        ("CMP.MCH", {"age_min": "adult"}, "age"),
        ("CMP.MCH", {"low": "40"}, "low"),
        ("CMP.MCH", {"low": ""}, "low"),
        ("CMP.MCH", {"source": ""}, "source"),
        ("CMP.HIV_AG_AB", {"text": ""}, "text"),
    ],
)
def test_bad_ranges_are_reported(
    cat_dir: Path, row_id: str, changes: dict[str, str], expected: str
) -> None:
    _edit(cat_dir, "component_ranges.csv", row_id, **changes)
    problems = _problems(cat_dir)
    assert any(expected in p for p in problems), problems


def test_a_component_without_a_range_is_reported(cat_dir: Path) -> None:
    rows = [r for r in _rows(cat_dir / "component_ranges.csv") if r["component_id"] != "CMP.MCH"]
    _rewrite(cat_dir / "component_ranges.csv", rows)
    assert any("CMP.MCH" in p and "range" in p for p in _problems(cat_dir))


def test_a_range_for_an_unknown_component_is_reported(cat_dir: Path) -> None:
    _append(
        cat_dir,
        "component_ranges.csv",
        component_id="CMP.NOPE",
        sex="any",
        text="x",
        source="Tietz",
    )
    assert any("CMP.NOPE" in p for p in _problems(cat_dir))


def test_duplicate_ids_across_files_are_reported(cat_dir: Path) -> None:
    _append(
        cat_dir,
        "exam.csv",
        id="HX.EXPOSURE.OCCUPATION",
        name="x",
        category="c",
        synonyms="a|b",
        specialty_scope="attending",
    )
    assert any("HX.EXPOSURE.OCCUPATION" in p and "twice" in p for p in _problems(cat_dir))


def test_a_component_no_test_uses_is_reported(cat_dir: Path) -> None:
    _append(cat_dir, "components.csv", id="CMP.ORPHAN", name="Orphan", unit_si="g/L", decimals="0")
    _append(
        cat_dir,
        "component_ranges.csv",
        component_id="CMP.ORPHAN",
        sex="any",
        low="1",
        high="2",
        source="Tietz",
    )
    assert any("CMP.ORPHAN" in p and "no test" in p for p in _problems(cat_dir))


def test_an_item_without_its_normal_template_is_reported(cat_dir: Path) -> None:
    rows = [r for r in _rows(cat_dir / "normal_templates.csv") if r["item_id"] != "REF.TOXICOLOGY"]
    _rewrite(cat_dir / "normal_templates.csv", rows)
    assert any("REF.TOXICOLOGY" in p and "template" in p for p in _problems(cat_dir))


def test_build_gives_a_sorted_load_document() -> None:
    doc = cat.build_document(cat.read_catalogue(FIXTURE), version=0)
    assert doc["version"] == 0
    ids = [i["id"] for i in doc["items"]]
    assert ids == sorted(ids)
    assert {i["kind"] for i in doc["items"]} == {
        "history",
        "exam",
        "test",
        "action",
        "referral",
        "diagnosis",
        "finding",
    }
    cbc = next(t for t in doc["tests"] if t["item_id"] == "LAB.HAEM.CBC")
    assert cbc == {
        "item_id": "LAB.HAEM.CBC",
        "route": "direct",
        "specimen": "EDTA blood",
        "price_inr": 200,
        "price_source": "estimate",
        "tat_minutes": 240,
        "invasive": False,
        "loinc": None,
        "components": ["CMP.HB", "CMP.RBC", "CMP.MCH"],
    }
    hb = next(c for c in doc["components"] if c["id"] == "CMP.HB")
    assert hb["conv_factor"] == 0.1
    assert hb["decimals"] == 0
    assert hb["ref_ranges"] == [
        {
            "sex": "F",
            "age_min": 18,
            "low": 115,
            "high": 165,
            "source": "Dacie and Lewis Practical Haematology, 12th ed. (2017)",
        },
        {
            "sex": "M",
            "age_min": 18,
            "low": 130,
            "high": 180,
            "source": "Dacie and Lewis Practical Haematology, 12th ed. (2017)",
        },
    ]
    pb = next(c for c in doc["components"] if c["id"] == "CMP.PB_BLOOD")
    assert pb["ref_ranges"][0]["display"] == "<5"
    hiv = next(c for c in doc["components"] if c["id"] == "CMP.HIV_AG_AB")
    assert hiv["unit_si"] is None
    tietz = "Tietz Textbook of Laboratory Medicine, 7th ed. (2022)"
    assert hiv["ref_ranges"] == [{"sex": "any", "text": "Non-reactive", "source": tietz}]
    assert doc["diagnoses"] == [{"item_id": "DX.LEAD_POISONING", "icd11": None, "icd10": "T56.0"}]
    assert doc["value_rules"][0]["inputs"] == ["CMP.HB", "CMP.RBC"]
    finding = next(i for i in doc["items"] if i["kind"] == "finding")
    assert finding["synonyms"] == ["basophilic stippling", "punctate basophilia"]


def test_build_is_deterministic() -> None:
    one = cat.build_document(cat.read_catalogue(FIXTURE), version=0)
    two = cat.build_document(cat.read_catalogue(FIXTURE), version=0)
    assert json.dumps(one) == json.dumps(two)


def test_cli_check_and_build(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cat.main(["check", "--dir", str(FIXTURE)]) == 0
    assert "history 2" in capsys.readouterr().out
    out = tmp_path / "doc.json"
    assert cat.main(["build", "--dir", str(FIXTURE), "--version", "3", "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["version"] == 3


def test_cli_refuses_a_broken_catalogue(
    cat_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _edit(cat_dir, "tests.csv", "LAB.HAEM.CBC", route="lab")
    assert cat.main(["check", "--dir", str(cat_dir)]) == 1
    assert "route" in capsys.readouterr().err
    out = tmp_path / "doc.json"
    assert cat.main(["build", "--dir", str(cat_dir), "--version", "0", "--out", str(out)]) == 1
    assert not out.exists()


def test_cli_reports_an_unreadable_catalogue(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cat.main(["check", "--dir", str(tmp_path)]) == 1
    assert "history.csv" in capsys.readouterr().err
