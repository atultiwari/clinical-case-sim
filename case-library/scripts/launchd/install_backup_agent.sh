#!/usr/bin/env bash
# Install (or reinstall) the nightly Case Vault backup LaunchAgent for this user.
# Uninstall: launchctl bootout gui/$(id -u)/local.clinical-case-sim.casevault-backup
#            && rm ~/Library/LaunchAgents/local.clinical-case-sim.casevault-backup.plist
set -euo pipefail

readonly LABEL="local.clinical-case-sim.casevault-backup"
readonly HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CASE_LIBRARY="$(cd "$HERE/../.." && pwd)"
readonly TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$HOME/CaseVaultBackups" "$HOME/Library/LaunchAgents"
sed -e "s|CASE_LIBRARY_PATH|$CASE_LIBRARY|" -e "s|HOME_PATH|$HOME|" "$HERE/$LABEL.plist" >"$TARGET"
plutil -lint "$TARGET"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$TARGET"
echo "Installed $TARGET; next run at 02:30."
