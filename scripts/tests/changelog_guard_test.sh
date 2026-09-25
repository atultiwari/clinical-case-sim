#!/usr/bin/env bash
# Tests for scripts/changelog_guard.sh (umbrella task U0.1).
# Each case builds a throwaway Git repository, stages or commits some paths,
# and checks the guard's exit status. Run: bash scripts/tests/changelog_guard_test.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GUARD="$ROOT/scripts/changelog_guard.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0

new_repo() {
  local dir="$WORK/$1"
  mkdir -p "$dir"
  git -C "$dir" init -q -b main
  git -C "$dir" config user.name "Guard Test"
  git -C "$dir" config user.email "guard-test@example.invalid"
  git -C "$dir" config commit.gpgsign false
  mkdir -p "$dir/docs" "$dir/case-library/schemas" "$dir/case-library/catalogue"
  echo "# Changelog" > "$dir/docs/CHANGELOG.md"
  echo '{"version": "0.3"}' > "$dir/case-library/schemas/bundle.schema.json"
  echo "id,label" > "$dir/case-library/catalogue/lab.csv"
  echo "readme" > "$dir/README.md"
  git -C "$dir" add -A
  git -C "$dir" commit -q -m "base"
  echo "$dir"
}

touch_file() {
  mkdir -p "$(dirname "$1")"
  echo "change $RANDOM" >> "$1"
}

expect() {
  local want="$1" name="$2"
  shift 2
  local got=0
  "$@" > /dev/null 2>&1 || got=$?
  if { [ "$want" = pass ] && [ "$got" -eq 0 ]; } || { [ "$want" = fail ] && [ "$got" -eq 1 ]; }; then
    passed=$((passed + 1))
    echo "ok    $name"
  else
    failed=$((failed + 1))
    echo "FAIL  $name (expected $want, exit status $got)"
  fi
}

staged_guard() { (cd "$1" && bash "$GUARD" --staged); }
range_guard() { (cd "$1" && bash "$GUARD" --range main HEAD); }

# --- staged mode (the pre-commit hook) ---

r=$(new_repo schema-alone); touch_file "$r/case-library/schemas/bundle.schema.json"; git -C "$r" add -A
expect fail "staged: schema change without changelog is blocked" staged_guard "$r"

r=$(new_repo catalogue-alone); touch_file "$r/case-library/catalogue/lab.csv"; git -C "$r" add -A
expect fail "staged: catalogue change without changelog is blocked" staged_guard "$r"

r=$(new_repo new-schema-file); touch_file "$r/case-library/schemas/nested/new.json"; git -C "$r" add -A
expect fail "staged: new file in a schemas subfolder is blocked" staged_guard "$r"

r=$(new_repo schema-deleted); git -C "$r" rm -q case-library/schemas/bundle.schema.json
expect fail "staged: deleting a schema file without changelog is blocked" staged_guard "$r"

r=$(new_repo schema-renamed-out); git -C "$r" mv case-library/schemas/bundle.schema.json README-schema.json
expect fail "staged: moving a file out of schemas without changelog is blocked" staged_guard "$r"

r=$(new_repo schema-with-changelog)
touch_file "$r/case-library/schemas/bundle.schema.json"; touch_file "$r/docs/CHANGELOG.md"; git -C "$r" add -A
expect pass "staged: schema change with changelog is allowed" staged_guard "$r"

r=$(new_repo unrelated); touch_file "$r/README.md"; touch_file "$r/nidana/app.ts"; git -C "$r" add -A
expect pass "staged: unrelated change is allowed" staged_guard "$r"

r=$(new_repo lookalikes)
touch_file "$r/case-library/schemas-old/x.json"; touch_file "$r/nidana/case-library/schemas/x.json"
touch_file "$r/case-library/docs/schemas.md"; git -C "$r" add -A
expect pass "staged: look-alike paths are not guarded" staged_guard "$r"

r=$(new_repo unstaged-only); touch_file "$r/case-library/schemas/bundle.schema.json"
expect pass "staged: an unstaged schema edit is not part of the commit" staged_guard "$r"

r=$(new_repo nothing-staged)
expect pass "staged: an empty index passes" staged_guard "$r"

# --- range mode (the contract workflow on a pull request) ---

r=$(new_repo pr-schema-alone); git -C "$r" checkout -q -b feature
touch_file "$r/case-library/schemas/bundle.schema.json"; git -C "$r" commit -qam "schema"
expect fail "range: pull request with a schema change and no changelog fails" range_guard "$r"

r=$(new_repo pr-split); git -C "$r" checkout -q -b feature
touch_file "$r/case-library/catalogue/lab.csv"; git -C "$r" commit -qam "catalogue"
touch_file "$r/docs/CHANGELOG.md"; git -C "$r" commit -qam "changelog"
expect pass "range: changelog in a later commit of the same pull request passes" range_guard "$r"

r=$(new_repo pr-main-moved); git -C "$r" checkout -q -b feature
touch_file "$r/README.md"; git -C "$r" commit -qam "docs"
git -C "$r" checkout -q main; touch_file "$r/case-library/schemas/bundle.schema.json"; touch_file "$r/docs/CHANGELOG.md"
git -C "$r" commit -qam "main moved"; git -C "$r" checkout -q feature
expect pass "range: changes on main since the branch point are ignored" range_guard "$r"

r=$(new_repo pr-unrelated); git -C "$r" checkout -q -b feature
touch_file "$r/README.md"; git -C "$r" commit -qam "docs"
expect pass "range: pull request without guarded paths passes" range_guard "$r"

# --- usage errors ---

r=$(new_repo usage)
expect_usage() { local got=0; (cd "$r" && bash "$GUARD" "$@") > /dev/null 2>&1 || got=$?; [ "$got" -eq 2 ]; }
expect pass "usage: no arguments exits 2" expect_usage
expect pass "usage: unknown mode exits 2" expect_usage --bogus
expect pass "usage: bad revision exits 2" expect_usage --range no-such-ref HEAD

echo
echo "$passed passed, $failed failed"
[ "$failed" -eq 0 ]
