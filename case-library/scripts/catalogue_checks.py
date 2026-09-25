"""The rules every catalogue must pass before it is built (catalogue/README.md, PLAN L0.4).

check(catalogue) returns one plain-English problem per line; an empty list means
the catalogue is clean.
"""

import re
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.catalogue import Catalogue, Row

ID_PATTERNS: Mapping[str, re.Pattern[str]] = {
    "history": re.compile(r"^HX\.[A-Z0-9_.]+$"),
    "exam": re.compile(r"^EX\.[A-Z0-9_.]+$"),
    "test": re.compile(r"^(LAB|IMG|PROC)\.[A-Z0-9_.]+$"),
    "action": re.compile(r"^(RX|ACT)\.[A-Z0-9_.]+$"),
    "referral": re.compile(r"^REF\.[A-Z0-9_.]+$"),
    "diagnosis": re.compile(r"^DX\.[A-Z0-9_.]+$"),
    "finding": re.compile(r"^FND\.[A-Z0-9_.]+$"),
    "component": re.compile(r"^CMP\.[A-Z0-9_.]+$"),
}
ROUTES = frozenset({"direct", "service.pathology", "service.radiology", "service.microbiology"})
SERVICES = frozenset({"service.pathology", "service.radiology", "service.microbiology"})
SEXES = frozenset({"F", "M", "any"})
BOOLEANS = frozenset({"true", "false"})
RULE_INPUTS: Mapping[str, Callable[[int], bool]] = {
    "ratio": lambda n: n == 2,
    "difference": lambda n: n >= 2,
    "not_above": lambda n: n == 1,
    "sum_equals": lambda n: n >= 2,
}
TEMPLATE_KINDS = frozenset({"history", "exam", "referral"})
ICD10 = re.compile(r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,2})?$")
ICD11 = re.compile(r"^[0-9A-Z]{4}(\.[0-9A-Z]{1,2})?([&/][0-9A-Z.&/]+)?$")
MIN_SYNONYMS = 2
MAX_DECIMALS = 6


def _split(cell: str) -> list[str]:
    return [part.strip() for part in cell.split("|") if part.strip()]


def _is_number(cell: str) -> bool:
    try:
        float(cell)
    except ValueError:
        return False
    return True


def _is_whole(cell: str) -> bool:
    return cell.isdigit()


def check(catalogue: "Catalogue") -> list[str]:
    """Every problem in the catalogue, one per line."""
    return [
        *_check_items(catalogue),
        *_check_tests(catalogue),
        *_check_components(catalogue),
        *_check_ranges(catalogue),
        *_check_diagnoses(catalogue),
        *_check_findings(catalogue),
        *_check_templates(catalogue),
        *_check_rules(catalogue),
    ]


def _check_items(catalogue: "Catalogue") -> Iterator[str]:
    ids = [row["id"] for _, row in catalogue.items()]
    ids += [row["id"] for row in catalogue.rows("components.csv")]
    for item_id, count in Counter(ids).items():
        if count > 1:
            yield f"{item_id}: the id is used twice"
    specialties = {
        "consultant." + row["id"].removeprefix("REF.").lower()
        for row in catalogue.rows("referrals.csv")
    }
    for kind, row in catalogue.items():
        yield from _check_item(kind, row, specialties)


def _check_item(kind: str, row: "Row", specialties: set[str]) -> Iterator[str]:
    item_id = row["id"]
    if not ID_PATTERNS[kind].match(item_id):
        yield f"{item_id}: the id does not fit the {kind} pattern {ID_PATTERNS[kind].pattern}"
    if not row["name"]:
        yield f"{item_id}: the name is empty"
    if not row["category"]:
        yield f"{item_id}: the category is empty"
    synonyms = _split(row["synonyms"])
    if len(synonyms) < MIN_SYNONYMS:
        yield f"{item_id}: needs at least two synonyms"
    folded = [s.casefold() for s in synonyms]
    if row["name"].casefold() in folded:
        yield f"{item_id}: a synonym repeats the name"
    if len(set(folded)) < len(folded):
        yield f"{item_id}: a duplicate synonym"
    scope = _split(row["specialty_scope"])
    allowed = {"attending", "consultant.*"} | specialties | SERVICES
    unknown = [s for s in scope if s not in allowed]
    if not scope or unknown:
        yield f"{item_id}: specialty scope {row['specialty_scope']!r} is not valid"


def _check_tests(catalogue: "Catalogue") -> Iterator[str]:
    components = {row["id"] for row in catalogue.rows("components.csv")}
    for row in catalogue.rows("tests.csv"):
        test_id = row["id"]
        if row["route"] not in ROUTES:
            yield f"{test_id}: route {row['route']!r} is not one of {sorted(ROUTES)}"
        if not _is_number(row["price_inr"]) or float(row["price_inr"]) < 0:
            yield f"{test_id}: price_inr {row['price_inr']!r} is not a price"
        if row["price_source"] != "estimate" and not row["price_source"].startswith("CGHS"):
            yield f"{test_id}: price_source must be 'estimate' or start with 'CGHS'"
        if not _is_whole(row["tat_minutes"]):
            yield f"{test_id}: tat_minutes {row['tat_minutes']!r} is not a whole number"
        if row["invasive"] not in BOOLEANS:
            yield f"{test_id}: invasive must be true or false"
        listed = _split(row["components"])
        if not listed:
            yield f"{test_id}: needs at least one component"
        for component_id, count in Counter(listed).items():
            if count > 1:
                yield f"{test_id}: lists {component_id} twice"
            if component_id not in components:
                yield f"{test_id}: component {component_id} is not in components.csv"


def _check_components(catalogue: "Catalogue") -> Iterator[str]:
    used = {c for row in catalogue.rows("tests.csv") for c in _split(row["components"])}
    ranges: dict[str, list[Row]] = {}
    for rng in catalogue.rows("component_ranges.csv"):
        ranges.setdefault(rng["component_id"], []).append(rng)
    for row in catalogue.rows("components.csv"):
        own = ranges.get(row["id"], [])
        yield from _check_component(row, own, used)


def _check_component(row: "Row", ranges: list["Row"], used: set[str]) -> Iterator[str]:
    cid = row["id"]
    if not ID_PATTERNS["component"].match(cid):
        yield f"{cid}: the id does not fit the component pattern"
    if not row["name"]:
        yield f"{cid}: the name is empty"
    if cid not in used:
        yield f"{cid}: no test lists this component"
    if not ranges:
        yield f"{cid}: needs at least one reference range"
    numeric = any(r["low"] or r["high"] for r in ranges) or bool(row["unit_si"])
    if numeric:
        if not row["unit_si"]:
            yield f"{cid}: a numeric component needs unit_si"
        if not _is_whole(row["decimals"]) or int(row["decimals"]) > MAX_DECIMALS:
            yield f"{cid}: decimals must be a whole number from 0 to {MAX_DECIMALS}"
    elif not row["normal_text"]:
        yield f"{cid}: a qualitative component needs normal_text"
    if row["unit_conv"] and not _is_number(row["conv_factor"]):
        yield f"{cid}: unit_conv needs a numeric conv_factor"
    if row["conv_factor"] and not _is_number(row["conv_factor"]):
        yield f"{cid}: conv_factor {row['conv_factor']!r} is not a number"


def _check_ranges(catalogue: "Catalogue") -> Iterator[str]:
    components = {row["id"]: row for row in catalogue.rows("components.csv")}
    for rng in catalogue.rows("component_ranges.csv"):
        cid = rng["component_id"]
        component = components.get(cid)
        if component is None:
            yield f"{cid}: has a range but is not in components.csv"
            continue
        yield from _check_range(cid, rng, numeric=bool(component["unit_si"]))


def _check_range(cid: str, rng: "Row", *, numeric: bool) -> Iterator[str]:
    if rng["sex"] not in SEXES:
        yield f"{cid}: range sex {rng['sex']!r} must be F, M or any"
    for field in ("age_min", "age_max"):
        if rng[field] and not _is_number(rng[field]):
            yield f"{cid}: range {field} {rng[field]!r} is not an age in years"
    if not rng["source"]:
        yield f"{cid}: range needs a source"
    if numeric:
        if not (_is_number(rng["low"]) and _is_number(rng["high"])):
            yield f"{cid}: a numeric range needs numeric low and high"
        elif float(rng["low"]) > float(rng["high"]):
            yield f"{cid}: range low {rng['low']} is above high {rng['high']}"
    elif not rng["text"]:
        yield f"{cid}: a qualitative range needs its normal text"


def _check_diagnoses(catalogue: "Catalogue") -> Iterator[str]:
    for row in catalogue.rows("diagnoses.csv"):
        if not ICD10.match(row["icd10"]):
            yield f"{row['id']}: icd10 {row['icd10']!r} is not an ICD-10 code"
        if row["icd11"] and not ICD11.match(row["icd11"]):
            yield f"{row['id']}: icd11 {row['icd11']!r} is not an ICD-11 code"
        if row["codes_verified"] not in BOOLEANS:
            yield f"{row['id']}: codes_verified must be true or false"


def _check_findings(catalogue: "Catalogue") -> Iterator[str]:
    tests = {row["id"] for row in catalogue.rows("tests.csv")}
    for row in catalogue.rows("findings.csv"):
        shown_by = _split(row["shown_by"])
        if not shown_by:
            yield f"{row['id']}: shown_by needs at least one test"
        for test_id in shown_by:
            if test_id not in tests:
                yield f"{row['id']}: shown_by names {test_id}, which is not in tests.csv"


def _check_templates(catalogue: "Catalogue") -> Iterator[str]:
    kinds = {row["id"]: kind for kind, row in catalogue.items()}
    templates = Counter(row["item_id"] for row in catalogue.rows("normal_templates.csv"))
    for row in catalogue.rows("normal_templates.csv"):
        if kinds.get(row["item_id"]) not in TEMPLATE_KINDS:
            yield f"{row['item_id']}: a normal template needs a history, exam or referral item"
        if not row["template"]:
            yield f"{row['item_id']}: the normal template is empty"
    for item_id, kind in kinds.items():
        if kind in TEMPLATE_KINDS and templates[item_id] != 1:
            yield f"{item_id}: needs exactly one normal template (has {templates[item_id]})"


def _check_rules(catalogue: "Catalogue") -> Iterator[str]:
    components = {row["id"] for row in catalogue.rows("components.csv")}
    for row in catalogue.rows("value_rules.csv"):
        rule_id, inputs = row["id"], _split(row["inputs"])
        accepts = RULE_INPUTS.get(row["kind"])
        if accepts is None:
            yield f"{rule_id}: kind {row['kind']!r} is not one of {sorted(RULE_INPUTS)}"
        elif not accepts(len(inputs)):
            yield f"{rule_id}: a {row['kind']} rule cannot take {len(inputs)} inputs"
        for component_id in [row["target"], *inputs]:
            if component_id not in components:
                yield f"{rule_id}: {component_id} is not in components.csv"
        for field in ("factor", "tolerance_pct"):
            if row[field] and not _is_number(row[field]):
                yield f"{rule_id}: {field} {row[field]!r} is not a number"
        if not row["formula"]:
            yield f"{rule_id}: the formula is empty"
