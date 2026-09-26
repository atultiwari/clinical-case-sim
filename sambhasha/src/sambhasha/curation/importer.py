"""The bundle importer: `sambhasha case import <bundle.json>` (SPEC §9; PLAN P0.6).

It checks the file's SHA-256 against the `.sha256` file beside it (hashing the bytes as
written, never re-serialising), validates the bundle (schema 0.3), refuses one whose file
name is not its bundle id, runs the leak scanner on every seat-facing text, and stores it
sealed. Every bundle it imports is marked not eligible for a study's primary results: the
cases in this public repository are development-only (S-010). It never writes to the Case
Vault.
"""

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from sambhasha.curation.catalogue_names import CatalogueNames
from sambhasha.curation.leakscan import LeakFinding, Lexicon, scan_bundle
from sambhasha.domain.case_file import BundleError, CaseBundle, parse_bundle
from sambhasha.storage.repo import BundleRecord, CaseRepository, DuplicateError

DEVELOPMENT_ONLY: Final = "S-010: cases committed to the public repository are development-only"
_HASH_LINE = re.compile(r"(?P<digest>[0-9a-f]{64}) [ *](?P<name>\S.*)")
_COUNTED: Final = ("facts", "ledger", "reports", "consult_notes", "raw_material", "media", "gaps")


class ImportRefusedError(Exception):
    """The bundle was not imported. The message says why."""


@dataclass(frozen=True)
class ImportReport:
    bundle_id: str
    sha256: str
    counts: Mapping[str, int]
    leaks: tuple[LeakFinding, ...]
    primary_eligible: bool
    eligibility_reason: str


def read_verified(path: Path) -> tuple[CaseBundle, str]:
    """The bundle in a file, after checking its hash and its name; or ImportRefusedError."""
    try:
        data = path.read_bytes()
    except FileNotFoundError as error:
        raise ImportRefusedError(f"bundle file not found: {path}") from error
    digest = _expected_digest(path)
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest:
        raise ImportRefusedError(
            f"{path.name}: SHA-256 {actual} does not match {digest} in its .sha256 file"
        )
    try:
        bundle = parse_bundle(data)
    except BundleError as error:
        raise ImportRefusedError(f"{path.name}: {error}") from error
    if path.name != f"{bundle.bundle_id}.json":
        raise ImportRefusedError(
            f"{path.name} holds bundle {bundle.bundle_id}; rename it or re-export"
        )
    return bundle, digest


def _expected_digest(path: Path) -> str:
    hash_file = path.with_name(f"{path.name}.sha256")
    try:
        line = hash_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise ImportRefusedError(
            f"{hash_file.name} is missing; bundles come with their hash"
        ) from error
    match = _HASH_LINE.fullmatch(line)
    if match is None:
        raise ImportRefusedError(f"{hash_file.name} is not '<sha256>  <file name>'")
    if match["name"] != path.name:
        raise ImportRefusedError(f"{hash_file.name} names {match['name']}, not {path.name}")
    return match["digest"]


def import_bundle(path: Path, repo: CaseRepository, catalogue: CatalogueNames) -> ImportReport:
    """Verify, scan and store one bundle file; refuse it with a reason if anything fails."""
    bundle, digest = read_verified(path)
    leaks = scan_bundle(bundle, Lexicon.from_bundle(bundle, catalogue))
    if leaks:
        listed = "\n".join(f"  {f.location} {f.row_id}: {f.term!r}" for f in leaks)
        raise ImportRefusedError(
            f"{bundle.bundle_id}: {len(leaks)} leak(s) in seat-facing text:\n{listed}"
        )
    try:
        repo.add_bundle(bundle, digest)
    except DuplicateError as error:
        raise ImportRefusedError(f"{bundle.bundle_id} is already imported") from error
    repo.set_eligibility(bundle.bundle_id, eligible=False, reason=DEVELOPMENT_ONLY)
    return ImportReport(
        bundle_id=bundle.bundle_id,
        sha256=digest,
        counts=MappingProxyType({name: len(getattr(bundle, name)) for name in _COUNTED}),
        leaks=leaks,
        primary_eligible=False,
        eligibility_reason=DEVELOPMENT_ONLY,
    )


def primary_bundles(repo: CaseRepository) -> tuple[BundleRecord, ...]:
    """The bundles a study's primary analysis may use: only those marked eligible."""
    return tuple(record for record in repo.list_bundles() if record.primary_eligible)
