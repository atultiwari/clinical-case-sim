"""Only `sambhasha.llm` imports the openai SDK (CLAUDE.md conventions; SPEC §11)."""

import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "src" / "sambhasha"
IMPORT = re.compile(r"^\s*(import openai|from openai\b)", re.MULTILINE)


def test_no_module_outside_llm_imports_openai() -> None:
    offenders = [
        str(path.relative_to(SOURCE))
        for path in SOURCE.rglob("*.py")
        if "llm" not in path.relative_to(SOURCE).parts and IMPORT.search(path.read_text())
    ]

    assert offenders == []


def test_the_llm_package_does_use_it() -> None:
    assert any(IMPORT.search(p.read_text()) for p in (SOURCE / "llm").rglob("*.py"))
