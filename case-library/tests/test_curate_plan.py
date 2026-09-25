"""scripts/curate_plan.py: the case-curate skill's dry run (PLAN L0.6)."""

import json
from pathlib import Path

import pytest

from scripts import curate_plan as plan

CASE_LIBRARY = Path(__file__).resolve().parents[1]
PILOT = CASE_LIBRARY / "cases" / "PMC12949993"


def test_every_snippet_declares_step_writes_and_params() -> None:
    snippets = plan.load_snippets()
    assert len(snippets) >= 15
    for snippet in snippets:
        assert 1 <= snippet.step <= 11, snippet.name
        assert snippet.writes, snippet.name
        assert set(snippet.params) == set(plan.placeholders(snippet.sql)), snippet.name


def test_the_skill_version_comes_from_skill_md() -> None:
    assert plan.skill_version() == "v0.1"


@pytest.mark.parametrize(
    ("kind", "value", "expected"),
    [
        ("", "O'Brien", "'O''Brien'"),
        ("", None, "null"),
        ("jsonb", {"a": "it's"}, "'{\"a\": \"it''s\"}'::jsonb"),
        ("textarray", ["a", "b'c"], "array['a', 'b''c']::text[]"),
    ],
)
def test_literals_are_quoted_safely(kind: str, value: object, expected: str) -> None:
    assert plan.literal(value, kind) == expected


def test_render_fills_every_placeholder() -> None:
    sql = "select {{cv}}, {{doc:jsonb}}, {{tags:textarray}};"
    rendered = plan.render(sql, {"cv": "X@v1", "doc": {"k": 1}, "tags": ["t"]})
    assert rendered == "select 'X@v1', '{\"k\": 1}'::jsonb, array['t']::text[];"


def test_render_refuses_a_missing_parameter() -> None:
    with pytest.raises(plan.PlanError, match="cv"):
        plan.render("select {{cv}};", {})


def test_placeholders_are_shown_for_values_written_later() -> None:
    rendered = plan.render("select {{paths:jsonb}};", {}, placeholders_for_missing=True)
    assert rendered == "select '<paths: written during this step>'::jsonb;"


def test_long_json_is_elided_in_a_dry_run() -> None:
    doc = {"facts": ["x" * 50] * 100}
    rendered = plan.render("select {{doc:jsonb}};", {"doc": doc}, elide_over=200)
    assert rendered.startswith("select '<doc: ")
    assert "bytes of JSON" in rendered


def test_the_pilot_dry_run_lists_all_eleven_steps() -> None:
    steps = plan.build_plan(PILOT)
    assert [s.number for s in steps] == list(range(1, 12))
    import_step = steps[3]
    assert [s.name for s in import_step.snippets] == [
        "04_import.sql",
        "04b_released_by.sql",
        "04c_snapshot.sql",
    ]
    assert "casevault.import_case_json('<doc: " in import_step.snippets[0].sql
    assert "'PMC12949993@v1'" in steps[6].snippets[0].sql
    assert steps[1].snippets == ()  # licence is read from PMC, not written
    assert plan.write_count(steps) >= 12


def test_the_dry_run_never_connects(monkeypatch: pytest.MonkeyPatch) -> None:
    import psycopg

    def refuse(*_: object, **__: object) -> None:
        raise AssertionError("the dry run must not connect")

    monkeypatch.setattr(psycopg, "connect", refuse)
    assert plan.main([str(PILOT)]) == 0


def test_cli_prints_steps_and_sql(capsys: pytest.CaptureFixture[str]) -> None:
    assert plan.main([str(PILOT)]) == 0
    out = capsys.readouterr().out
    assert "Dry run: nothing is written" in out
    assert "Step 11 Hand over" in out
    assert "status = 'in_review'" in out
    assert out.count("approval") >= 1


def test_cli_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert plan.main([str(PILOT), "--json"]) == 0
    steps = json.loads(capsys.readouterr().out)
    assert steps[0]["name"] == "Identify"


def test_a_folder_without_a_gold_file_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert plan.main([str(tmp_path)]) == 1
    assert "gold case file" in capsys.readouterr().err


def test_render_can_escape_json_to_ascii() -> None:
    sql = "select {{doc:jsonb}}"
    doc = {"text": "37 \u00b0C, \u03b1\u03b1/\u03b1\u03b1"}

    assert "°" in plan.render(sql, {"doc": doc})
    rendered = plan.render(sql, {"doc": doc}, ascii_json=True)
    assert rendered.isascii()
    assert "\\u00b0" in rendered
