"""The leak scanner: finds the diagnosis, or its synonyms, in text a seat could see (SPEC §9).

The Case Library scans every case before export (its `casevault.leak_scan`); the importer
scans again here as a second line of defence, with the same rules:

- terms are the ground truth's accepted synonyms and leak terms, the catalogue's names for
  the diagnosis, and any case-specific phrases the caller adds;
- matching ignores case and spacing and respects word boundaries ("plumbing" is not
  "plumbism");
- allowed phrases never count: every catalogue test name and synonym, and the case's own
  test and component names, so a term inside "blood lead" or "PNH flow cytometry" is no leak.
"""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import cached_property

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.domain.case_file import CaseBundle

MIN_TERM_LENGTH = 3


def _normalise(phrases: Iterable[str]) -> tuple[str, ...]:
    cleaned = (" ".join(p.lower().split()) for p in phrases)
    return tuple(dict.fromkeys(p for p in cleaned if len(p) >= MIN_TERM_LENGTH))


def _pattern(phrase: str) -> re.Pattern[str]:
    words = r"\s+".join(re.escape(word) for word in phrase.split())
    return re.compile(rf"(?<!\w){words}(?!\w)", re.IGNORECASE)


@dataclass(frozen=True)
class Leak:
    term: str
    start: int
    end: int


@dataclass(frozen=True)
class LeakFinding:
    """A leak in a bundle: where it is, which row, and which term."""

    location: str
    row_id: str
    term: str


@dataclass(frozen=True)
class Lexicon:
    """What counts as a leak for one case, and which phrases are allowed anyway."""

    terms: tuple[str, ...]
    allowed: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "terms", _normalise(self.terms))
        object.__setattr__(self, "allowed", _normalise(self.allowed))

    @classmethod
    def from_bundle(
        cls,
        bundle: CaseBundle,
        catalogue: CatalogueNames | None = None,
        *,
        extra_terms: Iterable[str] = (),
        extra_allowed: Iterable[str] = (),
    ) -> "Lexicon":
        final_dx = bundle.ground_truth.final_dx
        dx_ids = (final_dx.id, *(final_dx.ids or ()))
        case_test_names = (
            *(f.item for f in bundle.facts if f.category == "lab"),
            *(m.test for m in bundle.raw_material),
        )
        return cls(
            terms=(
                *final_dx.accepted_synonyms,
                *final_dx.leak_terms,
                *(catalogue.diagnosis(*dx_ids) if catalogue else ()),
                *extra_terms,
            ),
            allowed=(
                *case_test_names,
                *(catalogue.test_names if catalogue else ()),
                *extra_allowed,
            ),
        )

    @cached_property
    def _term_patterns(self) -> tuple[tuple[str, re.Pattern[str]], ...]:
        return tuple((term, _pattern(term)) for term in self.terms)

    @cached_property
    def _allowed_patterns(self) -> tuple[re.Pattern[str], ...]:
        return tuple(_pattern(phrase) for phrase in self.allowed)

    def allowed_spans(self, text: str) -> tuple[tuple[int, int], ...]:
        return tuple(m.span() for p in self._allowed_patterns for m in p.finditer(text))

    def term_matches(self, text: str) -> Iterator[Leak]:
        for term, pattern in self._term_patterns:
            for match in pattern.finditer(text):
                yield Leak(term, match.start(), match.end())


def find_leaks(text: str, lexicon: Lexicon) -> tuple[Leak, ...]:
    """Every leak in the text, in order. A match overlapping an allowed phrase is not one."""
    matches = tuple(lexicon.term_matches(text))
    if not matches:
        return ()
    allowed = lexicon.allowed_spans(text)  # only where a term matched: most texts have none
    leaks = (
        leak
        for leak in matches
        if not any(leak.start < end and start < leak.end for start, end in allowed)
    )
    return tuple(sorted(leaks, key=lambda leak: (leak.start, leak.end, leak.term)))


def seat_facing_texts(bundle: CaseBundle) -> Iterator[tuple[str, str, str]]:
    """(location, row id, text) for everything in a bundle that a seat could be shown.

    Not scanned: the ground truth, test utility and path analysis (never shown to seats,
    invariant I8), facts released `never`, confirmatory facts (`reveals_dx`), and the case's
    display title and tags, which are Nidana's and never reach a Sambhasha seat.
    """
    for location, text in (
        ("vignette", bundle.vignette),
        ("opening_statement_lay", bundle.opening_statement_lay),
    ):
        yield location, bundle.bundle_id, text or ""
    for fact in bundle.facts:
        if fact.release != "never" and not fact.reveals_dx:
            yield "fact", fact.id, _join(fact.value, fact.release_text, fact.lay_text)
    for row in bundle.ledger:
        value = row.value.value if isinstance(row.value.value, str) else None
        yield "ledger", row.id, _join(row.value.text, value, row.release_text, row.lay_text)
    for report in bundle.reports:
        yield "report", report.id, _join(report.report_text, report.impression, report.status_line)
    for note in bundle.consult_notes:
        yield "consult_note", note.id, _join(note.note_text, *note.recommendations)
    for figure in bundle.media:
        yield "media", figure.id, figure.redacted_caption or ""
    for material in bundle.raw_material:
        yield "raw_material", material.id, material.findings


def scan_bundle(bundle: CaseBundle, lexicon: Lexicon | None = None) -> tuple[LeakFinding, ...]:
    """Every leak in a bundle's seat-facing text, one finding per place and term."""
    lexicon = lexicon or Lexicon.from_bundle(bundle)
    findings = {
        LeakFinding(location, row_id, leak.term)
        for location, row_id, text in seat_facing_texts(bundle)
        for leak in find_leaks(text, lexicon)
    }
    return tuple(sorted(findings, key=lambda f: (f.location, f.row_id, f.term)))


def _join(*parts: str | None) -> str:
    return " | ".join(p for p in parts if p)
