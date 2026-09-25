"""Replay a case's curation on the local database and report what is still open (PLAN L1.3).

    uv run python -m scripts.case_replay cases/PMC11227049 [cases/... ...]

For each case folder it loads the catalogue from catalogue/*.csv (templates count
as approved), adds the case's proposed new items from `catalogue_needs.json` if
present, imports the gold case file and runs skill steps 7-9 from `curation/`,
exactly as the MCP calls will on the Case Vault. Then it runs the step 10 checks
and the placeholder scan. Everything happens in one transaction that is always
rolled back, on the local database only (CASE_LIBRARY_LOCAL_DB_URL, default the
local Supabase stack). Exit status 1 when any case has an open problem.
"""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg

from scripts import catalogue as cat
from scripts import curate_plan as plan

LOCAL_DB_URL = "postgresql://postgres:postgres@127.0.0.1:55322/postgres"
GENERATOR = "claude-opus-5-5 via case-curate v0.1"
NEEDS_FILE = "catalogue_needs.json"

# snippet, parameter, file in curation/; missing files are skipped and show up as gaps.
BEFORE_NORMALS: tuple[tuple[str, str, str], ...] = (
    ("07_path_analysis.sql", "paths", "paths.json"),
    ("08b_affected.sql", "rows", "affected.json"),
    ("08d_rules.sql", "rows", "rules.json"),
)
AFTER_NORMALS: tuple[tuple[str, str, str], ...] = (
    ("09a_reports.sql", "reports", "reports.json"),
    ("09b_consult_notes.sql", "notes", "consult_notes.json"),
    ("09c_lay_text.sql", "lay", "lay_text.json"),
    ("09d_test_utility.sql", "utility", "test_utility.json"),
    ("06_ground_truth.sql", "ground_truth", "ground_truth.json"),
)
CHECKS = """
select 'consistency', c.check_name || ' ' || coalesce(c.rule_id, '') || ' ' || c.target
       || ' day ' || coalesce(c.day::text, 'all') || ': ' || c.detail
from casevault.check_consistency(%(cv)s) c
union all
select 'leak', l.location || ' ' || l.row_id || ': ' || l.term from casevault.leak_scan(%(cv)s) l
union all
select 'placeholder', p.location || ' ' || p.row_id || ': ' || p.snippet
from casevault.placeholder_scan(%(cv)s) p
union all
select 'coverage', g.kind || ' ' || coalesce(g.component_id, g.item_id) || ' day '
       || coalesce(g.day::text, 'all')
from casevault.coverage_gaps(%(cv)s) g
"""


@dataclass(frozen=True)
class Replay:
    case_dir: Path
    case_version: str
    problems: list[tuple[str, str]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def _snippet(name: str) -> str:
    return next(s.sql for s in plan.load_snippets() if s.name == name)


def _run(db: psycopg.Connection, name: str, params: dict[str, Any]) -> None:
    with db.cursor() as cur:
        cur.execute(plan.render(_snippet(name), params))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def catalogue_document(case_dirs: Sequence[Path]) -> dict[str, Any]:
    """The CSV catalogue with templates approved, plus every case's proposed items."""
    document = cat.build_document(cat.read_catalogue(cat.DEFAULT_DIR), version=0)
    for template in document["normal_templates"]:
        template["review_status"] = "approved"
    for case_dir in case_dirs:
        needs_file = case_dir / NEEDS_FILE
        if not needs_file.exists():
            continue
        needs = _load_json(needs_file)
        for key, rows in needs.items():
            if isinstance(rows, list):
                document.setdefault(key, []).extend(rows)
    for template in document["normal_templates"]:
        template["review_status"] = "approved"
    return document


def _replay_one(db: psycopg.Connection, case_dir: Path) -> Replay:
    gold = _load_json(next(case_dir.glob("gold-case-file*.json")))
    cv = f"{gold['case_id']}@v{gold.get('version', 1)}"
    base = {"cv": cv, "generator": GENERATOR, "skill_version": "v0.1"}
    curation = case_dir / "curation"
    _run(db, "04_import.sql", {**base, "doc": gold})
    _run(db, "08a_derived.sql", base)
    for snippet, param, file in BEFORE_NORMALS:
        if (curation / file).exists():
            _run(db, snippet, {**base, param: _load_json(curation / file)})
    _run(db, "08c_normals.sql", base)
    for snippet, param, file in AFTER_NORMALS:
        if (curation / file).exists():
            _run(db, snippet, {**base, param: _load_json(curation / file)})
    problems = [(str(k), str(v)) for k, v in db.execute(CHECKS, {"cv": cv}).fetchall()]
    counts = {
        f"ledger {tier}": n
        for tier, n in db.execute(
            "select tier, count(*) from casevault.synthetic_ledger"
            " where case_version_id = %s group by tier",
            (cv,),
        ).fetchall()
    }
    return Replay(case_dir, cv, problems, counts)


def replay(db: psycopg.Connection, case_dirs: Sequence[Path]) -> list[Replay]:
    """Replay every case inside one rolled-back transaction."""
    results: list[Replay] = []
    with db.transaction(force_rollback=True):
        db.execute(
            "select casevault.load_catalogue(%s::jsonb)",
            (json.dumps(catalogue_document(case_dirs)),),
        )
        for case_dir in case_dirs:
            with db.transaction():
                results.append(_replay_one(db, case_dir))
    return results


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cases", nargs="+", type=Path)
    args = parser.parse_args(argv)
    url = os.environ.get("CASE_LIBRARY_LOCAL_DB_URL", LOCAL_DB_URL)
    with psycopg.connect(url, autocommit=True) as db:
        results = replay(db, args.cases)
    failed = False
    for r in results:
        print(f"== {r.case_version}: {len(r.problems)} open problem(s); {r.counts}")
        for kind, text in r.problems[:200]:
            print(f"  {kind}: {text}")
        failed = failed or bool(r.problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
