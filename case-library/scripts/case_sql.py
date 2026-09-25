"""Render a curated case as one SQL transaction for the Case Vault (PLAN L1.3).

    uv run python -m scripts.case_sql cases/PMC11227049 [...] --out build/batch1

Each file holds skill steps 4-9 and 11 for one case, in the order the replay
runs them (scripts/case_replay.py), inside one transaction. Before the
hand-over it runs the step 10 checks and raises if any is open, so either the
whole case lands in `in_review` with nothing open, or nothing is written. JSON
is ASCII-escaped, so copying the file cannot corrupt it. The file is data for
Atul to run (scripts/vault_load.py); this script connects to nothing.
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts import curate_plan as plan
from scripts.case_replay import AFTER_NORMALS, BEFORE_NORMALS, GENERATOR

ARTICLES = Path(__file__).resolve().parents[1] / "data" / "articles"

GUARD = """
do $guard$
declare
  v_open text;
begin
  select string_agg(k || ': ' || v, '; ') into v_open from (
    select 'consistency' as k, c.check_name || ' ' || c.target as v
    from casevault.check_consistency({cv}) c
    union all select 'leak', l.term from casevault.leak_scan({cv}) l
    union all select 'placeholder', p.row_id from casevault.placeholder_scan({cv}) p
    union all select 'coverage', coalesce(g.component_id, g.item_id)
    from casevault.coverage_gaps({cv}) g
  ) x;
  if v_open is not null then
    raise exception 'Case % not handed over; open problems: %', {cv}, left(v_open, 2000);
  end if;
end
$guard$;
"""


def _snippets() -> dict[str, str]:
    return {s.name: s.sql for s in plan.load_snippets()}


def _article(pmcid: str) -> tuple[str, str] | None:
    for name in ("efetch.jats.xml", "jats.xml"):
        path = ARTICLES / pmcid / name
        if path.exists():
            data = path.read_bytes()
            return data.decode("utf-8"), hashlib.sha256(data).hexdigest()
    return None


def render_case_body(case_dir: Path) -> str:
    """The case's writing calls, the step 10 guard and the hand-over, without a transaction."""
    gold = json.loads(next(case_dir.glob("gold-case-file*.json")).read_text(encoding="utf-8"))
    cv = f"{gold['case_id']}@v{gold.get('version', 1)}"
    base = {"cv": cv, "generator": GENERATOR, "skill_version": plan.skill_version()}
    curation = case_dir / "curation"
    snippets = _snippets()
    calls: list[tuple[str, dict[str, Any]]] = [("04_import.sql", {"doc": gold})]
    article = _article(gold["case_id"])
    if article:
        text, digest = article
        calls.append(
            (
                "04c_snapshot.sql",
                {
                    "pmcid": gold["case_id"],
                    "fulltext_format": "jats",
                    "fulltext": text,
                    "content_hash": digest,
                },
            )
        )
    calls.append(("08a_derived.sql", {}))
    for name, param, file in BEFORE_NORMALS:
        if (curation / file).exists():
            calls.append((name, {param: json.loads((curation / file).read_text("utf-8"))}))
    calls.append(("08c_normals.sql", {}))
    for name, param, file in AFTER_NORMALS:
        if (curation / file).exists():
            calls.append((name, {param: json.loads((curation / file).read_text("utf-8"))}))
    body = [
        f"-- {cv}: {name}\n{plan.render(snippets[name], {**base, **p}, ascii_json=True)}"
        for name, p in calls
    ]
    quoted_cv = plan.literal(cv)
    handover = plan.render(snippets["11_handover.sql"], base)
    return "\n".join(body) + GUARD.format(cv=quoted_cv) + handover


def render_case(case_dir: Path) -> str:
    """The case as one transaction: all of it lands in `in_review`, or none of it."""
    return "begin;\n" + render_case_body(case_dir) + "\ncommit;\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cases", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for case_dir in args.cases:
        sql = render_case(case_dir)
        path = args.out / f"{case_dir.name}.sql"
        path.write_text(sql, encoding="utf-8")
        print(f"Wrote {path} ({len(sql.encode('utf-8')):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
