"""Names from the shared catalogue that the leak scanner needs (Case Library SPEC §5).

Read straight from the catalogue CSV files in `case-library/catalogue/`: test names and
synonyms (allowed phrases) and diagnosis names and synonyms (leak terms). The Gatekeeper's
full use of the catalogue, with coding and synonyms for matching, arrives in P1.2.
"""

import csv
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

DEFAULT_CATALOGUE_DIR = Path(__file__).resolve().parents[4] / "case-library" / "catalogue"


class CatalogueError(ValueError):
    """The catalogue files are missing or malformed."""


def _names(row: dict[str, str]) -> tuple[str, ...]:
    synonyms = [s for s in (row.get("synonyms") or "").split("|") if s.strip()]
    return (row["name"], *synonyms)


def _rows(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = set(required) - set(reader.fieldnames or ())
            if missing:
                raise CatalogueError(f"{path.name} lacks the columns {sorted(missing)}")
            return list(reader)
    except FileNotFoundError as error:
        raise CatalogueError(f"catalogue file not found: {path}") from error


@dataclass(frozen=True)
class CatalogueNames:
    test_names: tuple[str, ...]
    diagnosis_names: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    @classmethod
    def load(cls, directory: Path = DEFAULT_CATALOGUE_DIR) -> "CatalogueNames":
        tests = _rows(directory / "tests.csv", ("id", "name", "synonyms"))
        diagnoses = _rows(directory / "diagnoses.csv", ("id", "name", "synonyms"))
        return cls(
            test_names=tuple(name for row in tests for name in _names(row)),
            diagnosis_names=MappingProxyType({row["id"]: _names(row) for row in diagnoses}),
        )

    def diagnosis(self, *ids: str) -> tuple[str, ...]:
        """The names and synonyms of the given diagnosis ids, where the catalogue has them."""
        return tuple(name for i in ids for name in self.diagnosis_names.get(i, ()))
