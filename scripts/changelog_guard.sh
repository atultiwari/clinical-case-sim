#!/usr/bin/env bash
# Changelog guard (S-004, docs/REPOSITORY.md, umbrella task U0.1).
#
# A change to the shared contract under case-library/schemas/ or
# case-library/catalogue/ must come with a change to docs/CHANGELOG.md.
#
#   changelog_guard.sh --staged          the staged commit (pre-commit hook)
#   changelog_guard.sh --range BASE HEAD  a pull request: HEAD against its
#                                         merge base with BASE (CI)
#
# Exit status: 0 allowed, 1 blocked, 2 usage or Git error.
set -euo pipefail

GUARDED_PATTERN='^case-library/(schemas|catalogue)/'
CHANGELOG='docs/CHANGELOG.md'

usage() {
  echo "usage: $0 --staged | --range BASE HEAD" >&2
  exit 2
}

changed_files() {
  case "${1:-}" in
    --staged)
      [ "$#" -eq 1 ] || usage
      git diff --cached --name-only --no-renames
      ;;
    --range)
      [ "$#" -eq 3 ] || usage
      local base
      base="$(git merge-base "$2" "$3" 2> /dev/null)" || {
        echo "changelog guard: cannot find a merge base of '$2' and '$3'" >&2
        exit 2
      }
      git diff --name-only --no-renames "$base" "$3"
      ;;
    *)
      usage
      ;;
  esac
}

main() {
  local files guarded
  files="$(changed_files "$@")" || exit 2
  guarded="$(printf '%s\n' "$files" | grep -E "$GUARDED_PATTERN" || true)"

  if [ -z "$guarded" ]; then
    exit 0
  fi
  if printf '%s\n' "$files" | grep -qxF "$CHANGELOG"; then
    exit 0
  fi

  {
    echo "changelog guard: these shared-contract files changed without $CHANGELOG:"
    printf '%s\n' "$guarded" | sed 's/^/  /'
    echo "Add a versioned entry to $CHANGELOG with an acknowledgement item per part (CLAUDE.md rule 3)."
  } >&2
  exit 1
}

main "$@"
