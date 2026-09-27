"""The Synthetic Findings Service (SPEC §8; D-009, D-010, D-023).

Only requests the catalogue cannot answer reach it; everything in the catalogue comes
pre-generated and reviewed in the bundle. For such a request it:

1. returns the stored row if the same request was answered before for this case and day;
2. refuses to generate for a gap marked `auto_generate: false` (the Case Reviewer sets it);
3. asks the synthetic model, which reads the ground truth, for the likeliest result;
4. checks it (leaks, "not available", contradictions) and regenerates with the reasons,
   up to MAX_RETRIES times;
5. stores the row, pending review, so the same request always gets the same result.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from pydantic import BaseModel, Field

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.leakscan import Lexicon
from sambhasha.domain.case_file import CaseBundle, Gap
from sambhasha.domain.synthetic import SyntheticRow
from sambhasha.gatekeeper.coding import normalise
from sambhasha.gatekeeper.resolver import OutsideCatalogue
from sambhasha.llm.gateway import LLMGateway, LLMOutputError
from sambhasha.llm.types import ChatMessage
from sambhasha.prompts import Prompt, load_prompt
from sambhasha.storage.repo import CaseRepository, DuplicateError
from sambhasha.synthetic.checks import CHECKS, check_result

MAX_RETRIES: Final = 2
MIN_GAP_COVERAGE: Final = 0.5  # share of a gap item's words the request must contain


class SyntheticReply(BaseModel):
    result_text: str = Field(min_length=1)
    rationale: str
    confidence: float = Field(ge=0, le=1)


@dataclass(frozen=True)
class Generated:
    row: SyntheticRow
    cached: bool

    @property
    def text(self) -> str:
        return self.row.result_text


@dataclass(frozen=True)
class HeldForReviewer:
    """The request matches a gap the Case Reviewer fills; nothing is generated."""

    gap_id: str
    query: str


@dataclass(frozen=True)
class GenerationFailed:
    query: str
    problems: tuple[str, ...]


SyntheticOutcome = Generated | HeldForReviewer | GenerationFailed


def request_code(query: str) -> str:
    return f"REQ:{normalise(query)}"


def match_gap(query: str, gaps: tuple[Gap, ...]) -> Gap | None:
    """The gap whose item the request covers best, if it covers at least half its words."""
    asked = set(normalise(query).split())
    best: tuple[float, Gap] | None = None
    for gap in gaps:
        words = set(normalise(gap.item).split())
        if not words:
            continue
        coverage = len(asked & words) / len(words)
        if coverage >= MIN_GAP_COVERAGE and (best is None or coverage > best[0]):
            best = (coverage, gap)
    return best[1] if best else None


class SyntheticService:
    def __init__(
        self,
        bundle: CaseBundle,
        repo: CaseRepository,
        gateway: LLMGateway,
        catalogue: CatalogueNames,
        prompt: Prompt | None = None,
    ) -> None:
        self._bundle = bundle
        self._repo = repo
        self._gateway = gateway
        self._lexicon = Lexicon.from_bundle(bundle, catalogue)
        self._prompt = prompt or load_prompt("synthetic")

    def answer(
        self, request: OutsideCatalogue, *, day: int, released: tuple[str, ...] = ()
    ) -> SyntheticOutcome:
        code = request_code(request.query)
        day_bucket = day if "test" in request.kind.split("|") else None
        stored = self._repo.get_synthetic(self._bundle.bundle_id, code, day_bucket)
        if stored is not None:
            return Generated(row=stored, cached=True)
        gap = match_gap(request.query, self._bundle.gaps)
        if gap is not None and not gap.auto_generate:
            return HeldForReviewer(gap_id=gap.id, query=request.query)
        return self._generate(request, code, day, day_bucket, gap, released)

    def _generate(
        self,
        request: OutsideCatalogue,
        code: str,
        day: int,
        day_bucket: int | None,
        gap: Gap | None,
        released: tuple[str, ...],
    ) -> SyntheticOutcome:
        messages: tuple[ChatMessage, ...] = (
            ChatMessage(role="system", content=self._prompt.text),
            ChatMessage(role="user", content=self._brief(request, day, gap, released)),
        )
        problems: tuple[str, ...] = ()
        for _attempt in range(MAX_RETRIES + 1):
            try:
                result = self._gateway.structured(
                    "synthetic", messages, SyntheticReply, prompt_version=self._prompt.version
                )
            except LLMOutputError as error:
                return GenerationFailed(query=request.query, problems=(str(error),))
            reply = result.value
            problems = check_result(reply.result_text, self._bundle, self._lexicon)
            if not problems:
                row = SyntheticRow(
                    bundle_id=self._bundle.bundle_id,
                    code=code,
                    day_bucket=day_bucket,
                    query=request.query.strip(),
                    kind=request.kind,
                    result_text=reply.result_text,
                    rationale=reply.rationale,
                    confidence=reply.confidence,
                    checks=CHECKS,
                    generator_model=result.calls[-1].model,
                    prompt_version=self._prompt.version,
                    gap_id=gap.id if gap else None,
                    created_at=datetime.now(UTC),
                )
                return self._store(row)
            messages = (
                *messages,
                ChatMessage(role="assistant", content=reply.model_dump_json()),
                ChatMessage(
                    role="user",
                    content="That result was rejected:\n- "
                    + "\n- ".join(problems)
                    + "\nWrite it again, following every rule.",
                ),
            )
        return GenerationFailed(query=request.query, problems=problems)

    def _store(self, row: SyntheticRow) -> Generated:
        try:
            self._repo.add_synthetic(row)
        except DuplicateError:
            # Another writer answered the same request first: theirs is the answer.
            stored = self._repo.get_synthetic(row.bundle_id, row.code, row.day_bucket)
            if stored is not None:
                return Generated(row=stored, cached=True)
            raise
        return Generated(row=row, cached=False)

    def _brief(
        self, request: OutsideCatalogue, day: int, gap: Gap | None, released: tuple[str, ...]
    ) -> str:
        truth = self._bundle.ground_truth
        profile = self._bundle.case.lab_profile
        parts = [
            f"True diagnosis: {truth.final_dx.text}",
            "Other findings in the truth: " + "; ".join(truth.final_dx.secondary_findings),
            "Key discriminators: " + "; ".join(truth.key_discriminators or ()),
            f"Patient: {profile.age_years if profile else '?'} years, "
            f"{profile.sex if profile else 'sex not recorded'}",
            f"Admission summary: {self._bundle.vignette or ''}",
            f"Day: {day} (day 0 is {self._bundle.clock.day_0_label or 'admission'})",
            "Already in the record:\n" + ("\n".join(f"- {r}" for r in released) or "- nothing yet"),
            f"Requested ({request.kind}): {request.query}",
        ]
        if gap is not None:
            parts.append(f"Gap guidance: {gap.guidance or 'none'}")
        return "\n\n".join(parts)
