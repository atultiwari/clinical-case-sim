"""Derived values, the normal generator, checks, coverage and the leak scan (SPEC §6)."""

from typing import Any

import psycopg
import pytest

from tests.integration.conftest import MINI_GENERATOR, add_affected_cbc, seed_mini_case

pytestmark = pytest.mark.integration


def _one(db: psycopg.Connection, query: str, params: tuple[Any, ...]) -> Any:
    row = db.execute(query, params).fetchone()
    assert row is not None
    return row[0]


def _derive(db: psycopg.Connection, cv: str) -> int:
    return int(_one(db, "select casevault.compute_derived(%s, %s, 'v0.0')", (cv, MINI_GENERATOR)))


def _normals(db: psycopg.Connection, cv: str) -> int:
    return int(_one(db, "select casevault.resolve_normals(%s)", (cv,)))


def _ledger(db: psycopg.Connection, cv: str) -> list[tuple[Any, ...]]:
    return db.execute(
        "select target, day_bucket, value from casevault.synthetic_ledger"
        " where case_version_id = %s and tier = 'normal' order by target, day_bucket nulls first",
        (cv,),
    ).fetchall()


def _missing(db: psycopg.Connection, cv: str) -> dict[str, list[str]]:
    rows = db.execute("select kind, missing from casevault.coverage_report(%s)", (cv,)).fetchall()
    return {kind: missing for kind, missing in rows if missing}


# --- Derived values ----------------------------------------------------------


def test_derived_mch_from_article_values(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)

    assert _derive(db, cv) == 1
    row = db.execute(
        "select id, value_num, unit, origin, formula from casevault.fact"
        " where case_version_id = %s and origin = 'derived'",
        (cv,),
    ).fetchone()
    assert row is not None
    assert (row[0], float(row[1]), row[2], row[3]) == ("D.MCH.d0", 30.0, "pg", "derived")
    assert row[4].startswith("MCH")


def test_derivation_runs_once(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _derive(db, cv)

    assert _derive(db, cv) == 0


# --- The normal generator ----------------------------------------------------


def test_normals_fill_open_components_and_templates(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _derive(db, cv)

    _normals(db, cv)
    filled = {(t, d) for t, d, _ in _ledger(db, cv)}

    # Days 0-2. The blood count is on the path, so it is left for affected rows.
    assert filled == {
        ("CMP.NA", 0), ("CMP.NA", 1), ("CMP.NA", 2), ("CMP.K", 0), ("CMP.K", 1), ("CMP.K", 2),
        ("CMP.UA_COLOUR", None), ("HX.OCCUPATION", None),
    }  # fmt: skip


def test_items_on_the_path_are_left_for_claude(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _normals(db, cv)

    targets = {t for t, _, _ in _ledger(db, cv)}

    assert not targets & {"CMP.HB", "CMP.RBC", "CMP.PB", "HX.SUPPLEMENTS", "LAB.FILM"}


def test_formula_targets_are_calculated_from_affected_values(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _derive(db, cv)
    add_affected_cbc(db, cv)

    _normals(db, cv)
    rows = db.execute(
        "select day_bucket, tier, value ->> 'value', rationale, confidence"
        " from casevault.synthetic_ledger where case_version_id = %s and target = 'CMP.MCH'"
        " order by day_bucket",
        (cv,),
    ).fetchall()

    # MCH = Hb / RBC: 75 / 2.5 on day 1, 80 (article) / 2.7 on day 2.
    assert [(r[0], r[1], r[2]) for r in rows] == [(1, "affected", "30.0"), (2, "affected", "29.6")]
    assert all(r[3].startswith("Calculated: MCH") and r[4] == 1 for r in rows)


def test_normal_values_sit_inside_the_patients_range(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _normals(db, cv)

    values = {(t, d): v for t, d, v in _ledger(db, cv)}

    sodium = values[("CMP.NA", 1)]
    assert 136 <= sodium["value"] <= 145  # the female range, not the male one
    assert sodium["unit"] == "mmol/L"
    assert sodium["ref_range"] == "136-145"
    assert 3.5 <= values[("CMP.K", 1)]["value"] <= 5.1
    assert values[("CMP.UA_COLOUR", None)] == {"text": "Straw"}


def test_normal_values_are_deterministic(db: psycopg.Connection) -> None:
    first = _one(db, "select casevault.normal_value('PMC1', 'CMP.NA', 3, 135, 145, 0)", ())
    again = _one(db, "select casevault.normal_value('PMC1', 'CMP.NA', 3, 135, 145, 0)", ())
    next_day = _one(db, "select casevault.normal_value('PMC1', 'CMP.NA', 4, 135, 145, 0)", ())

    assert first == again
    assert 135 <= first <= 145
    assert 135 <= next_day <= 145


def test_case_laboratory_overrides_the_catalogue_range(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute(
        'update casevault."case" set lab_profile = lab_profile'
        ' || \'{"components": {"CMP.NA": {"low": 140, "high": 142, "unit": "mEq/L"}}}\''
        " where id = 'PMC0000001'"
    )
    _normals(db, cv)

    sodium = {(t, d): v for t, d, v in _ledger(db, cv)}[("CMP.NA", 1)]

    assert 140 <= sodium["value"] <= 142
    assert sodium["unit"] == "mEq/L"


def test_normals_run_once(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _normals(db, cv)

    assert _normals(db, cv) == 0


# --- Coverage ----------------------------------------------------------------


def test_coverage_lists_what_is_still_open(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _derive(db, cv)
    _normals(db, cv)

    # The blood count is covered: Hb and RBC from day 0 carry forward to days 1-2.
    assert _missing(db, cv) == {
        "referral": ["REF.TOXICOLOGY"],
        "test": ["LAB.FILM"],
    }


def test_coverage_is_complete_once_everything_resolves(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _derive(db, cv)
    add_affected_cbc(db, cv)
    _normals(db, cv)
    db.execute(
        "insert into casevault.report (case_version_id, id, test_item_id, variant, status,"
        " findings, report_text, generator, skill_version)"
        " values (%s, 'RP01', 'LAB.FILM', 'only', 'final', '{FND.STIPPLING}',"
        " 'Coarse basophilic stippling.', 'g', 's')",
        (cv,),
    )
    db.execute(
        "insert into casevault.consult_note (case_version_id, id, specialty, note_text, origin,"
        " rationale, confidence, generator, skill_version)"
        " values (%s, 'CN01', 'REF.TOXICOLOGY', 'Happy to see her.', 'affected', 'r', 0.8,"
        " 'g', 's')",
        (cv,),
    )

    assert _missing(db, cv) == {}
    gaps = db.execute("select count(*) from casevault.coverage_gaps(%s)", (cv,)).fetchone()
    assert gaps == (0,)


def test_coverage_carries_the_latest_earlier_value_forward(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)

    rows = db.execute(
        "select item_id, component_id, day from casevault.coverage_gaps(%s)"
        " where item_id = 'LAB.CBC'",
        (cv,),
    ).fetchall()

    assert ("LAB.CBC", "CMP.RBC", 2) not in rows  # RBC day 0 answers a day-2 order
    assert ("LAB.CBC", "CMP.MCH", 1) in rows  # nothing derived yet


def test_coverage_leaves_the_days_before_the_first_value_open(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute("delete from casevault.fact where case_version_id = %s and id = 'L01'", (cv,))
    db.execute(
        "insert into casevault.synthetic_ledger (case_version_id, target, day_bucket, tier, value,"
        " rationale, confidence, generator, skill_version) values"
        " (%s, 'CMP.RBC', 2, 'affected', '{\"value\": 2.7}', 'Tracks Hb', 0.7, 'g', 'v0')",
        (cv,),
    )

    rows = db.execute(
        "select day from casevault.coverage_gaps(%s) where component_id = 'CMP.RBC' order by day",
        (cv,),
    ).fetchall()

    assert rows == [(0,), (1,)]


def test_normals_never_fill_a_component_the_case_has_measured(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute(
        "insert into casevault.fact (case_version_id, id, category, item, catalogue_ref, value,"
        " value_num, unit, day, origin, release, source_locator, generator, skill_version) values"
        " (%s, 'L99', 'chemistry', 'Sodium', 'CMP.NA', '131', 131, 'mmol/L', 1, 'article',"
        " 'chart', 'Table 9', 'g', 'v0')",
        (cv,),
    )

    _normals(db, cv)

    assert {t for t, _, _ in _ledger(db, cv)} >= {"CMP.K"}
    assert "CMP.NA" not in {t for t, _, _ in _ledger(db, cv)}
    gaps = db.execute(
        "select day from casevault.coverage_gaps(%s) where component_id = 'CMP.NA'", (cv,)
    ).fetchall()
    assert gaps == [(0,)]  # day 0 comes before the first value: Claude resolves it


# --- Consistency checks ------------------------------------------------------


def _checks(db: psycopg.Connection, cv: str) -> list[tuple[str, str]]:
    rows = db.execute(
        "select check_name, target from casevault.check_consistency(%s)", (cv,)
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def test_clean_case_has_no_findings(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _derive(db, cv)
    add_affected_cbc(db, cv)
    _normals(db, cv)

    assert _checks(db, cv) == []


def test_range_check_flags_an_abnormal_normal_row(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute(
        "insert into casevault.synthetic_ledger (case_version_id, target, day_bucket, tier, value,"
        " generator, skill_version)"
        " values (%s, 'CMP.K', 1, 'normal', '{\"value\": 7.0}', 'g', 's')",
        (cv,),
    )

    assert _checks(db, cv) == [("range", "CMP.K")]


def test_formula_check_flags_an_inconsistent_article_value(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute(
        "insert into casevault.fact (case_version_id, id, category, item, catalogue_ref, value,"
        " value_num, day, origin, release, source_locator, generator, skill_version)"
        " values (%s, 'L09', 'lab', 'MCH', 'CMP.MCH', '25', 25, 0, 'article', 'chart', 'T1',"
        " 'g', 's')",
        (cv,),
    )

    assert _checks(db, cv) == [("formula", "CMP.MCH")]


def test_physiology_checks(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    _derive(db, cv)
    # Nonsense rules that the fixture's day-0 values break: Hb 72 > RBC 2.4,
    # and RBC 2.4 + MCH 30 is not Hb 72.
    db.execute(
        "insert into casevault.value_rule (id, kind, target, inputs, formula) values"
        " ('P.ABOVE', 'not_above', 'CMP.HB', '{CMP.RBC}', 'test rule'),"
        " ('P.SUM', 'sum_equals', 'CMP.HB', '{CMP.RBC,CMP.MCH}', 'test rule')"
    )

    rows = db.execute(
        "select rule_id, target, day from casevault.check_consistency(%s)", (cv,)
    ).fetchall()

    assert rows == [("P.ABOVE", "CMP.HB", 0), ("P.SUM", "CMP.HB", 0)]


def test_contradiction_when_a_synthetic_row_overlaps_an_article_fact(
    db: psycopg.Connection,
) -> None:
    cv = seed_mini_case(db)
    db.execute(
        "insert into casevault.synthetic_ledger (case_version_id, target, day_bucket, tier, value,"
        " generator, skill_version)"
        " values (%s, 'CMP.HB', 0, 'normal', '{\"value\": 130}', 'g', 's')",
        (cv,),
    )

    assert ("contradiction", "CMP.HB") in _checks(db, cv)


# --- Leak scan ---------------------------------------------------------------


def _leaks(db: psycopg.Connection, cv: str) -> list[tuple[str, str]]:
    rows = db.execute("select location, term from casevault.leak_scan(%s)", (cv,)).fetchall()
    return [(r[0], r[1]) for r in rows]


def test_clean_case_has_no_leaks(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)

    assert _leaks(db, cv) == []


def test_leak_scan_finds_synonyms_and_catalogue_names(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute(
        "update casevault.case_version set vignette = 'Classic Plumbism.' where id = %s", (cv,)
    )
    db.execute(
        "update casevault.media set redacted_caption = 'Film showing saturnism.'"
        " where case_version_id = %s",
        (cv,),
    )

    assert _leaks(db, cv) == [
        ("case_version.vignette", "plumbism"),
        ("media", "saturnism"),
    ]


def test_test_names_are_allowed(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute(
        "update casevault.fact set release_text = 'Her GP checked a blood lead level.'"
        " where case_version_id = %s and id = 'H02'",
        (cv,),
    )

    assert _leaks(db, cv) == []


def test_confirmatory_results_are_not_scanned(db: psycopg.Connection) -> None:
    cv = seed_mini_case(db)
    db.execute(
        "update casevault.fact set release_text = 'Consistent with lead poisoning.'"
        " where case_version_id = %s and id = 'L02'",
        (cv,),
    )

    assert _leaks(db, cv) == []
