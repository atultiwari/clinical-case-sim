"""Checks the Case Vault MCP set-up (PLAN L0.2, SPEC §4.1 and §4.2)."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

CASE_LIBRARY = Path(__file__).resolve().parents[1]
UMBRELLA = CASE_LIBRARY.parent
CASE_VAULT_REF = "vxiymbaxsiavxuyxzhnt"
MCP_FEATURES = {"database", "debugging", "development", "docs"}
# The account-level Supabase connector, as the Claude Code CLI and the desktop app name it.
ACCOUNT_CONNECTORS = {"mcp__claude_ai_Supabase", "mcp__bbfedc9b-cd23-4ebf-9705-6fa0acc5a3fc"}
WRITE_TOOLS = {"mcp__supabase__execute_sql", "mcp__supabase__apply_migration"}


def _read_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _supabase_query() -> dict[str, list[str]]:
    server = _read_json(CASE_LIBRARY / ".mcp.json")["mcpServers"]["supabase"]
    url = urlsplit(server["url"])
    assert server["type"] == "http"
    assert (url.scheme, url.netloc, url.path) == ("https", "mcp.supabase.com", "/mcp")
    return parse_qs(url.query)


def test_mcp_is_scoped_to_the_case_vault_project() -> None:
    assert _supabase_query()["project_ref"] == [CASE_VAULT_REF]


def test_mcp_enables_only_the_agreed_features() -> None:
    assert set(_supabase_query()["features"][0].split(",")) == MCP_FEATURES


def test_mcp_json_declares_only_the_supabase_server() -> None:
    assert list(_read_json(CASE_LIBRARY / ".mcp.json")["mcpServers"]) == ["supabase"]


def test_case_library_keeps_manual_approval_for_writes() -> None:
    permissions = _read_json(CASE_LIBRARY / ".claude" / "settings.json")["permissions"]

    allow = set(permissions.get("allow", []))

    assert set(permissions["ask"]) >= WRITE_TOOLS
    assert not allow & (WRITE_TOOLS | {"mcp__supabase", "mcp__supabase__*"})


@pytest.mark.parametrize("part", ["case-library", "nidana", "sambhasha"])
def test_account_level_connector_is_denied(part: str) -> None:
    deny = set(_read_json(UMBRELLA / part / ".claude" / "settings.json")["permissions"]["deny"])

    assert deny >= ACCOUNT_CONNECTORS


@pytest.mark.parametrize("part", ["nidana", "sambhasha"])
def test_other_parts_have_no_supabase_tools(part: str) -> None:
    deny = set(_read_json(UMBRELLA / part / ".claude" / "settings.json")["permissions"]["deny"])

    assert "mcp__supabase" in deny
    assert not (UMBRELLA / part / ".mcp.json").exists()
