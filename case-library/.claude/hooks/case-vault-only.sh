#!/usr/bin/env bash
# PreToolUse guard: the Supabase connector may touch only the Case Vault.
set -euo pipefail
readonly CASE_VAULT_REF="vxiymbaxsiavxuyxzhnt"
input="$(cat)"
tool="$(jq -r '.tool_name // ""' <<<"$input")"
project="$(jq -r '.tool_input.project_id // empty' <<<"$input")"
if [[ -n "$project" && "$project" != "$CASE_VAULT_REF" ]]; then
  echo "Blocked: ${tool} targets project '${project}'. Only the Case Vault (${CASE_VAULT_REF}) is allowed here." >&2
  exit 2
fi
exit 0
