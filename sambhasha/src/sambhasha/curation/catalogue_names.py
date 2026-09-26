"""Names from the shared catalogue that the leak scanner needs (Case Library SPEC §5).

Read straight from the catalogue CSV files in `case-library/catalogue/`: test names and
synonyms (allowed phrases) and diagnosis names and synonyms (leak terms). The Gatekeeper's
full use of the catalogue, with coding and synonyms for matching, arrives in P1.2.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from sambhasha.catalogue import DEFAULT_CATALOGUE_DIR, CatalogueError, read_rows, split_synonyms

__all__ = ["DEFAULT_CATALOGUE_DIR", "CatalogueError", "CatalogueNames"]


def _names(row: dict[str, str]) -> tuple[str, ...]:
    return (row["name"], *split_synonyms(row.get("synonyms")))


@dataclass(frozen=True)
class CatalogueNames:
    test_names: tuple[str, ...]
    diagnosis_names: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    @classmethod
    def load(cls, directory: Path = DEFAULT_CATALOGUE_DIR) -> "CatalogueNames":
        tests = read_rows(directory / "tests.csv", ("id", "name", "synonyms"))
        diagnoses = read_rows(directory / "diagnoses.csv", ("id", "name", "synonyms"))
        return cls(
            test_names=tuple(name for row in tests for name in _names(row)),
            diagnosis_names=MappingProxyType({row["id"]: _names(row) for row in diagnoses}),
        )

    def diagnosis(self, *ids: str) -> tuple[str, ...]:
        """The names and synonyms of the given diagnosis ids, where the catalogue has them."""
        return tuple(name for i in ids for name in self.diagnosis_names.get(i, ()))
