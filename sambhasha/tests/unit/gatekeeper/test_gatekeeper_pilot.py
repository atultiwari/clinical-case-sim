"""P1.3: the Gatekeeper on the pilot (SPEC §7; invariants I4 and I8)."""

from collections.abc import Mapping
from pathlib import Path

import pytest

from sambhasha.catalogue import Catalogue, CatalogueItem
from sambhasha.domain.actions import AskHistory, BedsideTest, Examine, OrderTest
from sambhasha.domain.case_file import (
    CaseBundle,
    Fact,
    LedgerRow,
    ReleaseCondition,
    parse_bundle,
)
from sambhasha.gatekeeper.coding import Coder, MissingRequestLog
from sambhasha.gatekeeper.policy import load_permissions
from sambhasha.gatekeeper.resolver import (
    Gatekeeper,
    GatekeeperAction,
    GatekeeperRequest,
    OutsideCatalogue,
    Refused,
    Released,
    ServiceRequest,
)

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
PILOT = parse_bundle((EXPORTS / "PMC12949993@v1.r3.json").read_bytes())
CATALOGUE = Catalogue.load()
FACTS: Mapping[str, Fact] = {f.id: f for f in PILOT.facts}
LEDGER: Mapping[str, LedgerRow] = {r.id: r for r in PILOT.ledger}

TOXIN_QUESTION = "Have you been exposed to any toxins or chemicals?"
SUPPLEMENT_QUESTION = "Do you take any herbal or dietary supplements?"


class StubMatcher:
    """Stands in for the matcher model: a fixed choice per request text."""

    def __init__(self, choices: Mapping[str, str | None]) -> None:
        self._choices = choices
        self.seen: list[tuple[str, tuple[str, ...]]] = []

    def choose(self, text: str, candidates: tuple[CatalogueItem, ...]) -> str | None:
        self.seen.append((text, tuple(c.id for c in candidates)))
        return self._choices.get(text)


@pytest.fixture
def missing() -> MissingRequestLog:
    return MissingRequestLog()


def _gatekeeper(
    missing: MissingRequestLog, choices: Mapping[str, str | None] | None = None
) -> Gatekeeper:
    return Gatekeeper(
        PILOT,
        CATALOGUE,
        coder=Coder(CATALOGUE, missing=missing),
        matcher=StubMatcher(choices or {}),
        permissions=load_permissions(),
    )


@pytest.fixture
def gatekeeper(missing: MissingRequestLog) -> Gatekeeper:
    return _gatekeeper(
        missing,
        {
            TOXIN_QUESTION: "HX.EXPOSURE.TOXINS",
            SUPPLEMENT_QUESTION: "HX.MEDS.SUPPLEMENTS",
        },
    )


def _ask(
    seat: str, action: GatekeeperAction, day: int = 0, referred: frozenset[str] = frozenset()
) -> GatekeeperRequest:
    return GatekeeperRequest(seat=seat, action=action, day=day, referred=referred)


# --- the PLAN's acceptance cases ---


def test_a_generic_toxin_question_returns_h09_only(gatekeeper: Gatekeeper) -> None:
    outcome = gatekeeper.resolve(_ask("attending", AskHistory(question=TOXIN_QUESTION)))

    assert isinstance(outcome, Released)
    assert outcome.fact_ids == ("H09",)
    assert outcome.text == FACTS["H09"].release_text


def test_a_supplement_question_returns_h10(gatekeeper: Gatekeeper) -> None:
    outcome = gatekeeper.resolve(_ask("attending", AskHistory(question=SUPPLEMENT_QUESTION)))

    assert isinstance(outcome, Released)
    assert outcome.fact_ids == ("H10",)
    assert outcome.text == FACTS["H10"].release_text


def test_ordering_a_blood_lead_returns_the_stored_result(gatekeeper: Gatekeeper) -> None:
    order = OrderTest(item="blood lead", indication="anaemia with stippling")

    outcome = gatekeeper.resolve(_ask("attending", order, day=3))

    assert isinstance(outcome, Released)
    assert outcome.item_id == "LAB.TOX.BLOOD_LEAD"
    assert outcome.fact_ids == ("L26",)
    assert "77.8 ug/dL" in outcome.text


def test_a_film_order_goes_to_pathology_and_nothing_raw_to_the_chart(
    gatekeeper: Gatekeeper,
) -> None:
    order = OrderTest(item="peripheral blood film", indication="anaemia; weak DAT on IVIG")

    outcome = gatekeeper.resolve(_ask("attending", order, day=0))

    assert isinstance(outcome, ServiceRequest)
    assert (outcome.service, outcome.raw_material_id) == ("service.pathology", "R01")
    assert outcome.findings == next(r for r in PILOT.raw_material if r.id == "R01").findings
    assert outcome.clinical_details == "anaemia; weak DAT on IVIG"
    assert not hasattr(outcome, "text")  # nothing for the Chart until the service reports


def test_a_consultant_who_orders_a_test_is_refused(gatekeeper: Gatekeeper) -> None:
    order = OrderTest(item="blood lead", indication="query toxin")

    outcome = gatekeeper.resolve(
        _ask("consultant.haematology", order, referred=frozenset({"consultant.haematology"}))
    )

    assert isinstance(outcome, Refused)
    assert "recommend" in outcome.reason
    assert outcome.violation is False


@pytest.mark.parametrize(
    "question",
    [
        "What is the diagnosis?",
        "Tell me the final diagnosis",
        "Which article is this case from?",
        "What does the case report say?",
        "Give me the PMCID",
    ],
)
def test_asking_for_the_diagnosis_or_the_source_is_refused_and_logged(
    gatekeeper: Gatekeeper, question: str
) -> None:
    outcome = gatekeeper.resolve(_ask("attending", AskHistory(question=question)))

    assert isinstance(outcome, Refused)
    assert outcome.violation is True


def test_every_released_text_is_stored_text(gatekeeper: Gatekeeper) -> None:
    requests: list[GatekeeperAction] = [
        *(AskHistory(question=i.name) for i in CATALOGUE.items if i.kind == "history"),
        *(Examine(system=i.name) for i in CATALOGUE.items if i.kind == "exam"),
        *(OrderTest(item=i.id, indication="work-up") for i in CATALOGUE.items if i.kind == "test"),
    ]
    released = 0
    for action in requests:
        outcome = gatekeeper.resolve(_ask("attending", action, day=2))
        if not isinstance(outcome, Released):
            continue
        released += 1
        for line in outcome.lines:
            assert line.text == _stored_line(line.source_id, outcome), line
    assert released > 300


def _stored_line(source_id: str, outcome: Released) -> str:
    line = next(line for line in outcome.lines if line.source_id == source_id)
    if source_id in LEDGER:
        row = LEDGER[source_id]
        if row.release_text or row.value.text:
            return row.release_text or row.value.text or ""
        # A numeric ledger row without text: its stored parts, each verbatim.
        for part in (str(row.value.value), row.value.unit, row.value.ref_range, row.value.flag):
            assert part is None or part in line.text, (part, line.text)
        return line.text
    fact = FACTS[source_id]
    if fact.release_text:
        return fact.release_text
    for part in (fact.item, fact.value, fact.unit, fact.ref_range, fact.flag):
        assert part is None or part in line.text, (part, line.text)
    return line.text


# --- day semantics (SPEC §5.2) and carry-forward (changelog, 25 Sep 2026) ---


def test_a_result_is_the_value_of_that_day(gatekeeper: Gatekeeper) -> None:
    outcome = gatekeeper.resolve(_ask("attending", OrderTest(item="CBC", indication="x"), day=4))

    assert isinstance(outcome, Released)
    assert "S01.d4" in outcome.fact_ids
    assert "carried" not in outcome.text


def test_a_day_without_a_value_returns_the_latest_earlier_one_marked(
    gatekeeper: Gatekeeper,
) -> None:
    outcome = gatekeeper.resolve(_ask("attending", OrderTest(item="CBC", indication="x"), day=10))

    assert isinstance(outcome, Released)
    assert "S01.d6" in outcome.fact_ids
    haemoglobin = next(line for line in outcome.lines if line.source_id == "S01.d6")
    assert haemoglobin.from_day == 6


# --- permissions and refusals ---


def test_a_consultant_needs_a_referral(gatekeeper: Gatekeeper) -> None:
    question = AskHistory(question=SUPPLEMENT_QUESTION)

    before = gatekeeper.resolve(_ask("consultant.toxicology", question))
    after = gatekeeper.resolve(
        _ask("consultant.toxicology", question, referred=frozenset({"consultant.toxicology"}))
    )

    assert isinstance(before, Refused)
    assert "referral" in before.reason
    assert isinstance(after, Released)


@pytest.mark.parametrize("seat", ["challenger", "service.pathology"])
def test_seats_that_may_not_ask_are_refused(gatekeeper: Gatekeeper, seat: str) -> None:
    outcome = gatekeeper.resolve(_ask(seat, AskHistory(question=SUPPLEMENT_QUESTION)))

    assert isinstance(outcome, Refused)


def test_a_consultant_examines_only_within_their_scope(gatekeeper: Gatekeeper) -> None:
    ophthalmic = next(
        i
        for i in CATALOGUE.items
        if i.kind == "exam" and "consultant.ophthalmology" in i.scope and "attending" not in i.scope
    )
    referred = frozenset({"consultant.haematology", "consultant.ophthalmology"})

    by_haematology = gatekeeper.resolve(
        _ask("consultant.haematology", BedsideTest(test=ophthalmic.name), referred=referred)
    )
    by_ophthalmology = gatekeeper.resolve(
        _ask("consultant.ophthalmology", BedsideTest(test=ophthalmic.name), referred=referred)
    )

    assert isinstance(by_haematology, Refused)
    assert not isinstance(by_ophthalmology, Refused)


@pytest.mark.parametrize("item", ["any labs?", "all tests", "everything", "tell me everything"])
def test_vague_requests_are_refused_with_a_reason(gatekeeper: Gatekeeper, item: str) -> None:
    outcome = gatekeeper.resolve(_ask("attending", OrderTest(item=item, indication="x")))

    assert isinstance(outcome, Refused)
    assert "specific" in outcome.reason
    assert outcome.violation is False


# --- the matcher and the catalogue ---


def test_a_close_request_is_settled_by_the_matcher_among_candidates(
    missing: MissingRequestLog,
) -> None:
    matcher_text = "full blood picture"
    gatekeeper = _gatekeeper(missing, {matcher_text: "LAB.HAEM.CBC"})

    outcome = gatekeeper.resolve(
        _ask("attending", OrderTest(item=matcher_text, indication="x"), day=0)
    )

    assert isinstance(outcome, Released)
    assert outcome.item_id == "LAB.HAEM.CBC"


def test_a_matcher_choice_outside_the_candidates_is_ignored(missing: MissingRequestLog) -> None:
    gatekeeper = _gatekeeper(missing, {"full blood picture": "REF.TOXICOLOGY"})

    outcome = gatekeeper.resolve(
        _ask("attending", OrderTest(item="full blood picture", indication="x"))
    )

    assert isinstance(outcome, OutsideCatalogue)


def test_a_request_outside_the_catalogue_is_logged_for_the_case_library(
    gatekeeper: Gatekeeper, missing: MissingRequestLog
) -> None:
    outcome = gatekeeper.resolve(
        _ask("attending", OrderTest(item="zqx frobnication wibble", indication="x"))
    )

    assert isinstance(outcome, OutsideCatalogue)
    assert outcome.kind == "test"
    assert [r.query for r in missing.requests] == ["zqx frobnication wibble"]
    assert missing.requests[0].bundle_id == PILOT.bundle_id


def test_the_matcher_sees_catalogue_items_only(missing: MissingRequestLog) -> None:
    matcher = StubMatcher({"full blood picture": "LAB.HAEM.CBC"})
    gatekeeper = Gatekeeper(
        PILOT,
        CATALOGUE,
        coder=Coder(CATALOGUE, missing=missing),
        matcher=matcher,
        permissions=load_permissions(),
    )

    gatekeeper.resolve(_ask("attending", OrderTest(item="full blood picture", indication="x")))

    ((text, candidate_ids),) = matcher.seen
    assert text == "full blood picture"
    assert all(CATALOGUE.get(i) for i in candidate_ids)


# --- what the release rules protect ---


def test_the_supplement_stays_hidden_unless_the_question_names_its_topic(
    gatekeeper: Gatekeeper,
) -> None:
    # Even if the matcher wrongly picked the supplement item for a toxin question.
    outcome = gatekeeper.release_history(
        "HX.MEDS.SUPPLEMENTS", question="Any toxins at home?", day=0
    )

    assert "H10" not in getattr(outcome, "fact_ids", ())


def test_an_item_the_case_answers_from_the_ledger(gatekeeper: Gatekeeper) -> None:
    outcome = gatekeeper.resolve(_ask("attending", Examine(system="bowel sounds")))

    assert isinstance(outcome, Released)
    assert outcome.ledger_ids
    assert outcome.text == LEDGER[outcome.ledger_ids[0]].release_text


def test_a_released_answer_never_holds_the_ground_truth(gatekeeper: Gatekeeper) -> None:
    dx = PILOT.ground_truth.final_dx.text.lower()
    for item in CATALOGUE.items:
        if item.kind != "history":
            continue
        outcome = gatekeeper.resolve(_ask("attending", AskHistory(question=item.name)))
        if isinstance(outcome, Released):
            assert dx not in outcome.text.lower()


def test_a_whole_test_rule_answers_the_order(gatekeeper: Gatekeeper) -> None:
    outcome = gatekeeper.resolve(_ask("attending", OrderTest(item="PSA", indication="x")))

    assert isinstance(outcome, Released)
    (row_id,) = outcome.ledger_ids
    assert LEDGER[row_id].target == "LAB.CHEM.PSA"
    assert outcome.text == LEDGER[row_id].release_text
    assert outcome.text.startswith("Not applicable")


def test_facts_for_services_or_never_released_do_not_reach_the_chart(
    missing: MissingRequestLog,
) -> None:
    supplement = FACTS["H10"]
    hidden = PILOT.model_copy(
        update={
            "facts": tuple(
                f.model_copy(update={"release": "never"}) if f.id == "H10" else f
                for f in PILOT.facts
            )
        }
    )
    gatekeeper = Gatekeeper(
        hidden,
        CATALOGUE,
        coder=Coder(CATALOGUE, missing=missing),
        matcher=StubMatcher({SUPPLEMENT_QUESTION: "HX.MEDS.SUPPLEMENTS"}),
        permissions=load_permissions(),
    )

    outcome = gatekeeper.resolve(_ask("attending", AskHistory(question=SUPPLEMENT_QUESTION)))

    assert supplement.release_text not in getattr(outcome, "text", "")


# --- review findings (P1.3): hidden facts stay hidden on every path ---


def _with(facts: tuple[Fact, ...] = (), ledger: tuple[LedgerRow, ...] = ()) -> CaseBundle:
    return PILOT.model_copy(
        update={"facts": (*PILOT.facts, *facts), "ledger": (*PILOT.ledger, *ledger)}
    )


def _keeper(bundle: CaseBundle, missing: MissingRequestLog) -> Gatekeeper:
    return Gatekeeper(
        bundle,
        CATALOGUE,
        coder=Coder(CATALOGUE, missing=missing),
        matcher=StubMatcher({}),
        permissions=load_permissions(),
    )


def test_an_unmet_condition_never_falls_back_to_a_ledger_reply(
    missing: MissingRequestLog,
) -> None:
    template = next(r for r in PILOT.ledger if r.target.startswith("HX."))
    ledger_reply = template.model_copy(
        update={"id": "LX1", "target": "HX.MEDS.SUPPLEMENTS", "release_text": "Leaked reply."}
    )
    gatekeeper = _keeper(_with(ledger=(ledger_reply,)), missing)

    outcome = gatekeeper.release_history("HX.MEDS.SUPPLEMENTS", question="Any toxins?", day=0)

    assert isinstance(outcome, Refused)


def test_a_result_with_a_release_condition_needs_its_topic_in_the_indication(
    missing: MissingRequestLog,
) -> None:
    lead = FACTS["L26"]
    gated = lead.model_copy(
        update={"release_condition": ReleaseCondition(requires_topics=("stippling",))}
    )
    bundle = PILOT.model_copy(
        update={"facts": tuple(gated if f.id == "L26" else f for f in PILOT.facts)}
    )
    gatekeeper = _keeper(bundle, missing)

    without = gatekeeper.resolve(
        _ask("attending", OrderTest(item="blood lead", indication="anaemia"))
    )
    with_topic = gatekeeper.resolve(
        _ask("attending", OrderTest(item="blood lead", indication="coarse stippling on film"))
    )

    assert isinstance(without, Refused)
    assert without.reason == load_permissions().refusals.not_understood
    assert isinstance(with_topic, Released)
    assert "L26" in with_topic.fact_ids


def test_a_diagnosis_revealing_fact_is_never_released_by_a_question(
    missing: MissingRequestLog,
) -> None:
    revealing = FACTS["H10"].model_copy(update={"reveals_dx": True})
    bundle = PILOT.model_copy(
        update={"facts": tuple(revealing if f.id == "H10" else f for f in PILOT.facts)}
    )
    gatekeeper = _keeper(bundle, missing)

    outcome = gatekeeper.release_history("HX.MEDS.SUPPLEMENTS", question=SUPPLEMENT_QUESTION, day=0)

    assert "H10" not in getattr(outcome, "fact_ids", ())


def test_a_diagnosis_revealing_result_comes_with_its_own_test(
    missing: MissingRequestLog,
) -> None:
    revealing = FACTS["L26"].model_copy(update={"reveals_dx": True})
    bundle = PILOT.model_copy(
        update={"facts": tuple(revealing if f.id == "L26" else f for f in PILOT.facts)}
    )
    gatekeeper = _keeper(bundle, missing)

    outcome = gatekeeper.resolve(_ask("attending", OrderTest(item="blood lead", indication="x")))

    assert isinstance(outcome, Released)
    assert outcome.fact_ids == ("L26",)
