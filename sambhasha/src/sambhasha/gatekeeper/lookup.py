"""What a bundle holds for a catalogue item on a given day (SPEC §5.2, §7).

Every text here is stored text: a fact's or ledger row's release text, or its stored value,
unit, range and flag set side by side. Nothing is written, summarised or interpreted.

Day semantics: a request on day d gets the latest value dated on or before d. A value with
no day holds throughout the admission. If the latest value is from an earlier day, the line
records that day (the carry-forward rule, changelog 25 Sep 2026).
"""

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from types import MappingProxyType
from typing import Final

from sambhasha.domain.base import DomainModel
from sambhasha.domain.case_file import CaseBundle, Fact, LedgerRow, RawMaterial
from sambhasha.gatekeeper.coding import normalise

SEAT_RELEASES: Final = frozenset({"chart", "vignette"})
# Words too general to show that a question names a hidden item's topic.
_GENERIC_TOPIC_WORDS: Final = frozenset({"or", "and", "over", "the", "medicine", "drug"})


class Line(DomainModel):
    """One released line: which stored row it came from, its text, and an earlier day if any."""

    source_id: str
    text: str
    from_day: int | None = None
    is_ledger: bool = False


def fact_text(fact: Fact) -> str:
    if fact.release_text:
        return fact.release_text
    value = fact.value if fact.value is not None else _number(fact.value_num)
    return _join(fact.item, value, fact.unit, fact.ref_range, fact.flag)


def ledger_text(row: LedgerRow, name: str) -> str:
    if row.release_text or row.value.text:
        return row.release_text or row.value.text or ""
    return _join(
        name, _number(row.value.value), row.value.unit, row.value.ref_range, row.value.flag
    )


def _join(name: str, value: str | None, unit: str | None, ref: str | None, flag: str | None) -> str:
    text = f"{name}: {value or ''}"
    if unit:
        text += f" {unit}"
    if ref:
        text += f" ({ref})"
    if flag:
        text += f" [{flag}]"
    return text


def _number(value: object) -> str | None:
    return None if value is None else str(value)


def _dated(day: int | None, requested: int) -> bool:
    return day is None or day <= requested


def _latest[T](rows: Iterable[T], day_of: Callable[[T], int | None], requested: int) -> T | None:
    """The row for the requested day: the latest dated on or before it, else an undated one."""
    candidates = [r for r in rows if _dated(day_of(r), requested)]
    dated = [r for r in candidates if day_of(r) is not None]
    if dated:
        return max(dated, key=lambda r: day_of(r) or 0)
    return candidates[0] if candidates else None


def _fact_day(fact: Fact) -> int | None:
    return fact.day


def _ledger_day(row: LedgerRow) -> int | None:
    return row.day_bucket


def _raw_day(material: RawMaterial) -> int | None:
    return material.day


def topics_named(question: str, topics: Sequence[str]) -> bool:
    """Whether the question names one of a hidden fact's topics (its `requires_topics`)."""
    asked = set(normalise(question).split())
    for topic in topics:
        words = set(normalise(topic).split()) - _GENERIC_TOPIC_WORDS
        if asked & words:
            return True
    return False


class CaseIndex:
    """One bundle, indexed by catalogue id. Only seat-releasable rows are indexed."""

    def __init__(self, bundle: CaseBundle, names: Mapping[str, str]) -> None:
        self._names = names
        by_item: defaultdict[str, list[Fact]] = defaultdict(list)
        by_component: defaultdict[str, list[Fact]] = defaultdict(list)
        for fact in bundle.facts:
            if fact.release not in SEAT_RELEASES:
                continue
            for item_id in fact.released_by:
                by_item[item_id].append(fact)
            if fact.catalogue_ref:
                by_component[fact.catalogue_ref].append(fact)
        ledger: defaultdict[str, list[LedgerRow]] = defaultdict(list)
        for row in bundle.ledger:
            ledger[row.target].append(row)
        raw: defaultdict[str, list[RawMaterial]] = defaultdict(list)
        for material in bundle.raw_material:
            if material.test_item_id:
                raw[material.test_item_id].append(material)
        self._facts_by_item = MappingProxyType({k: tuple(v) for k, v in by_item.items()})
        self._facts_by_component = MappingProxyType({k: tuple(v) for k, v in by_component.items()})
        self._ledger = MappingProxyType({k: tuple(v) for k, v in ledger.items()})
        self._raw = MappingProxyType({k: tuple(v) for k, v in raw.items()})

    def answer(self, item_id: str, day: int, question: str) -> tuple[Line, ...]:
        """History and examination: the facts released by the item, else its ledger reply."""
        facts = [
            f
            for f in self._facts_by_item.get(item_id, ())
            if _dated(f.day, day) and _conditions_met(f, question)
        ]
        if facts:
            return tuple(Line(source_id=f.id, text=fact_text(f)) for f in facts)
        row = _latest(self._ledger.get(item_id, ()), _ledger_day, day)
        return () if row is None else (self._ledger_line(row, item_id, day),)

    def component(self, component_id: str, day: int) -> Line | None:
        """One result component on a day: the article's value, else the ledger's."""
        fact = _latest(self._facts_by_component.get(component_id, ()), _fact_day, day)
        if fact is not None:
            return Line(source_id=fact.id, text=fact_text(fact), from_day=_earlier(fact.day, day))
        row = _latest(self._ledger.get(component_id, ()), _ledger_day, day)
        return None if row is None else self._ledger_line(row, component_id, day)

    def raw_material(self, test_id: str, day: int) -> RawMaterial | None:
        return _latest(self._raw.get(test_id, ()), _raw_day, day)

    def _ledger_line(self, row: LedgerRow, target: str, day: int) -> Line:
        name = self._names.get(target, target)
        return Line(
            source_id=row.id,
            text=ledger_text(row, name),
            from_day=_earlier(row.day_bucket, day),
            is_ledger=True,
        )


def _earlier(value_day: int | None, requested: int) -> int | None:
    return value_day if value_day is not None and value_day < requested else None


def _conditions_met(fact: Fact, question: str) -> bool:
    condition = fact.release_condition
    if condition is None or not condition.requires_topics:
        return True
    return topics_named(question, condition.requires_topics)
