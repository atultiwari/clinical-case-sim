"""What the scoring conditions are judged on: the run, reduced to catalogue ids (D-022)."""

from sambhasha.domain.base import DomainModel


class Encounter(DomainModel):
    dx_id: str | None  # the committed diagnosis, mapped
    evidence_items: frozenset[str]  # fact and ledger ids in the events the commit cited
    released_items: frozenset[str]  # fact and ledger ids released to the team
    asked: frozenset[str]  # history and examination items answered
    ordered: frozenset[str]  # tests ordered
    referred: frozenset[str]  # referrals made, as REF ids
    plan: tuple[str, ...]  # RX, ACT and REF ids in the committed plan, in order
    findings: tuple[tuple[str, str | None], ...]  # (FND id, the test whose report showed it)
