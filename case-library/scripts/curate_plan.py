"""The case-curate skill's dry run: every step and the SQL it would run (SPEC §4.4, PLAN L0.6).

    uv run python -m scripts.curate_plan cases/PMC12949993
    uv run python -m scripts.curate_plan cases/PMC12949993 --json

It reads the skill's SQL snippets (.claude/skills/case-curate/sql/) and the case
folder's gold case file, and prints the plan. It never connects to a database.
Values that are only written during curation (path analysis, affected rows,
reports) appear as labelled placeholders. The same `render` fills the snippets
for real runs, whose SQL Claude sends through the Supabase MCP.
"""

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CASE_LIBRARY = Path(__file__).resolve().parents[1]
SKILL_DIR = CASE_LIBRARY / ".claude" / "skills" / "case-curate"
SQL_DIR = SKILL_DIR / "sql"
MODEL = "claude-opus-5-5"
PLACEHOLDER = re.compile(r"\{\{(\w+)(?::(jsonb|textarray))?\}\}")
HEADER = re.compile(r"^-- (step|writes|params): (.*)$", re.MULTILINE)
ELIDE_OVER = 400
GOLD_FILES = ("gold-case-file.json", "gold-case-file.draft.json")

# (number, name, what Claude does outside SQL). SPEC §4.4.
STEPS: tuple[tuple[int, str, str], ...] = (
    (1, "Identify", "Look up the PMCID, DOI and title; stop if the article is already here."),
    (
        2,
        "Licence",
        "Read the licence from PMC's OA service; stop unless CC0, CC BY, BY-SA, NC or "
        "ND; set production_ok and public_release_ok in the gold file's source block.",
    ),
    (
        3,
        "Fetch",
        "Fetch JATS XML through E-utilities, OAI-PMH or BioC within NCBI limits; cache "
        "it in data/articles/<PMCID>/ and compute its SHA-256.",
    ),
    (
        4,
        "Extract",
        "Write cases/<PMCID>/gold-case-file.json: atomic facts with day, unit, range, "
        "source locator and catalogue link; raw material; every figure with its licence and "
        "annotation flag. Import it, link history facts to the items that release them, store the "
        "snapshot.",
    ),
    (
        5,
        "Redact",
        "Remove the diagnosis from everything a player sees; write the vignette, the "
        "patient's opening words and a neutral title.",
    ),
    (
        6,
        "Ground truth",
        "Diagnosis, differential, red herrings, discriminators, rubric anchors, "
        "must-do and must-not-do as text plus conditions (SPEC §10.4). Imported with step 4; this "
        "snippet replaces it after a revision.",
    ),
    (
        7,
        "Path analysis",
        "Efficient, trap and alternative paths with every catalogue item on "
        "them (templates/path-analysis.md).",
    ),
    (
        8,
        "Resolve",
        "Derived values; affected and reviewer rows with rationale and confidence "
        "(SPEC §6.4); the normal generator; rule replies.",
    ),
    (
        9,
        "Author",
        "Report variants with status lines, consult notes, the patient's words, test utility.",
    ),
    (
        10,
        "Check",
        "Consistency, contradiction, leak scan and coverage; fix and repeat until "
        "every query returns nothing.",
    ),
    (
        11,
        "Hand over",
        "Set in_review; summarise counts per origin and the judgement calls "
        "(templates/case-summary.md).",
    ),
)


class PlanError(ValueError):
    """The plan cannot be built. The message says why."""


@dataclass(frozen=True)
class Snippet:
    name: str
    step: int
    writes: str
    params: tuple[str, ...]
    sql: str


@dataclass(frozen=True)
class Step:
    number: int
    name: str
    action: str
    snippets: tuple[Snippet, ...]


def placeholders(sql: str) -> list[str]:
    return sorted({m.group(1) for m in PLACEHOLDER.finditer(sql)})


def _parse(path: Path) -> Snippet:
    text = path.read_text(encoding="utf-8")
    header = {key: value.strip() for key, value in HEADER.findall(text)}
    try:
        step = int(header["step"].split()[0])
    except (KeyError, ValueError) as err:
        raise PlanError(f"{path.name}: needs a '-- step: <n> <name>' header line.") from err
    params = tuple(
        p.split(":")[0].strip() for p in header.get("params", "").split(",") if p.strip()
    )
    return Snippet(path.name, step, header.get("writes", ""), params, text)


def load_snippets(directory: Path = SQL_DIR) -> list[Snippet]:
    return [_parse(path) for path in sorted(directory.glob("*.sql"))]


def skill_version(skill_md: Path = SKILL_DIR / "SKILL.md") -> str:
    match = re.search(r"^version:\s*(\S+)\s*$", skill_md.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise PlanError(f"{skill_md} has no 'version:' line in its front matter.")
    return f"v{match.group(1).removeprefix('v')}"


def _quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def literal(value: Any, kind: str = "", *, ascii_json: bool = False) -> str:
    """A SQL literal for value: text, jsonb or text[]. ascii_json escapes JSON to pure ASCII."""
    if value is None:
        return "null"
    if kind == "jsonb":
        return _quote(json.dumps(value, ensure_ascii=ascii_json)) + "::jsonb"
    if kind == "textarray":
        return "array[" + ", ".join(_quote(str(v)) for v in value) + "]::text[]"
    return _quote(str(value))


def render(
    sql: str,
    params: Mapping[str, Any],
    *,
    placeholders_for_missing: bool = False,
    elide_over: int | None = None,
    ascii_json: bool = False,
) -> str:
    """Fill every {{name}}, {{name:jsonb}} and {{name:textarray}} with a quoted literal.

    ascii_json writes JSON with \\u escapes, so a copied or pasted file cannot corrupt it.
    """

    def fill(match: re.Match[str]) -> str:
        name, kind = match.group(1), match.group(2) or ""
        if name not in params:
            if not placeholders_for_missing:
                raise PlanError(f"No value for parameter {name!r}.")
            return literal(f"<{name}: written during this step>", "") + (
                "::jsonb" if kind == "jsonb" else ""
            )
        value = params[name]
        if kind == "jsonb" and elide_over is not None:
            size = len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
            if size > elide_over:
                return literal(f"<{name}: {size:,} bytes of JSON>") + "::jsonb"
        return literal(value, kind, ascii_json=ascii_json)

    return PLACEHOLDER.sub(fill, sql)


def _gold(case_dir: Path) -> dict[str, Any]:
    for name in GOLD_FILES:
        path = case_dir / name
        if path.exists():
            doc: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return doc
    raise PlanError(f"{case_dir} has no gold case file ({' or '.join(GOLD_FILES)}).")


def known_params(case_dir: Path) -> dict[str, Any]:
    """The parameters a dry run can fill before curation writes anything."""
    doc = _gold(case_dir)
    version = skill_version()
    source = doc.get("source") or {}
    return {
        "cv": f"{doc['case_id']}@v{doc.get('version', 1)}",
        "pmcid": source.get("pmcid") or doc["case_id"],
        "doc": doc,
        "ground_truth": doc.get("ground_truth"),
        "vignette": doc.get("vignette"),
        "opening_statement_lay": doc.get("opening_statement_lay"),
        "generator": f"{MODEL} via case-curate {version}",
        "skill_version": version,
    }


def build_plan(case_dir: Path) -> list[Step]:
    params = known_params(case_dir)
    by_step: dict[int, list[Snippet]] = {}
    for snippet in load_snippets():
        sql = render(snippet.sql, params, placeholders_for_missing=True, elide_over=ELIDE_OVER)
        by_step.setdefault(snippet.step, []).append(
            Snippet(snippet.name, snippet.step, snippet.writes, snippet.params, sql)
        )
    return [Step(n, name, action, tuple(by_step.get(n, []))) for n, name, action in STEPS]


def write_count(steps: Sequence[Step]) -> int:
    """How many MCP calls write (each one needs Atul's approval)."""
    return sum(1 for s in steps for snip in s.snippets if snip.writes != "nothing")


def _print(steps: Sequence[Step], case_dir: Path) -> None:
    print(
        f"Dry run: nothing is written. Case folder {case_dir}; "
        f"{write_count(steps)} writing calls, each needing an approval.\n"
    )
    for step in steps:
        print(f"Step {step.number} {step.name}\n  {step.action}")
        for snippet in step.snippets:
            print(f"\n  -- {snippet.name} (writes: {snippet.writes})")
            body = "\n".join(line for line in snippet.sql.splitlines() if not line.startswith("--"))
            print("\n".join("  " + line for line in body.strip().splitlines()))
        print()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--json", action="store_true", help="print the plan as JSON")
    args = parser.parse_args(argv)
    try:
        steps = build_plan(args.case_dir)
    except PlanError as err:
        print(err, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([asdict(s) for s in steps], ensure_ascii=False, indent=1))
    else:
        _print(steps, args.case_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
