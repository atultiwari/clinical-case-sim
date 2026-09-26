"""P0.6: the bundle importer (SPEC §9). Milestone M0: the pilot imports cleanly."""

import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.importer import (
    DEVELOPMENT_ONLY,
    ImportRefusedError,
    import_bundle,
    primary_bundles,
)
from sambhasha.storage.memory import InMemoryRepository

EXPORTS = Path(__file__).resolve().parents[4] / "case-library" / "exports"
PILOT_R1 = EXPORTS / "PMC12949993@v1.r1.json"
CATALOGUE = CatalogueNames.load()


def _newest(paths: list[Path]) -> list[Path]:
    newest: dict[str, tuple[tuple[int, int], Path]] = {}
    for path in paths:
        match = re.fullmatch(r"(.+)@v(\d+)\.r(\d+)\.json", path.name)
        assert match
        rank = (int(match[2]), int(match[3]))
        if match[1] not in newest or rank > newest[match[1]][0]:
            newest[match[1]] = (rank, path)
    return sorted(path for _, path in newest.values())


def _copy(path: Path, directory: Path) -> Path:
    copy = directory / path.name
    shutil.copyfile(path, copy)
    shutil.copyfile(path.with_name(f"{path.name}.sha256"), copy.with_name(f"{copy.name}.sha256"))
    return copy


def _write(directory: Path, name: str, data: bytes, digest: str | None = None) -> Path:
    path = directory / name
    path.write_bytes(data)
    digest = digest or hashlib.sha256(data).hexdigest()
    path.with_name(f"{name}.sha256").write_text(f"{digest}  {name}\n")
    return path


# --- the pilot (M0) ---


def test_the_pilot_imports_with_every_row() -> None:
    repo = InMemoryRepository()

    report = import_bundle(PILOT_R1, repo, CATALOGUE)

    bundle = repo.get_bundle("PMC12949993@v1.r1")
    kinds = {
        kind: sum(f.id.startswith(prefix) for f in bundle.facts)
        for kind, prefix in (("history", "H"), ("series", "S"), ("single", "L"), ("derived", "D"))
    }
    assert kinds == {"history": 10, "series": 125, "single": 35, "derived": 21}
    assert report.counts == {
        "facts": 191,
        "ledger": 1109,
        "reports": 16,
        "consult_notes": 22,
        "raw_material": 3,
        "media": 4,
        "gaps": 20,
    }
    assert report.leaks == ()


def test_the_import_records_the_bundle_revision_and_hash() -> None:
    repo = InMemoryRepository()

    report = import_bundle(PILOT_R1, repo, CATALOGUE)

    (record,) = repo.list_bundles()
    expected = PILOT_R1.with_name(f"{PILOT_R1.name}.sha256").read_text().split()[0]
    assert (record.bundle_id, record.revision, record.sha256) == ("PMC12949993@v1.r1", 1, expected)
    assert report.sha256 == expected


def test_an_imported_bundle_is_not_eligible_for_primary_results() -> None:
    repo = InMemoryRepository()

    report = import_bundle(PILOT_R1, repo, CATALOGUE)

    (record,) = repo.list_bundles()
    assert record.primary_eligible is False
    assert record.eligibility_reason == DEVELOPMENT_ONLY
    assert report.primary_eligible is False


def test_every_published_bundle_imports_and_none_is_primary() -> None:
    repo = InMemoryRepository()
    newest = _newest(sorted(EXPORTS.glob("*.json")))

    for path in newest:
        import_bundle(path, repo, CATALOGUE)

    assert len(repo.list_bundles()) == len(newest) >= 10
    assert primary_bundles(repo) == ()


def test_primary_bundles_are_those_marked_eligible() -> None:
    repo = InMemoryRepository()
    import_bundle(PILOT_R1, repo, CATALOGUE)
    repo.set_eligibility("PMC12949993@v1.r1", eligible=True, reason="a future study case")

    assert [r.bundle_id for r in primary_bundles(repo)] == ["PMC12949993@v1.r1"]


# --- refusals ---


def _refusal(path: Path, repo: InMemoryRepository | None = None) -> str:
    repo = repo or InMemoryRepository()
    with pytest.raises(ImportRefusedError) as caught:
        import_bundle(path, repo, CATALOGUE)
    return str(caught.value)


def test_a_wrong_hash_is_refused(tmp_path: Path) -> None:
    path = _write(tmp_path, PILOT_R1.name, PILOT_R1.read_bytes(), digest="0" * 64)

    assert "SHA-256" in _refusal(path)


def test_a_changed_byte_is_refused(tmp_path: Path) -> None:
    path = _copy(PILOT_R1, tmp_path)
    path.write_bytes(path.read_bytes().replace(b"Admission", b"admission", 1))

    assert "SHA-256" in _refusal(path)


def test_a_missing_hash_file_is_refused(tmp_path: Path) -> None:
    path = tmp_path / PILOT_R1.name
    shutil.copyfile(PILOT_R1, path)

    assert ".sha256" in _refusal(path)


def test_a_hash_file_for_another_bundle_is_refused(tmp_path: Path) -> None:
    path = _copy(PILOT_R1, tmp_path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_name(f"{path.name}.sha256").write_text(f"{digest}  PMC1@v1.r1.json\n")

    assert "names" in _refusal(path)


def test_a_malformed_hash_file_is_refused(tmp_path: Path) -> None:
    path = _copy(PILOT_R1, tmp_path)
    path.with_name(f"{path.name}.sha256").write_text("not a hash\n")

    assert ".sha256" in _refusal(path)


def test_an_unsupported_schema_version_is_refused(tmp_path: Path) -> None:
    data = json.loads(PILOT_R1.read_bytes())
    data["schema_version"] = "0.2"
    path = _write(tmp_path, PILOT_R1.name, json.dumps(data).encode())

    message = _refusal(path)

    assert "schema_version" in message
    assert "0.3" in message


def test_a_file_named_for_another_bundle_is_refused(tmp_path: Path) -> None:
    path = _write(tmp_path, "PMC12949993@v1.r9.json", PILOT_R1.read_bytes())

    assert "PMC12949993@v1.r1" in _refusal(path)


def test_a_leaking_bundle_is_refused_with_its_findings(tmp_path: Path) -> None:
    data = json.loads(PILOT_R1.read_bytes())
    data["vignette"] += " Suspected plumbism."
    path = _write(tmp_path, PILOT_R1.name, json.dumps(data).encode())
    repo = InMemoryRepository()

    message = _refusal(path, repo)

    assert "leak" in message
    assert "vignette" in message
    assert "plumbism" in message
    assert repo.list_bundles() == ()


def test_a_bundle_is_imported_once() -> None:
    repo = InMemoryRepository()
    import_bundle(PILOT_R1, repo, CATALOGUE)

    assert "already imported" in _refusal(PILOT_R1, repo)


def test_a_missing_file_is_refused(tmp_path: Path) -> None:
    assert "not found" in _refusal(tmp_path / "PMC1@v1.r1.json")
