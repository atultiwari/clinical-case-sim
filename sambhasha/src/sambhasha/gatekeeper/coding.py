"""Coding request text to catalogue ids (D-022; SPEC §7, "Matching").

The Gatekeeper looks a seat's request up in the catalogue's names and synonyms first:

1. **exact**: the normalised text is one item's name or synonym, or the same words in any
   order. The Gatekeeper uses that id directly.
2. **candidates**: otherwise, the items whose names share the most words with the request,
   ranked. The matcher model chooses among them (P1.3); it never writes its own answer.
3. **unmatched**: nothing shares a word. The request is logged as a missing request for the
   Case Library, which may add the item to the catalogue.

Normalisation is the same for the request and for every name, so it only has to be
consistent: case, accents, punctuation, word order, plurals, British and American spelling
("haemoglobin", "hemoglobin"), filler words ("level", "test", "please"), a leading article
and the symbol "Pb" all stop mattering; "%" reads as "percent". A test checks that
normalising adds no ambiguity the catalogue does not already have.
"""

import csv
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal

from sambhasha.catalogue import Catalogue, CatalogueItem, Kind, kind_of
from sambhasha.domain.base import DomainModel

MAX_CANDIDATES: Final = 10
MIN_OVERLAP: Final = 0.34  # share of words in common for a candidate (Jaccard)

_FILLER: Final = frozenset(
    [
        "please",
        "pls",
        "kindly",
        "send",
        "order",
        "ordered",
        "check",
        "do",
        "get",
        "for",
        "of",
        "on",
        "to",
        "and",
        "level",
        "levels",
        "test",
        "tests",
        "measure",
        "measurement",
    ]
)
_ARTICLES: Final = frozenset({"a", "an", "the"})  # dropped only at the start: "haemoglobin A"
_ABBREVIATIONS: Final = MappingProxyType({"pb": "lead"})
_SPELLING: Final = (
    (re.compile(r"^oes"), "es"),  # oesophagus, oestrogen
    (re.compile(r"^oed"), "ed"),  # oedema
    (re.compile(r"^paed"), "ped"),  # paediatric
    (re.compile(r"aem"), "em"),  # haem-, anaemia, leukaemia, septicaemia
    (re.compile(r"our$"), "or"),  # tumour, colour
)
_PLURAL_KEEP: Final = ("ss", "us", "is", "ys")
_ITEM_ID: Final = re.compile(r"[A-Z]+\.[A-Z0-9_.]+")


def _token(word: str) -> str:
    word = _ABBREVIATIONS.get(word, word)
    for pattern, replacement in _SPELLING:
        word = pattern.sub(replacement, word)
    if len(word) >= 5 and word.endswith("s") and not word.endswith(_PLURAL_KEEP):
        word = word[:-1]
    return word


def normalise(text: str) -> str:
    """The comparable form of a request or a catalogue name."""
    plain = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in plain if not unicodedata.combining(c)).lower()
    words = re.sub(r"[^a-z0-9]+", " ", plain.replace("%", " percent ")).split()
    while words and words[0] in _ARTICLES:
        words = words[1:]
    return " ".join(_token(w) for w in words if w not in _FILLER)


def _word_key(normalised: str) -> str:
    return " ".join(sorted(set(normalised.split())))


class Coding(DomainModel):
    text: str
    normalised: str
    status: Literal["exact", "candidates", "unmatched"]
    ids: tuple[str, ...]  # exact: one id; candidates: ranked best first; unmatched: none


class MissingRequest(DomainModel):
    """A request no catalogue item matched, in the Case Vault's `missing_request` shape."""

    created_at: datetime
    source: Literal["sambhasha"] = "sambhasha"
    bundle_id: str | None
    kind: str
    query: str


class MissingRequestLog:
    """Missing requests collected during runs, exported as CSV for the Case Library."""

    def __init__(self) -> None:
        self._requests: tuple[MissingRequest, ...] = ()

    @property
    def requests(self) -> tuple[MissingRequest, ...]:
        return self._requests

    def add(self, request: MissingRequest) -> None:
        self._requests = (*self._requests, request)

    def write_csv(self, path: Path) -> Path:
        fields = ("created_at", "source", "bundle_id", "kind", "query")
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for request in self._requests:
                row = request.model_dump(mode="json")
                writer.writerow({f: row[f] if row[f] is not None else "" for f in fields})
        return path


@dataclass(frozen=True)
class _Index:
    by_phrase: Mapping[str, frozenset[str]]
    by_words: Mapping[str, frozenset[str]]
    phrases: Mapping[str, tuple[frozenset[str], ...]]  # id -> the word sets of its phrases


def _build_index(items: Iterable[CatalogueItem]) -> _Index:
    by_phrase: defaultdict[str, set[str]] = defaultdict(set)
    by_words: defaultdict[str, set[str]] = defaultdict(set)
    phrases: defaultdict[str, list[frozenset[str]]] = defaultdict(list)
    for item in items:
        for phrase in (item.name, *item.synonyms):
            normalised = normalise(phrase)
            if not normalised:
                continue
            by_phrase[normalised].add(item.id)
            by_words[_word_key(normalised)].add(item.id)
            phrases[item.id].append(frozenset(normalised.split()))
    return _Index(
        by_phrase=MappingProxyType({k: frozenset(v) for k, v in by_phrase.items()}),
        by_words=MappingProxyType({k: frozenset(v) for k, v in by_words.items()}),
        phrases=MappingProxyType({k: tuple(v) for k, v in phrases.items()}),
    )


class Coder:
    """Codes request text against the catalogue, one index per set of kinds."""

    def __init__(self, catalogue: Catalogue, *, missing: MissingRequestLog) -> None:
        self._catalogue = catalogue
        self._missing = missing
        self._indexes: dict[tuple[Kind, ...], _Index] = {}

    def code(self, text: str, *, kinds: tuple[Kind, ...], bundle_id: str | None = None) -> Coding:
        normalised = normalise(text)
        stripped = text.strip()
        if _ITEM_ID.fullmatch(stripped) and self._is_item(stripped, kinds):
            return Coding(text=text, normalised=normalised, status="exact", ids=(stripped,))
        if not normalised:
            return Coding(text=text, normalised=normalised, status="unmatched", ids=())
        index = self._index(kinds)
        for found in (index.by_phrase.get(normalised), index.by_words.get(_word_key(normalised))):
            if found and len(found) == 1:
                return Coding(text=text, normalised=normalised, status="exact", ids=tuple(found))
        ranked = _rank(frozenset(normalised.split()), index)
        if ranked:
            return Coding(text=text, normalised=normalised, status="candidates", ids=ranked)
        self._missing.add(
            MissingRequest(
                created_at=datetime.now(UTC),
                bundle_id=bundle_id,
                kind="|".join(kinds),
                query=text.strip(),
            )
        )
        return Coding(text=text, normalised=normalised, status="unmatched", ids=())

    def _is_item(self, item_id: str, kinds: tuple[Kind, ...]) -> bool:
        try:
            self._catalogue.get(item_id)
        except KeyError:
            return False
        return kind_of(item_id) in kinds

    def _index(self, kinds: tuple[Kind, ...]) -> _Index:
        key = tuple(sorted(set(kinds)))
        if key not in self._indexes:
            self._indexes[key] = _build_index(i for i in self._catalogue.items if i.kind in key)
        return self._indexes[key]


def _rank(words: frozenset[str], index: _Index) -> tuple[str, ...]:
    """Items sharing words with the request, best first (ties by id, for repeatable runs)."""
    scores = {
        item_id: best
        for item_id, phrase_sets in index.phrases.items()
        if (best := max(len(words & p) / len(words | p) for p in phrase_sets)) >= MIN_OVERLAP
    }
    ranked = sorted(scores, key=lambda item_id: (-scores[item_id], item_id))
    return tuple(ranked[:MAX_CANDIDATES])
