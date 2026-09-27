"""Evaluating the shared conditions on an encounter (Case Library SPEC §10.4).

An id ending in `.*` matches every id with that prefix; any other id matches only itself.
Every key present in a condition must hold.
"""

from collections.abc import Callable, Iterable

from sambhasha.domain.conditions import Condition
from sambhasha.evaluation.encounter import Encounter


def matches(pattern: str, item_id: str) -> bool:
    if pattern.endswith(".*"):
        return item_id.startswith(pattern[:-1])
    return item_id == pattern


def _any_of(patterns: Iterable[str], items: Iterable[str]) -> bool:
    pool = tuple(items)
    return any(matches(p, i) for p in patterns for i in pool)


def _all_of(patterns: Iterable[str], items: Iterable[str]) -> bool:
    pool = tuple(items)
    return all(any(matches(p, i) for i in pool) for p in patterns)


def _first(pattern: str, plan: tuple[str, ...]) -> int | None:
    return next((n for n, item in enumerate(plan) if matches(pattern, item)), None)


def _plan_before(pair: tuple[str, str], plan: tuple[str, ...]) -> bool:
    """A is planned before B, or in the same place in the list (together)."""
    first, second = (_first(p, plan) for p in pair)
    return first is not None and second is not None and first <= second


def _findings(condition: Condition, encounter: Encounter) -> bool:
    wanted = condition.finding_ids() or ()
    tests = condition.finding_tests()
    shown = [
        finding
        for finding, test in encounter.findings
        if tests is None or (test is not None and any(matches(t, test) for t in tests))
    ]
    return _all_of(wanted, shown)


def holds(condition: Condition, encounter: Encounter) -> bool:
    checks: list[Callable[[], bool]] = []
    c, e = condition, encounter
    if c.dx_in is not None:
        checks.append(lambda: e.dx_id is not None and _any_of(c.dx_in or (), (e.dx_id,)))
    if c.evidence_has is not None:
        checks.append(lambda: _all_of(c.evidence_has or (), e.evidence_items))
    if c.released_all is not None:
        checks.append(lambda: _all_of(c.released_all or (), e.released_items))
    if c.released_any is not None:
        checks.append(lambda: _any_of(c.released_any or (), e.released_items))
    if c.finding_released is not None:
        checks.append(lambda: _findings(c, e))
    if c.asked_any is not None:
        checks.append(lambda: _any_of(c.asked_any or (), e.asked))
    if c.ordered_any is not None:
        checks.append(lambda: _any_of(c.ordered_any or (), e.ordered))
    if c.ordered_all is not None:
        checks.append(lambda: _all_of(c.ordered_all or (), e.ordered))
    if c.referred_any is not None:
        checks.append(lambda: _any_of(c.referred_any or (), e.referred))
    if c.plan_has is not None:
        checks.append(lambda: _all_of(c.plan_has or (), e.plan))
    if c.plan_has_any is not None:
        checks.append(lambda: _any_of(c.plan_has_any or (), e.plan))
    if c.plan_before is not None:
        checks.append(lambda: _plan_before(c.plan_before or ("", ""), e.plan))
    if c.not_ is not None:
        checks.append(lambda: not holds(c.not_, e))  # type: ignore[arg-type]
    if c.all_ is not None:
        checks.append(lambda: all(holds(x, e) for x in c.all_ or ()))
    if c.any_ is not None:
        checks.append(lambda: any(holds(x, e) for x in c.any_ or ()))
    return all(check() for check in checks)
