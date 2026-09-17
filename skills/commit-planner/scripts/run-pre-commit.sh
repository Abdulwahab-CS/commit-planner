#!/usr/bin/env bash
# Run the repo's pre-commit hooks on every file, the way CI does.
#
# Usage: bash run-pre-commit.sh [--clean]
#   --clean   clear the hook cache first (pre-commit clean)
#
# Exit: 0 all clean | 1 errors left in your files | 2 setup problem
#       3 hooks changed files you did not touch (review before committing)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 2
export LC_ALL=C

if [ ! -f .pre-commit-config.yaml ]; then
  echo "No .pre-commit-config.yaml found: nothing to lint."
  exit 0
fi
if ! command -v pre-commit >/dev/null 2>&1; then
  echo "pre-commit is not installed (pip install pre-commit)."
  exit 2
fi

changed_files() { git status --porcelain --untracked-files=all | cut -c4- | sort; }
fingerprint() {
  { git diff HEAD 2>/dev/null; git ls-files -z --others --exclude-standard | xargs -0 cat 2>/dev/null; } | cksum
}
run_hooks() {
  local rc=0
  pre-commit run --all-files || rc=1
  # --all-files only sees tracked files, so lint new files too, as CI will after the commit.
  if [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git ls-files -z --others --exclude-standard | xargs -0 pre-commit run --files || rc=1
  fi
  return "$rc"
}

before="$(changed_files)"

if [ "${1:-}" = "--clean" ]; then
  pre-commit clean || exit 2
fi
# Build hook environments at the revs pinned in the config (never autoupdate).
pre-commit install-hooks || { echo "Could not install the hook environments."; exit 2; }

status=1
for pass in 1 2 3; do
  echo "== pass $pass =="
  start="$(fingerprint)"
  if run_hooks; then status=0; break; fi
  # Hooks failed without changing anything: the remaining errors need a manual fix.
  if [ "$(fingerprint)" = "$start" ]; then break; fi
done

outside="$(comm -13 <(printf '%s\n' "$before") <(changed_files) | sed '/^$/d')"
if [ -n "$outside" ]; then
  echo
  echo "Hooks changed files you did not touch:"
  printf '%s\n' "$outside" | sed 's/^/  /'
  echo "Review them: revert with 'git restore -- <file>', or keep them as a separate commit."
  exit 3
fi

echo
if [ "$status" -eq 0 ]; then
  echo "All hooks pass."
else
  echo "Hook errors remain (see above). Fix them and run again."
fi
exit "$status"
