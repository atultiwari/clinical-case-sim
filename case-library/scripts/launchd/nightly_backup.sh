#!/usr/bin/env bash
# Nightly Case Vault backup, run by the LaunchAgent in this folder (PLAN L0.3).
# Appends one line per run to $CASE_VAULT_BACKUP_DIR/backup.log (default ~/CaseVaultBackups).
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
readonly CASE_LIBRARY="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly LOG_DIR="${CASE_VAULT_BACKUP_DIR:-$HOME/CaseVaultBackups}"
mkdir -p "$LOG_DIR"

cd "$CASE_LIBRARY"
if ! docker info >/dev/null 2>&1; then
  echo "$(date -u +'%Y-%m-%d %H:%M')Z backup FAILED: Docker is not running" >>"$LOG_DIR/backup.log"
  exit 1
fi
uv run --env-file .env python -m scripts.backup_case_vault >>"$LOG_DIR/backup.log" 2>&1
