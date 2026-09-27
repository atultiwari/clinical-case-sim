"""The Gatekeeper: releases stored case text on request, and refuses with a reason (SPEC §7).

For each history question, examination, bedside test or test order it:

1. checks the seat may take the action now (permissions, referral);
2. refuses a request for the diagnosis, the article or its source (a protocol violation),
   and a vague request ("any labs?");
3. codes the request to a catalogue item (P1.2), asking the matcher to choose among
   candidates when needed, and checks the item is within the seat's scope;
4. releases what the case holds for that item on that day: stored text only (invariant I4).
   Interpretive results go to a Diagnostic Service as raw material, never to the Chart.

A request the catalogue cannot answer comes back as `OutsideCatalogue`, for the Synthetic
Findings Service (P1.4); it is also logged as a missing request for the Case Library.
The Gatekeeper never reads the ground truth.
"""

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from sambhasha.catalogue import Catalogue, CatalogueItem, Kind
from sambhasha.domain.actions import AskHistory, BedsideTest, Examine, OrderTest
from sambhasha.domain.base import DomainModel
from sambhasha.domain.case_file import CaseBundle
from sambhasha.domain.seats import SeatId
from sambhasha.gatekeeper.coding import Coder, normalise
from sambhasha.gatekeeper.lookup import CaseIndex, Line
from sambhasha.gatekeeper.matcher import Matcher
from sambhasha.gatekeeper.policy import Permissions, in_scope

GatekeeperAction = AskHistory | Examine | BedsideTest | OrderTest

_PROTOCOL: Final = re.compile(
    r"\b(the|your|final|working|likely|underlying|actual|real)\s+diagnosis\b"
    r"|\bwhat\s+is\s+(the\s+)?(diagnosis|answer)\b|\bwhat'?s\s+wrong\b|\bwhat\s+is\s+wrong\b"
    r"|\barticle\b|\bcase\s+report\b|\b(the|which)\s+paper\b|\bjournal\b|\bpublication\b"
    r"|\bpmc\s*id\b|\bpmcid\b|\bpmc\d+|\bpmid\b|\bdoi\b|\bthe\s+answer\b",
    re.IGNORECASE,
)
_VAGUE: Final = re.compile(
    r"\beverything\b|\banything(\s+else)?\b|\bwhatever\b"
    r"|^\W*(any|all|every|other|more)\s+(the\s+)?"
    r"(labs?|tests?|investigations?|bloods?|results?|imaging|scans?)\W*$",
    re.IGNORECASE,
)
_ACTIONS: Final = MappingProxyType(
    {
        AskHistory: "ask_history",
        Examine: "examine",
        BedsideTest: "bedside_test",
        OrderTest: "order_test",
    }
)
_KINDS: Final[Mapping[type, tuple[Kind, ...]]] = MappingProxyType(
    {
        AskHistory: ("history",),
        Examine: ("exam",),
        BedsideTest: ("exam", "test"),
        OrderTest: ("test",),
    }
)


class GatekeeperRequest(DomainModel):
    seat: SeatId
    action: GatekeeperAction
    day: int  # the simulated day, relative to day 0
    referred: frozenset[str] = frozenset()  # the Consultant seats referred to so far


class Released(DomainModel):
    """Stored text for the Chart."""

    item_id: str
    lines: tuple[Line, ...]

    @property
    def text(self) -> str:
        return "\n".join(
            line.text + (f" (result from day {line.from_day})" if line.from_day is not None else "")
            for line in self.lines
        )

    @property
    def fact_ids(self) -> tuple[str, ...]:
        return tuple(line.source_id for line in self.lines if not line.is_ledger)

    @property
    def ledger_ids(self) -> tuple[str, ...]:
        return tuple(line.source_id for line in self.lines if line.is_ledger)


class ServiceRequest(DomainModel):
    """Sealed raw material for a Diagnostic Service; the Chart gets its report later."""

    item_id: str
    service: str
    clinical_details: str
    findings: str
    raw_material_id: str | None = None
    report_id: str | None = None  # the case's reviewed report, when it is the material
    media: tuple[str, ...] = ()
    ledger_ids: tuple[str, ...] = ()
    from_day: int | None = None
    released: Released | None = None  # the direct parts of a mixed test (an ECG's numbers)


class Refused(DomainModel):
    reason: str
    violation: bool = False  # a request for the diagnosis, the article or its source


class OutsideCatalogue(DomainModel):
    """The catalogue cannot answer this request; the Synthetic Findings Service may (P1.4)."""

    query: str
    kind: str


Outcome = Released | ServiceRequest | Refused | OutsideCatalogue


class Gatekeeper:
    def __init__(
        self,
        bundle: CaseBundle,
        catalogue: Catalogue,
        *,
        coder: Coder,
        matcher: Matcher,
        permissions: Permissions,
    ) -> None:
        self._bundle_id = bundle.bundle_id
        self._catalogue = catalogue
        self._coder = coder
        self._matcher = matcher
        self._permissions = permissions
        names = {item.id: item.name for item in catalogue.items}
        self._index = CaseIndex(bundle, names)

    def resolve(self, request: GatekeeperRequest) -> Outcome:
        action = request.action
        refusals = self._permissions.refusals
        refusal = self._permissions.check(request.seat, _ACTIONS[type(action)], request.referred)
        if refusal:
            return Refused(reason=refusal)
        text = _request_text(action)
        if _PROTOCOL.search(text):
            return Refused(reason=refusals.protocol, violation=True)
        if _VAGUE.search(text):
            return Refused(reason=refusals.vague)
        kinds = _KINDS[type(action)]
        if isinstance(action, Examine) and action.manoeuvre is None:
            system = self._system_examination(request.seat, action.system, request.day)
            if system is not None:
                return system
        named = self._identify_examination(action, kinds) if isinstance(action, Examine) else None
        item = named or self._identify(text, kinds)
        if isinstance(item, OutsideCatalogue):
            return item
        if not in_scope(request.seat, item.scope):
            return Refused(reason=refusals.out_of_scope)
        if item.kind == "test":
            indication = action.indication if isinstance(action, OrderTest) else ""
            return self._order(item, request.day, indication)
        return self.release_history(item.id, question=text, day=request.day)

    def release_history(self, item_id: str, *, question: str, day: int) -> Released | Refused:
        """What the case says for a history or examination item, honouring release conditions."""
        lines = self._index.answer(item_id, day, question)
        if not lines:
            return Refused(reason=self._permissions.refusals.not_understood)
        return Released(item_id=item_id, lines=lines)

    def _system_examination(self, seat: str, system: str, day: int) -> Released | None:
        """A whole system's examination ("abdomen"), or None if the text names no system."""
        config = self._permissions.system_examination
        if config is None:
            return None
        words = normalise(re.sub(r"(?i)\b(examin\w*|exam)\b", "", system))
        category = config.systems.get(words)
        if category is None:
            return None
        lines = tuple(
            line
            for item in self._catalogue.items
            if item.kind == "exam"
            and item.category == category
            and item.id not in config.explicit_only
            and in_scope(seat, item.scope)
            for line in self._index.answer(item.id, day, system)
        )
        return (
            Released(item_id=f"EX.SYSTEM.{category.upper().replace(' ', '_')}", lines=lines)
            if lines
            else None
        )

    def _identify_examination(
        self, action: Examine, kinds: tuple[Kind, ...]
    ) -> CatalogueItem | None:
        """A named manoeuvre first ("digital rectal examination"), if it is exactly an item."""
        if action.manoeuvre is None:
            return None
        coding = self._coder.code(action.manoeuvre, kinds=kinds, bundle_id=self._bundle_id)
        return self._catalogue.get(coding.ids[0]) if coding.status == "exact" else None

    def _identify(self, text: str, kinds: tuple[Kind, ...]) -> CatalogueItem | OutsideCatalogue:
        coding = self._coder.code(text, kinds=kinds, bundle_id=self._bundle_id)
        if coding.status == "exact":
            return self._catalogue.get(coding.ids[0])
        if coding.status == "candidates":
            candidates = tuple(self._catalogue.get(i) for i in coding.ids)
            choice = self._matcher.choose(text, candidates)
            if choice in coding.ids:
                return self._catalogue.get(choice)
            self._coder.record_missing(text, kinds=kinds, bundle_id=self._bundle_id)
        return OutsideCatalogue(query=text, kind="|".join(kinds))

    def _order(self, item: CatalogueItem, day: int, indication: str) -> Outcome:
        service = item.route if item.route and item.route.startswith("service.") else None
        reports = tuple(c for c in item.components if service and c.endswith("_REPORT"))
        direct = tuple(c for c in item.components if c not in reports)
        # A reply for the whole test (a rule such as "Not applicable") comes first.
        whole_test = self._index.answer(item.id, day, indication)
        if whole_test:
            return Released(item_id=item.id, lines=whole_test)
        lines = tuple(line for c in direct if (line := self._index.component(c, day, indication)))
        released = Released(item_id=item.id, lines=lines) if lines else None
        if service and reports:
            request = self._service_request(item, service, reports, day, indication, released)
            if request is not None:
                return request
        if released:
            return released
        if any(self._index.held_back(c, indication) for c in item.components):
            return Refused(reason=self._permissions.refusals.not_understood)
        self._coder.record_missing(item.id, kinds=("test",), bundle_id=self._bundle_id)
        return OutsideCatalogue(query=item.id, kind="test")

    def _service_request(
        self,
        item: CatalogueItem,
        service: str,
        reports: tuple[str, ...],
        day: int,
        indication: str,
        released: Released | None,
    ) -> ServiceRequest | None:
        """The material for the service: the article's raw material, else the case's reviewed
        report for the test, else the ledger's report text. None if the case holds none."""
        raw = self._index.raw_material(item.id, day)
        if raw is not None:
            from_day = raw.day if raw.day is not None and raw.day < day else None
            return ServiceRequest(
                item_id=item.id,
                service=service,
                clinical_details=indication,
                findings=raw.findings,
                raw_material_id=raw.id,
                media=raw.media,
                from_day=from_day,
                released=released,
            )
        report = self._index.report(item.id)
        if report is not None and report.report_text:
            return ServiceRequest(
                item_id=item.id,
                service=service,
                clinical_details=indication,
                findings=report.report_text,
                report_id=report.id,
                released=released,
            )
        lines = tuple(line for c in reports if (line := self._index.component(c, day, indication)))
        if not lines:
            return None
        return ServiceRequest(
            item_id=item.id,
            service=service,
            clinical_details=indication,
            findings="\n".join(line.text for line in lines),
            ledger_ids=tuple(line.source_id for line in lines),
            released=released,
        )


def _request_text(action: GatekeeperAction) -> str:
    if isinstance(action, AskHistory):
        return action.question
    if isinstance(action, Examine):
        return f"{action.system} {action.manoeuvre}" if action.manoeuvre else action.system
    if isinstance(action, BedsideTest):
        return action.test
    return action.item
