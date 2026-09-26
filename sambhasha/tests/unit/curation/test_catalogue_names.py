"""P0.5: reading test and diagnosis names from the shared catalogue."""

from pathlib import Path

import pytest

from sambhasha.curation.catalogue_names import CatalogueError, CatalogueNames


def _write(directory: Path, tests: str, diagnoses: str) -> Path:
    (directory / "tests.csv").write_text(tests, encoding="utf-8")
    (directory / "diagnoses.csv").write_text(diagnoses, encoding="utf-8")
    return directory


def test_names_and_synonyms_are_read(tmp_path: Path) -> None:
    names = CatalogueNames.load(
        _write(
            tmp_path,
            "id,name,synonyms\nLAB.A,Blood lead,BLL|lead level\n",
            "id,name,synonyms\nDX.A,Lead poisoning,plumbism\nDX.B,Other,\n",
        )
    )

    assert names.test_names == ("Blood lead", "BLL", "lead level")
    assert names.diagnosis("DX.A", "DX.MISSING") == ("Lead poisoning", "plumbism")
    assert names.diagnosis("DX.B") == ("Other",)


def test_a_missing_file_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(CatalogueError, match="not found"):
        CatalogueNames.load(tmp_path)


def test_a_missing_column_is_a_clear_error(tmp_path: Path) -> None:
    _write(tmp_path, "id,name\nLAB.A,Blood lead\n", "id,name,synonyms\n")

    with pytest.raises(CatalogueError, match="synonyms"):
        CatalogueNames.load(tmp_path)


def test_the_shared_catalogue_loads() -> None:
    names = CatalogueNames.load()

    assert "Full blood count" in names.test_names
    assert names.diagnosis("DX.LEAD_POISONING")
