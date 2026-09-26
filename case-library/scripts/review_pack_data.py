"""What a case review pack shows, fetched from the Case Vault with SELECTs only (SPEC §7.2).

PackData holds plain rows ({column: text}), one tuple per review area, so the
workbook writer can be tested from a JSON fixture without a database. Every row
carries a stable `key` ("<table>:<id>") that maps Atul's decision back to its row.
The queries live in scripts/review_pack_sql.py.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg

from scripts import review_pack_sql as sql

Row = Mapping[str, str]
Rows = tuple[Row, ...]
GROUND_TRUTH_PARTS = ("rubric", "must_do", "must_not_do")


class ReviewPackError(ValueError):
    """The pack cannot be built or read. The message says why."""


@dataclass(frozen=True)
class CaseSummary:
    """One case in the batch: status, source and licence flags (None for a de novo case)."""

    case_version_id: str
    status: str
    source: str
    licence: str
    production_ok: bool | None
    public_release_ok: bool | None
    origin_counts: Mapping[str, int]


@dataclass(frozen=True)
class PackData:
    batch: str
    cases: tuple[CaseSummary, ...]
    ledger: Rows  # live affected and reviewer rows; the writer splits off judgement calls
    normal_list: Rows
    article_facts: Rows
    patient_words: Rows
    reports_consults: Rows
    ground_truth: Rows
    leaks: Rows


ROW_FIELDS = tuple(f.name for f in fields(PackData) if f.name not in {"batch", "cases"})


def load_pack_data(path: Path) -> PackData:
    """A PackData from a JSON file (the test fixture's format)."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = tuple(CaseSummary(**case) for case in raw["cases"])
    rows = {name: tuple(dict(r) for r in raw.get(name, [])) for name in ROW_FIELDS}
    return PackData(batch=raw["batch"], cases=cases, **rows)


# --- formatting ----------------------------------------------------------------------------


def as_text(value: Any) -> str:
    """A database value as the text a reviewer reads."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def format_value(value: Any) -> str:
    """A ledger value ({"value": 75, "unit": ...} or {"text": ...}) as one line."""
    if isinstance(value, dict):
        if value.get("value") is not None:
            return f"{as_text(value['value'])} {value.get('unit') or ''}".strip()
        if value.get("text"):
            return str(value["text"])
    return as_text(value)


def format_range(low: Decimal | None, high: Decimal | None, unit: str | None) -> str:
    if low is None or high is None:
        return ""
    return f"{as_text(low)}-{as_text(high)} {unit or ''}".strip()


def _element_row(cv: str, part: str, element: Any, suffix: str) -> dict[str, str]:
    text, condition = as_text(element), ""
    if isinstance(element, dict):
        text = str(element.get("text", ""))
        if "score" in element:
            text = f"Score {element['score']}: {text}"
        condition = as_text(element.get("if"))
    return {
        "key": f"ground_truth:{cv}/{part}{suffix}",
        "case": cv,
        "part": part,
        "text": text,
        "condition": condition,
    }


def ground_truth_rows(cv: str, gt: Mapping[str, Any]) -> list[dict[str, str]]:
    """The final diagnosis, then each rubric anchor, must-do and must-not-do with its condition."""
    final = gt.get("final_dx") or {}
    rows = [
        {
            "key": f"ground_truth:{cv}/final_dx",
            "case": cv,
            "part": "final_dx",
            "text": str(final.get("text", "")),
            "condition": as_text({k: v for k, v in final.items() if k in {"id", "ids"}}),
        }
    ]
    for part in GROUND_TRUTH_PARTS:
        items = gt.get(part) or []
        if isinstance(items, dict):
            items = items.get(part, [items])
        rows += [_element_row(cv, part, e, f"/{n}") for n, e in enumerate(items, start=1)]
    return rows


# --- fetching ------------------------------------------------------------------------------


def _select(conn: psycopg.Connection[Any], query: str, params: Mapping[str, Any]) -> list[Any]:
    return conn.execute(query, params).fetchall()


def _texts(columns: Sequence[str], record: Sequence[Any]) -> dict[str, str]:
    return {column: as_text(value) for column, value in zip(columns, record, strict=True)}


def _params(cvs: list[str], pending_only: bool) -> dict[str, Any]:
    return {"cvs": cvs, "pending_only": pending_only}


def _cases(
    conn: psycopg.Connection[Any], cvs: list[str], pending_only: bool = False
) -> tuple[CaseSummary, ...]:
    counts: dict[str, dict[str, int]] = {cv: {} for cv in cvs}
    for cv, origin, count in _select(conn, sql.ORIGIN_COUNTS, _params(cvs, pending_only)):
        counts[cv][origin] = counts[cv].get(origin, 0) + count
    found = {r[0]: r for r in _select(conn, sql.CASES, {"cvs": cvs})}
    missing = [cv for cv in cvs if cv not in found]
    if missing:
        raise ReviewPackError("No such case version in the Case Vault: " + ", ".join(missing))
    summaries = []
    for cv in cvs:
        _, status, pmcid, licence, production_ok, public_ok = found[cv]
        summaries.append(
            CaseSummary(
                cv,
                status,
                pmcid or "de novo (no article)",
                licence or "",
                production_ok,
                public_ok,
                counts[cv],
            )
        )
    return tuple(summaries)


def _ledger(conn: psycopg.Connection[Any], cvs: list[str], pending_only: bool = False) -> Rows:
    rows = []
    for record in _select(conn, sql.LEDGER, _params(cvs, pending_only)):
        row = _texts(sql.LEDGER_COLUMNS, record[:-4])
        value, low, high, unit = record[-4:]
        rows.append(
            {**row, "value": format_value(value), "ref_range": format_range(low, high, unit)}
        )
    return tuple(rows)


def _plain(
    conn: psycopg.Connection[Any],
    query: str,
    columns: Sequence[str],
    cvs: list[str],
    pending_only: bool = False,
) -> Rows:
    return tuple(_texts(columns, r) for r in _select(conn, query, _params(cvs, pending_only)))


def _ground_truth(conn: psycopg.Connection[Any], cvs: list[str]) -> Rows:
    rows: list[dict[str, str]] = []
    for cv, gt in _select(conn, sql.GROUND_TRUTH, {"cvs": cvs}):
        rows += ground_truth_rows(cv, gt)
    return tuple(rows)


def _leaks(conn: psycopg.Connection[Any], cvs: list[str]) -> Rows:
    rows = []
    for cv in cvs:
        for location, row_id, term in _select(conn, sql.LEAKS, {"cv": cv}):
            rows.append(
                {
                    "key": f"leak_scan:{cv}/{location}/{row_id}/{term}",
                    "case": cv,
                    "location": location,
                    "row_id": row_id,
                    "term": term,
                }
            )
    return tuple(rows)


def fetch_pack_data(
    conn: psycopg.Connection[Any],
    case_version_ids: Sequence[str],
    batch: str = "",
    pending_only: bool = False,
) -> PackData:
    """Everything the pack shows for these case versions, read with SELECTs only.

    With `pending_only`, only the rows still awaiting review (the ground truth in full).
    """
    cvs = list(dict.fromkeys(case_version_ids))
    p = pending_only
    return PackData(
        batch=batch,
        cases=_cases(conn, cvs, p),
        ledger=_ledger(conn, cvs, p),
        normal_list=_plain(conn, sql.NORMAL_LIST, sql.NORMAL_LIST_COLUMNS, cvs, p),
        article_facts=_plain(conn, sql.ARTICLE_FACTS, sql.ARTICLE_FACT_COLUMNS, cvs, p),
        patient_words=_plain(conn, sql.PATIENT_WORDS, sql.PATIENT_WORDS_COLUMNS, cvs, p),
        reports_consults=_plain(conn, sql.REPORTS_CONSULTS, sql.REPORT_COLUMNS, cvs, p),
        ground_truth=_ground_truth(conn, cvs),
        leaks=_leaks(conn, cvs),
    )
