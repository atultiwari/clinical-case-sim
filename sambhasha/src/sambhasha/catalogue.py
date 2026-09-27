"""The shared catalogue, read from `case-library/catalogue/` (Case Library SPEC §5; D-022).

One global list of history questions, examinations, tests, components, actions, referrals,
diagnoses and findings, the same for every case. Sambhasha reads the CSV files as committed;
the catalogue changes only through the Case Library.
"""

import csv
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal

PINNED_CATALOGUE_VERSION: Final = 2  # CLAUDE.md, "Pinned shared-contract versions"
DEFAULT_CATALOGUE_DIR: Final = Path(__file__).resolve().parents[3] / "case-library" / "catalogue"

Kind = Literal["history", "exam", "test", "component", "action", "referral", "diagnosis", "finding"]
_FILES: Final[dict[str, Kind]] = {
    "history.csv": "history",
    "exam.csv": "exam",
    "tests.csv": "test",
    "components.csv": "component",
    "actions.csv": "action",
    "referrals.csv": "referral",
    "diagnoses.csv": "diagnosis",
    "findings.csv": "finding",
}
_PREFIXES: Final[dict[str, Kind]] = {
    "HX": "history",
    "EX": "exam",
    "LAB": "test",
    "IMG": "test",
    "PROC": "test",
    "CMP": "component",
    "RX": "action",
    "ACT": "action",
    "REF": "referral",
    "DX": "diagnosis",
    "FND": "finding",
}
_ID = re.compile(r"(?P<prefix>[A-Z]+)\.[A-Z0-9_.]+")


class CatalogueError(ValueError):
    """The catalogue files are missing or malformed, or an id breaks the patterns."""


def kind_of(item_id: str) -> Kind:
    """The kind an id belongs to, from its prefix (`LAB.HAEM.CBC` is a test)."""
    match = _ID.fullmatch(item_id)
    kind = _PREFIXES.get(match["prefix"]) if match else None
    if kind is None:
        raise CatalogueError(f"not a catalogue id: {item_id!r}")
    return kind


@dataclass(frozen=True)
class CatalogueItem:
    id: str
    kind: Kind
    name: str
    synonyms: tuple[str, ...]
    loinc: str | None = None
    scope: tuple[str, ...] = ()  # who may use it: "attending", "consultant.*", ...
    route: str | None = None  # tests: "direct" or the service that performs it
    components: tuple[str, ...] = ()  # tests: their component ids, in order
    price_inr: int | None = None  # tests: CGHS rate or estimate
    price_source: str | None = None
    tat_minutes: int | None = None  # tests: turnaround time


def read_rows(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    """The rows of one catalogue CSV, checking that the needed columns are there."""
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = set(required) - set(reader.fieldnames or ())
            if missing:
                raise CatalogueError(f"{path.name} lacks the columns {sorted(missing)}")
            return list(reader)
    except FileNotFoundError as error:
        raise CatalogueError(f"catalogue file not found: {path}") from error


def split_synonyms(field: str | None) -> tuple[str, ...]:
    return tuple(s.strip() for s in (field or "").split("|") if s.strip())


class Catalogue:
    def __init__(self, items: tuple[CatalogueItem, ...]) -> None:
        self._items = items
        self._by_id = MappingProxyType({item.id: item for item in items})

    @classmethod
    def load(cls, directory: Path = DEFAULT_CATALOGUE_DIR) -> "Catalogue":
        return cls(tuple(_read_items(directory)))

    @property
    def items(self) -> tuple[CatalogueItem, ...]:
        return self._items

    def get(self, item_id: str) -> CatalogueItem:
        try:
            return self._by_id[item_id]
        except KeyError:
            raise KeyError(f"no catalogue item {item_id}") from None


def _read_items(directory: Path) -> Iterator[CatalogueItem]:
    for filename, kind in _FILES.items():
        for row in read_rows(directory / filename, ("id", "name")):
            yield CatalogueItem(
                id=row["id"],
                kind=kind,
                name=row["name"],
                synonyms=split_synonyms(row.get("synonyms")),
                loinc=row.get("loinc") or None,
                scope=split_synonyms(row.get("specialty_scope")),
                route=row.get("route") or None,
                components=split_synonyms(row.get("components")),
                price_inr=_integer(row.get("price_inr")),
                price_source=row.get("price_source") or None,
                tat_minutes=_integer(row.get("tat_minutes")),
            )


def _integer(field: str | None) -> int | None:
    if not field:
        return None
    try:
        return int(float(field))
    except ValueError as error:
        raise CatalogueError(f"not a number in the catalogue: {field!r}") from error
