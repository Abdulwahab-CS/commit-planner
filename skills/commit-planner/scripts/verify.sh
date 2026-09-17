#!/usr/bin/env bash
# Check the commits made from COMMIT_PLAN.md.
#
# Usage: bash verify.sh <base-sha>
# Exit:  0 verified | 1 something needs attention
set -uo pipefail
base="${1:?usage: bash verify.sh <base-sha>}"
cd "$(git rev-parse --show-toplevel)" || exit 2
pattern="${AUTHORSHIP_PATTERN:-co-authored-by|claude|anthropic|assistant|generated with}"
me="$(git config user.name) <$(git config user.email)>"
result=0

echo "== New commits =="
git log --reverse --oneline "$base..HEAD"

echo
echo "== Left uncommitted =="
left="$(git status --short --untracked-files=all)"
if [ -z "$left" ]; then echo "nothing"; else echo "$left"; result=1; fi

echo
echo "== Author | committer (expected: $me) =="
while IFS=$'\x1f' read -r sha author committer; do
  mark="ok"
  if [ "$author" != "$me" ] || [ "$committer" != "$me" ]; then mark="MISMATCH"; result=1; fi
  echo "$sha  $author | $committer  [$mark]"
done < <(git log --reverse --format='%h%x1f%an <%ae>%x1f%cn <%ce>' "$base..HEAD")

echo
echo "== Attribution text in messages (expect none) =="
found=0
for commit in $(git rev-list --reverse "$base..HEAD"); do
  hits="$(git log -1 --format=%B "$commit" | grep -inE "$pattern" || true)"
  if [ -n "$hits" ]; then
    echo "$(git rev-parse --short "$commit"): $hits"
    found=1
    result=1
  fi
done
if [ "$found" -eq 0 ]; then echo "none"; fi

echo
if [ "$result" -eq 0 ]; then echo "VERIFIED (nothing was pushed)"; else echo "NEEDS ATTENTION"; fi
exit "$result"
