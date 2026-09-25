"""Checks that the Case Library scaffold (PLAN L0.1) is in place."""

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from tests.conftest import LOCAL_DB_URL

CASE_LIBRARY = Path(__file__).resolve().parents[1]
ENV_KEYS = [
    "CASE_VAULT_DB_URL_READONLY",
    "CASE_VAULT_DB_URL_BACKUP",
    "CASE_VAULT_BACKUP_DIR",
    "NCBI_API_KEY",
    "NCBI_EMAIL",
]


def _env_example_entries() -> dict[str, str]:
    lines = (CASE_LIBRARY / ".env.example").read_text(encoding="utf-8").splitlines()
    pairs = (line.split("=", 1) for line in lines if line and not line.startswith("#"))
    return {key.strip(): value.strip() for key, value in pairs}


def test_env_example_lists_exactly_the_expected_keys() -> None:
    assert sorted(_env_example_entries()) == sorted(ENV_KEYS)


def test_env_example_holds_no_values() -> None:
    assert all(value == "" for value in _env_example_entries().values())


@pytest.mark.parametrize(
    ("path", "ignored"),
    [
        ("data/raw.json", True),
        ("review/batch-01.xlsx", True),
        (".env", True),
        (".env.example", False),
        ("supabase/.temp/cli-latest", True),
        ("supabase/config.toml", False),
    ],
)
def test_gitignore(path: str, ignored: bool) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--no-index", path],
        cwd=CASE_LIBRARY,
        check=False,
    )

    assert (result.returncode == 0) is ignored


def test_supabase_config_names_the_case_vault_on_postgres_17() -> None:
    config = tomllib.loads((CASE_LIBRARY / "supabase" / "config.toml").read_text(encoding="utf-8"))

    assert config["project_id"] == "case-vault"
    assert config["db"]["major_version"] == 17


def test_casevault_schema_is_not_exposed_to_the_data_api() -> None:
    config = tomllib.loads((CASE_LIBRARY / "supabase" / "config.toml").read_text(encoding="utf-8"))

    assert "casevault" not in config["api"]["schemas"]


def test_migrations_folder_exists() -> None:
    assert (CASE_LIBRARY / "supabase" / "migrations").is_dir()


def test_local_stack_avoids_the_default_supabase_ports() -> None:
    """Other local Supabase projects use 543xx; `supabase db reset` must never hit them."""
    text = (CASE_LIBRARY / "supabase" / "config.toml").read_text(encoding="utf-8")

    assert re.search(r"\b543\d\d\b", text) is None


def test_integration_fixture_targets_the_configured_port() -> None:
    config = tomllib.loads((CASE_LIBRARY / "supabase" / "config.toml").read_text(encoding="utf-8"))

    assert f":{config['db']['port']}/" in LOCAL_DB_URL
