"""Checks on a generated result before anyone sees it (SPEC §8).

- leak: no diagnosis name or synonym (the P0.5 scanner, with the catalogue's terms);
- not_available: never "not available", or any way of saying so (D-009);
- consistency: no number that contradicts a value the case already holds for the same item.
"""

import re
from collections import defaultdict
from collections.abc import Mapping
from typing import Final

from sambhasha.curation.leakscan import Lexicon, find_leaks
from sambhasha.domain.case_file import CaseBundle

CHECKS: Final = ("leak", "not_available", "consistency")
_NOT_AVAILABLE: Final = re.compile(
    r"\bnot\s+available\b|\bunavailable\b|\bnot\s+(performed|done|measured|tested|reported)\b"
    r"|(?<![\w/])n/?a(?![\w/])|\bno\s+(result|data)\b",
    re.IGNORECASE,
)
_NUMBER: Final = re.compile(r"-?\d+(?:\.\d+)?")
_GAP_AFTER_NAME: Final = 24  # characters between an analyte's name and its number


def check_result(text: str, bundle: CaseBundle, lexicon: Lexicon) -> tuple[str, ...]:
    """Every problem with the text, as short reasons the generator is told on a retry."""
    problems = [f"leak: names {leak.term!r}" for leak in find_leaks(text, lexicon)]
    if _NOT_AVAILABLE.search(text):
        problems.append("not available: the result must give a finding, never its absence")
    problems += _contradictions(text, _stored_values(bundle))
    return tuple(problems)


def _stored_values(bundle: CaseBundle) -> Mapping[str, frozenset[float]]:
    """Every number the case holds, by item name (lower case)."""
    values: defaultdict[str, set[float]] = defaultdict(set)
    for fact in bundle.facts:
        for number in (fact.value_num, *_numbers(fact.value)):
            if number is not None:
                values[fact.item.lower()].add(float(number))
    return {name: frozenset(v) for name, v in values.items()}


def _numbers(text: str | None) -> tuple[float, ...]:
    return tuple(float(n) for n in _NUMBER.findall(text or ""))


def _contradictions(text: str, stored: Mapping[str, frozenset[float]]) -> list[str]:
    found = []
    for name, values in stored.items():
        pattern = re.compile(
            rf"(?<!\w){re.escape(name)}(?!\w)\D{{0,{_GAP_AFTER_NAME}}}?(-?\d+(?:\.\d+)?)",
            re.IGNORECASE,
        )
        for match in pattern.finditer(text):
            number = float(match.group(1))
            if number not in values:
                found.append(
                    f"contradicts the case: {name.capitalize()} {match.group(1)}"
                    " differs from every stored value"
                )
    return found
