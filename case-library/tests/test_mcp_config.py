"""Checks the Case Vault connector set-up (PLAN L0.2, SPEC §4.1 and §4.2)."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

CASE_LIBRARY = Path(__file__).resolve().parents[1]
UMBRELLA = CASE_LIBRARY.parent
CASE_VAULT_REF = "vxiymbaxsiavxuyxzhnt"
GUARD_HOOK = CASE_LIBRARY / ".claude" / "hooks" / "case-vault-only.sh"
# The account-level Supabase connector, as the Claude Code CLI and the desktop app name it.
ACCOUNT_CONNECTORS = {"mcp__claude_ai_Supabase", "mcp__bbfedc9b-cd23-4ebf-9705-6fa0acc5a3fc"}
WRITE_TOOLS = {"execute_sql", "apply_migration"}
ACCOUNT_TOOLS = {
    "create_project",
    "pause_project",
    "restore_project",
    "confirm_cost",
    "create_branch",
    "delete_branch",
    "merge_branch",
    "reset_branch",
    "rebase_branch",
    "deploy_edge_function",
}


def _read_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _case_library_settings() -> dict[str, Any]:
    return _read_json(CASE_LIBRARY / ".claude" / "settings.json")


def _run_guard(tool_input: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    payload = json.dumps(
        {"tool_name": "mcp__claude_ai_Supabase__execute_sql", "tool_input": tool_input}
    )
    return subprocess.run(
        [str(GUARD_HOOK)], input=payload, capture_output=True, text=True, check=False
    )


def test_case_library_has_no_project_scoped_server() -> None:
    assert not (CASE_LIBRARY / ".mcp.json").exists()


@pytest.mark.parametrize("connector", sorted(ACCOUNT_CONNECTORS))
def test_case_library_keeps_manual_approval_for_writes(connector: str) -> None:
    permissions = _case_library_settings()["permissions"]
    writes = {f"{connector}__{tool}" for tool in WRITE_TOOLS}

    assert set(permissions["ask"]) >= writes
    assert not set(permissions.get("allow", [])) & (writes | {connector, f"{connector}__*"})


@pytest.mark.parametrize("connector", sorted(ACCOUNT_CONNECTORS))
def test_case_library_denies_account_tools(connector: str) -> None:
    deny = set(_case_library_settings()["permissions"]["deny"])

    assert deny >= {f"{connector}__{tool}" for tool in ACCOUNT_TOOLS}
    assert connector not in deny


@pytest.mark.parametrize("connector", sorted(ACCOUNT_CONNECTORS))
def test_guard_hook_covers_the_connector(connector: str) -> None:
    [entry] = _case_library_settings()["hooks"]["PreToolUse"]

    assert f"{connector}__.*" in entry["matcher"].split("|")
    assert entry["hooks"][0]["command"].endswith("/.claude/hooks/case-vault-only.sh")


def test_guard_allows_the_case_vault() -> None:
    assert _run_guard({"project_id": CASE_VAULT_REF}).returncode == 0


def test_guard_allows_calls_without_a_project() -> None:
    assert _run_guard({}).returncode == 0


def test_guard_blocks_another_project() -> None:
    result = _run_guard({"project_id": "someotherproject"})

    assert result.returncode == 2
    assert "someotherproject" in result.stderr


@pytest.mark.parametrize("part", ["nidana", "sambhasha"])
def test_account_level_connector_is_denied(part: str) -> None:
    deny = set(_read_json(UMBRELLA / part / ".claude" / "settings.json")["permissions"]["deny"])

    assert deny >= ACCOUNT_CONNECTORS


@pytest.mark.parametrize("part", ["nidana", "sambhasha"])
def test_claude_ai_connectors_are_not_fetched(part: str) -> None:
    # Hides them in terminal and IDE sessions; the desktop app delivers connectors itself,
    # so there only the deny rules above apply.
    assert _read_json(UMBRELLA / part / ".claude" / "settings.json")["disableClaudeAiConnectors"]


@pytest.mark.parametrize("part", ["nidana", "sambhasha"])
def test_other_parts_have_no_supabase_tools(part: str) -> None:
    deny = set(_read_json(UMBRELLA / part / ".claude" / "settings.json")["permissions"]["deny"])

    assert "mcp__supabase" in deny
    assert not (UMBRELLA / part / ".mcp.json").exists()
