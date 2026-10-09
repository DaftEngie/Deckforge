#!/usr/bin/env bash
# Gate self-test: build known-bad commits in a throwaway clone and confirm the
# tamper check rejects each one. Exits non-zero if any bad change slips through.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

git clone --quiet "$repo_root" "$work/repo"
cd "$work/repo"
git config user.email "selftest@deckforge.invalid"
git config user.name "gate-selftest"
base="$(git rev-parse HEAD)"
first_test="$(git ls-files 'tests/test_*.py' | head -n 1)"

expect_fail() {
  local name="$1"
  if python ci/tamper_check.py --base "$base" >/dev/null 2>&1; then
    echo "SELFTEST FAILED: tamper check accepted bad change: $name"
    exit 1
  fi
  echo "ok: rejected $name"
  git reset --quiet --hard "$base"
}

git rm --quiet "$first_test"
git commit --quiet -m "bad: delete a test file"
expect_fail "deleted test file"

printf '\n# weakened\n' >> "$first_test"
git commit --quiet -am "bad: modify a test file"
expect_fail "modified test file"

mkdir -p src/deckforge
printf 'import pytest\n\n@pytest.mark.skip\ndef f():\n    pass\n' > src/deckforge/_bad.py
git add src/deckforge/_bad.py
git commit --quiet -m "bad: add skip marker"
expect_fail "added skip marker"

printf '\n' >> ci/tamper_check.py
git commit --quiet -am "bad: edit the gate itself"
expect_fail "edited protected ci/ file"

# And a clean change must still pass, or the gate is just broken.
printf 'X = 1\n' > src/deckforge/_ok.py
git add src/deckforge/_ok.py
git commit --quiet -m "good: add a module"
python ci/tamper_check.py --base "$base" >/dev/null
echo "ok: accepted clean change"
echo "gate self-test: all checks behaved as expected"
