"""The case bundle, schema 0.3 (Case Library SPEC §10; `case-bundle.v0.3.schema.json`).

A bundle is a frozen case version with its approved results. It holds the ground truth, so
it never reaches a seat (invariant I8); the Gatekeeper and the Evaluator read it.
"""

import json
import re
from collections import Counter
from datetime import date
from typing import Annotated, Any, Final, Literal, Self

from pydantic import AfterValidator, Field, StringConstraints, ValidationError, model_validator

from sambhasha.domain.base import DomainModel, NonEmptyStr
from sambhasha.domain.conditions import Condition, Rubric, ScoredItem

SCHEMA_VERSION: Final = "0.3"

_RELEASE = re.compile(r"vignette|chart|never|service\.[a-z_]+")
_SERIES_POINT = re.compile(r"[A-Z]+[0-9]+\.d-?[0-9]+")


def _check_release(value: str) -> str:
    if not _RELEASE.fullmatch(value):
        raise ValueError(
            f"unknown release {value!r}: expected vignette, chart, never or service.<department>"
        )
    return value


Release = Annotated[str, AfterValidator(_check_release)]
Day = int | None  # days from day 0; None means valid throughout the admission
FindingId = Annotated[str, StringConstraints(pattern=r"^FND\.")]


class BundleError(ValueError):
    """A bundle that Sambhasha cannot accept, with every problem listed."""


# --- case, source and clock ---


class ComponentRange(DomainModel):
    low: float | None = None
    high: float | None = None
    unit: str | None = None
    display: str | None = None


class LabProfile(DomainModel):
    """The case's own laboratory reference ranges, where they differ from the catalogue's."""

    age_years: int | None = None
    sex: str | None = None
    components: dict[str, ComponentRange] = Field(default_factory=dict)
    note: str | None = None
    source_note: str | None = None


class CaseInfo(DomainModel):
    slug: Annotated[str, StringConstraints(pattern=r"^c-[a-z0-9]{5}$")] | None = None
    display_title: str | None = None
    display_tags: tuple[str, ...] = ()
    specialty: str | None = None
    difficulty: str | None = None
    est_minutes: Annotated[int, Field(ge=1)] | None = None
    lab_profile: LabProfile | None = None


class Source(DomainModel):
    licence: NonEmptyStr
    production_ok: bool
    public_release_ok: bool
    citation: str | None = None
    doi: str | None = None
    pmcid: Annotated[str, StringConstraints(pattern=r"^PMC[0-9]+$")] | None = None
    url: str | None = None
    attribution: str | None = None


class Clock(DomainModel):
    day_0: date | None = None
    day_0_label: str | None = None


# --- facts and results ---


class ReleaseCondition(DomainModel):
    """Extra conditions on a fact's release (SPEC §5.4). Unknown keys are errors, so that
    the Gatekeeper never silently ignores a rule it does not understand."""

    requires_topics: tuple[NonEmptyStr, ...] | None = None
    answers: str | None = None
    note: str | None = None


class Fact(DomainModel):
    id: NonEmptyStr
    category: NonEmptyStr
    item: NonEmptyStr
    origin: Literal["article", "derived"]
    release: Release
    day: Day
    catalogue_ref: str | None = None
    released_by: tuple[str, ...] = ()
    code_system: str | None = None
    code: str | None = None
    value: str | None = None
    value_num: float | None = None
    unit: str | None = None
    ref_range: str | None = None
    flag: str | None = None
    kind: Literal["raw", "interpretation"] | None = None
    formula: str | None = None
    reveals_dx: bool = False
    pivotal: bool = False
    release_condition: ReleaseCondition | None = None
    release_text: str | None = None
    lay_text: str | None = None
    source_locator: str | None = None


class LedgerValue(DomainModel):
    """A pre-generated result: a number or text with its unit and range, or a text reply."""

    value: int | float | str | None = None
    unit: str | None = None
    ref_range: str | None = None
    flag: str | None = None
    text: str | None = None

    @model_validator(mode="after")
    def _has_content(self) -> Self:
        if self.value is None and self.text is None:
            raise ValueError("a ledger value needs a value or a text")
        return self


class LedgerRow(DomainModel):
    id: NonEmptyStr
    target: NonEmptyStr
    day_bucket: Day
    tier: Literal["affected", "normal", "rule", "reviewer"]
    value: LedgerValue
    gap_id: str | None = None
    release_text: str | None = None
    lay_text: str | None = None


class Report(DomainModel):
    """A pre-written Diagnostic Service report variant."""

    id: NonEmptyStr
    variant: Literal["original", "expert", "only"]
    status: Literal["provisional", "final"]
    findings: tuple[FindingId, ...]
    test_item_id: str | None = None
    status_line: str | None = None
    report_text: str | None = None
    impression: str | None = None
    suggested_reflex: tuple[str, ...] = ()
    based_on: tuple[str, ...] = ()
    origins: tuple[Literal["article", "affected", "normal", "rule", "reviewer"], ...] = ()

    @model_validator(mode="after")
    def _original_is_provisional(self) -> Self:
        if self.variant == "original" and (self.status != "provisional" or not self.status_line):
            raise ValueError("an original report is provisional and has a status_line")
        return self


class ConsultNoteTemplate(DomainModel):
    """A pre-written consult note, used when its condition holds."""

    id: NonEmptyStr
    specialty: NonEmptyStr
    variant: Annotated[int, Field(ge=1)]
    note_text: NonEmptyStr
    origin: Literal["affected", "rule"]
    condition: Condition | None = None
    recommendations: tuple[str, ...] = ()


class RawMaterial(DomainModel):
    """What a Diagnostic Service receives for an interpretive test (SPEC §5.3)."""

    id: NonEmptyStr
    test: NonEmptyStr
    release: Release
    findings: str
    test_item_id: str | None = None
    day: Day = None
    media: tuple[str, ...] = ()
    note: str | None = None
    source_locator: str | None = None


class Media(DomainModel):
    id: NonEmptyStr
    licence: NonEmptyStr
    production_ok: bool
    public_release_ok: bool
    has_annotations: bool
    production_decision: Literal["pending", "use", "mask", "exclude"]
    figure: str | None = None
    specimen: str | None = None
    stain: str | None = None
    file_path: str | None = None
    redacted_caption: str | None = None
    masked_path: str | None = None
    raw_fact_id: str | None = None


class Gap(DomainModel):
    id: NonEmptyStr
    item: NonEmptyStr
    guidance: str | None = None
    review_required: bool = False
    auto_generate: bool = True


# --- ground truth and analysis (Evaluator only) ---


class FinalDiagnosis(DomainModel):
    id: NonEmptyStr
    text: NonEmptyStr
    ids: tuple[str, ...] | None = None
    accepted_synonyms: tuple[str, ...] = ()
    icd10: tuple[str, ...] = ()
    secondary_findings: tuple[str, ...] = ()
    leak_terms: tuple[str, ...] = ()


class GroundTruth(DomainModel):
    final_dx: FinalDiagnosis
    accepted_differential: tuple[str, ...] | None = None
    red_herrings: tuple[str, ...] | None = None
    key_discriminators: tuple[str, ...] | None = None
    rubric: Rubric | None = None
    must_do: tuple[ScoredItem, ...] | None = None
    must_not_do: tuple[ScoredItem, ...] | None = None
    efficient_path: tuple[str, ...] | None = None
    teaching_points: tuple[str, ...] | None = None
    treatment_given: str | None = None
    outcome: str | None = None


class TestUtility(DomainModel):
    __test__ = False  # not a pytest class

    test_item_id: NonEmptyStr
    utility: Literal["essential", "supportive", "low_yield", "unnecessary", "risky"]
    rationale: str | None = None


class PathAnalysis(DomainModel):
    path_id: NonEmptyStr
    kind: Literal["efficient", "trap", "alternative"]
    name: NonEmptyStr
    items: tuple[str, ...]
    rationale: str | None = None


# --- the bundle ---

_ID_COLLECTIONS: Final = (
    "facts",
    "ledger",
    "reports",
    "consult_notes",
    "raw_material",
    "media",
    "gaps",
)


class CaseBundle(DomainModel):
    bundle_id: Annotated[
        str, StringConstraints(pattern=r"^(PMC[0-9]+|NID-[0-9]{4,})@v[0-9]+\.r[0-9]+$")
    ]
    schema_version: Literal["0.3"]
    catalogue_version: Annotated[int, Field(ge=0)]
    case: CaseInfo
    source: Source | None
    clock: Clock
    vignette: str | None
    opening_statement_lay: str | None
    facts: tuple[Fact, ...]
    ledger: tuple[LedgerRow, ...]
    reports: tuple[Report, ...]
    consult_notes: tuple[ConsultNoteTemplate, ...]
    raw_material: tuple[RawMaterial, ...]
    media: tuple[Media, ...]
    gaps: tuple[Gap, ...]
    ground_truth: GroundTruth
    test_utility: tuple[TestUtility, ...]
    path_analysis: tuple[PathAnalysis, ...]

    @model_validator(mode="after")
    def _ids_are_unique(self) -> Self:
        problems = []
        for name in _ID_COLLECTIONS:
            counts = Counter(row.id for row in getattr(self, name))
            problems += [f"duplicate id {i!r} in {name}" for i, n in counts.items() if n > 1]
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def series_points(self) -> tuple[Fact, ...]:
        """Article facts that are one day of a serial result, such as `S01.d0`."""
        return tuple(
            f for f in self.facts if f.origin == "article" and _SERIES_POINT.fullmatch(f.id)
        )


def parse_bundle(raw: bytes | str) -> CaseBundle:
    """Validate a bundle file's contents strictly (no type coercion) or raise BundleError."""
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        raise BundleError(f"the bundle is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise BundleError("a bundle must be a JSON object")
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise BundleError(
            f"unsupported schema_version {version!r}: Sambhasha reads schema {SCHEMA_VERSION}"
        )
    try:
        return CaseBundle.model_validate_json(raw, strict=True)
    except ValidationError as error:
        lines = [f"{_path(e['loc'])}: {e['msg']}" for e in error.errors()]
        raise BundleError(
            f"invalid bundle ({len(lines)} problems):\n" + "\n".join(lines)
        ) from error


def _path(loc: tuple[int | str, ...]) -> str:
    path = ""
    for part in loc:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path.lstrip(".") or "bundle"
