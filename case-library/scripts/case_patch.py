"""Correct a case already loaded into the Case Vault, before its review (PLAN L1.3).

    uv run python -m scripts.case_patch cases/PMC12643702 --since <git ref> --note "..." \\
        --out build/patches

The case as loaded (its files at the git ref) and the corrected case (its files
now) are both replayed on the local database in rolled-back transactions. The
normal generator is deterministic, so the difference between the two states is
exactly what the Case Vault needs. The patch is one transaction:

- content rows (facts, reports, consult notes, raw material, media, gaps, paths,
  test utility, ground truth, the version and case rows) are inserted, updated
  or deleted by key, which the Case Vault allows until a version is frozen;
- ledger rows are never deleted (the ledger is append-only): a changed value is
  a new pending row that supersedes the old one, and a row the corrected case no
  longer has is marked `rejected`, with the reviewer and note given here;
- the step 10 checks run at the end and undo everything if anything is open.

After the case has been reviewed (`--after-review`), approved ledger values
cannot be withdrawn, only replaced, so a corrected case that drops a (target,
day) is refused; and every content row the patch changes goes back to
`pending`, so the next review pack shows it.

It connects only to the local database; Atul runs the patch (scripts/vault_load.py).
"""

# The SQL here is built as text on purpose: it is a file for the Case Vault, and
# every value in it is quoted by curate_plan.literal.
# ruff: noqa: S608

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg

from scripts import curate_plan as plan
from scripts.case_replay import LOCAL_DB_URL, catalogue_document, replay_one
from scripts.case_sql import GUARD

REPO = Path(__file__).resolve().parents[2]
# Tables keyed by case version plus these columns, compared and patched row by row.
CONTENT: dict[str, tuple[str, ...]] = {
    "fact": ("id",),
    "raw_material": ("id",),
    "media": ("id",),
    "gap": ("id",),
    "report": ("id",),
    "consult_note": ("id",),
    "path_analysis": ("path_id",),
    "test_utility": ("test_item_id",),
    "ground_truth": (),
}
# Timestamps and generated keys differ between any two runs and carry no content.
VOLATILE = frozenset(
    {
        "created_at",
        "reviewed_at",
        "fetched_at",
        "curated_at",
        "decided_at",
        "frozen_at",
        "source_id",
    }
)
# Content tables whose rows carry a review, and the columns that record it.
REVIEWED_CONTENT = frozenset({"fact", "report", "consult_note"})
REVIEW_COLUMNS = ("review_status", "reviewed_by", "reviewed_at", "review_note")
REOPENED: dict[str, Any] = {
    "review_status": "pending",
    "reviewed_by": None,
    "reviewed_at": None,
    "review_note": None,
}
LEDGER_CONTENT = (
    "tier", "gap_id", "value", "release_text", "lay_text", "priority", "judgement_call",
    "rationale", "confidence", "checks",
)  # fmt: skip
LEDGER_COLUMNS = ", ".join(
    ("case_version_id", "target", "day_bucket", *LEDGER_CONTENT, "generator", "skill_version")
)
LIVE_ROW = (
    "(select l.id from casevault.synthetic_ledger l where l.case_version_id = {cv}"
    " and l.target = {t} and l.day_bucket is not distinct from {d}::int"
    " and casevault.is_live(l.review_status))"
)

Rows = dict[tuple[Any, ...], dict[str, Any]]
Snapshot = dict[str, Rows]


class PatchError(ValueError):
    """The corrected case cannot be reached by a patch the Case Vault accepts."""


@dataclass
class Patch:
    """Statements in order, with a count of each kind of change."""

    statements: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, kind: str, sql: str) -> None:
        self.statements.append(sql)
        self.counts[kind] = self.counts.get(kind, 0) + 1


def _git(*args: str) -> bytes:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is not on the PATH")
    return subprocess.run([git, "-C", str(REPO), *args], check=True, capture_output=True).stdout  # noqa: S603


def files_at(ref: str, case_dir: Path, into: Path) -> Path:
    """The case folder's JSON files as they were at a git ref, copied into `into`."""
    rel = case_dir.resolve().relative_to(REPO)
    out = into / case_dir.name
    for name in _git("ls-tree", "-r", "--name-only", ref, str(rel)).decode().split():
        if name.endswith(".json"):
            target = out / Path(name).relative_to(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_git("show", f"{ref}:{name}"))
    return out


def _one(db: psycopg.Connection, sql: str, param: str) -> dict[str, Any]:
    row = db.execute(sql, (param,)).fetchone()
    if row is None:
        raise LookupError(f"No row for {param}")
    return dict(row[0])


def snapshot(db: psycopg.Connection, cv: str, case_id: str) -> Snapshot:
    """Every content row and every live ledger row of a case version, as JSON."""
    snap: Snapshot = {}
    for table, key in CONTENT.items():
        rows = db.execute(
            f"select to_jsonb(t) from casevault.{table} t where case_version_id = %s", (cv,)
        ).fetchall()
        snap[table] = {tuple(r[0][k] for k in key): r[0] for r in rows}
    ledger = db.execute(
        "select to_jsonb(l) from casevault.synthetic_ledger l"
        " where case_version_id = %s and casevault.is_live(review_status)",
        (cv,),
    ).fetchall()
    snap["ledger"] = {(r[0]["target"], r[0]["day_bucket"]): r[0] for r in ledger}
    snap["case_version"] = {
        (cv,): _one(db, "select to_jsonb(v) from casevault.case_version v where id = %s", cv)
    }
    snap["case"] = {
        (case_id,): _one(db, 'select to_jsonb(c) from casevault."case" c where id = %s', case_id)
    }
    return snap


def same(a: dict[str, Any], b: dict[str, Any], columns: Sequence[str] | None = None) -> bool:
    """Whether two rows agree on the given columns, or on every column but the volatile ones."""
    keys = columns or [k for k in a.keys() | b.keys() if k not in VOLATILE]
    return all(a.get(k) == b.get(k) for k in keys)


def _changed(a: dict[str, Any], b: dict[str, Any], fixed: set[str]) -> list[str]:
    return [k for k in b if k not in VOLATILE | fixed and a.get(k) != b.get(k)]


def _json(value: Any) -> str:
    return plan.literal(value, "jsonb", ascii_json=True)


def _update(table: str, row: dict[str, Any], columns: list[str], where: str) -> str:
    sets = ", ".join(columns)
    return (
        f"update casevault.{table} set ({sets}) = (select {sets} from"
        f" jsonb_populate_record(null::casevault.{table}, {_json(row)})) where {where};"
    )


def _patch_header_rows(patch: Patch, old: Snapshot, new: Snapshot) -> None:
    for table, name in (("case", '"case"'), ("case_version", "case_version")):
        o, n = next(iter(old[table].values())), next(iter(new[table].values()))
        columns = _changed(o, n, {"status", "id"})
        if columns:
            where = f"id = {plan.literal(n['id'])}"
            patch.add(f"{table} updated", _update(name, n, columns, where))


def _patch_content(
    patch: Patch, old: Snapshot, new: Snapshot, cv_sql: str, after_review: bool = False
) -> None:
    for table, key in CONTENT.items():
        reopen = after_review and table in REVIEWED_CONTENT
        o, n = old[table], new[table]

        def where(row: dict[str, Any], key: tuple[str, ...] = key) -> str:
            keys = [f"{k} = {plan.literal(row[k])}" for k in key]
            return " and ".join([f"case_version_id = {cv_sql}", *keys])

        for k in o.keys() - n.keys():
            patch.add(f"{table} deleted", f"delete from casevault.{table} where {where(o[k])};")
        for k in n.keys() - o.keys():
            patch.add(
                f"{table} inserted",
                f"insert into casevault.{table} select * from"
                f" jsonb_populate_record(null::casevault.{table}, {_json(n[k])});",
            )
        for k in n.keys() & o.keys():
            columns = _changed(o[k], n[k], {"case_version_id", *key})
            if columns and reopen:
                reopened = {**n[k], **REOPENED}
                columns = [*columns, *(c for c in REVIEW_COLUMNS if c not in columns)]
                patch.add(f"{table} reopened", _update(table, reopened, columns, where(n[k])))
            elif columns:
                patch.add(f"{table} updated", _update(table, n[k], columns, where(n[k])))


def _patch_ledger(
    patch: Patch, old: Rows, new: Rows, cv_sql: str, reviewer: str, note: str
) -> None:
    def live(k: tuple[Any, ...]) -> str:
        day = "null" if k[1] is None else str(int(k[1]))
        return LIVE_ROW.format(cv=cv_sql, t=plan.literal(k[0]), d=day)

    for k in old.keys() - new.keys():
        patch.add(
            "ledger rejected",
            f"update casevault.synthetic_ledger set review_status = 'rejected',"
            f" reviewed_by = {plan.literal(reviewer)}, reviewed_at = now(),"
            f" review_note = {plan.literal(note)} where id = {live(k)};",
        )
    for k, row in new.items():
        if k in old and same(old[k], row, LEDGER_CONTENT):
            continue
        supersedes = "null"
        if k in old:
            patch.statements.append(
                "create temp table if not exists _old (id uuid) on commit drop; delete from _old;"
                f" insert into _old {live(k)[1:-1]};"
                " update casevault.synthetic_ledger set review_status = 'superseded'"
                " where id = (select id from _old);"
            )
            supersedes = "(select id from _old)"
        patch.add(
            "ledger superseded" if k in old else "ledger inserted",
            f"insert into casevault.synthetic_ledger ({LEDGER_COLUMNS}, supersedes)"
            f" select {LEDGER_COLUMNS}, {supersedes}"
            f" from jsonb_populate_record(null::casevault.synthetic_ledger, {_json(row)});",
        )


def patch_sql(
    old: Snapshot, new: Snapshot, cv: str, reviewer: str, note: str, after_review: bool = False
) -> Patch:
    """The statements that turn the `old` state into the `new` one, ending in the checks."""
    if after_review:
        dropped = sorted(old["ledger"].keys() - new["ledger"].keys(), key=str)
        if dropped:
            raise PatchError(
                f"{cv}: {len(dropped)} reviewed ledger value(s) would be withdrawn; after review"
                f" a value can only be replaced, so give each a corrected value: {dropped[:10]}"
            )
    cv_sql = plan.literal(cv)
    patch = Patch()
    _patch_header_rows(patch, old, new)
    _patch_content(patch, old, new, cv_sql, after_review)
    _patch_ledger(patch, old["ledger"], new["ledger"], cv_sql, reviewer, note)
    patch.statements.append(GUARD.format(cv=cv_sql))
    return patch


def render_patch(patch: Patch) -> str:
    return "begin;\n" + "\n".join(patch.statements) + "\ncommit;\n"


def build_patch(
    case_dir: Path, since: str, reviewer: str, note: str, after_review: bool = False
) -> Patch:
    """Replay the case at `since` and now, locally, and return the difference as a patch."""
    gold = json.loads(next(case_dir.glob("gold-case-file*.json")).read_text(encoding="utf-8"))
    cv, case_id = f"{gold['case_id']}@v{gold.get('version', 1)}", gold["case_id"]
    catalogue = json.dumps(catalogue_document([]))
    with (
        tempfile.TemporaryDirectory() as tmp,
        psycopg.connect(LOCAL_DB_URL, autocommit=True) as db,
        db.transaction(force_rollback=True),
    ):
        old_dir = files_at(since, case_dir, Path(tmp))
        db.execute("select casevault.load_catalogue(%s::jsonb)", (catalogue,))
        with db.transaction(force_rollback=True):
            replay_one(db, old_dir)
            old = snapshot(db, cv, case_id)
        with db.transaction(force_rollback=True):
            replay_one(db, case_dir)
            new = snapshot(db, cv, case_id)
    return patch_sql(old, new, cv, reviewer, note, after_review)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cases", nargs="+", type=Path)
    parser.add_argument("--since", required=True, help="git ref of the files that were loaded")
    parser.add_argument("--reviewer", default="atul")
    parser.add_argument("--note", required=True, help="review note on every rejected ledger row")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--after-review",
        action="store_true",
        help="the case has been reviewed: refuse withdrawn values, reopen changed rows",
    )
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for case_dir in args.cases:
        try:
            patch = build_patch(case_dir, args.since, args.reviewer, args.note, args.after_review)
        except PatchError as error:
            print(f"Not built: {error}", file=sys.stderr)
            return 1
        sql = render_patch(patch)
        path = args.out / f"{case_dir.name}.sql"
        path.write_text(sql, encoding="utf-8")
        print(f"Wrote {path} ({len(sql.encode('utf-8')):,} bytes): {patch.counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
