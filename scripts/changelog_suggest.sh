#!/usr/bin/env bash
# changelog_suggest: suggest a CHANGELOG.md entry from the last N commits.
# Does NOT auto-write — prints a draft to stdout for the human to review.
#
# Usage:
#   bash scripts/changelog_suggest.sh           # last 10 commits
#   bash scripts/changelog_suggest.sh 5         # last 5 commits
#   bash scripts/changelog_suggest.sh HEAD~3    # explicit range
set -uo pipefail
cd "$(dirname "$0")/.."

RANGE="${1:-HEAD~10..HEAD}"
COMMITS=$(git log --oneline "$RANGE" 2>/dev/null || true)
if [ -z "$COMMITS" ]; then
  echo "No commits found in range $RANGE" >&2
  exit 1
fi

# Categorize by commit message prefix
FIXES=""
FEATS=""
CHORES=""
TESTS=""
DOCS=""
OTHER=""

while IFS= read -r line; do
  hash=$(echo "$line" | awk '{print $1}')
  msg=$(echo "$line" | sed -E 's/^[a-f0-9]+ //')
  if echo "$msg" | grep -qE "^fix(\(.*\))?:"; then
    FIXES="${FIXES}- ${msg}\n"
  elif echo "$msg" | grep -qE "^feat(\(.*\))?:"; then
    FEATS="${FEATS}- ${msg}\n"
  elif echo "$msg" | grep -qE "^test(\(.*\))?:"; then
    TESTS="${TESTS}- ${msg}\n"
  elif echo "$msg" | grep -qE "^docs(\(.*\))?:"; then
    DOCS="${DOCS}- ${msg}\n"
  elif echo "$msg" | grep -qE "^chore(\(.*\))?:"; then
    CHORES="${CHORES}- ${msg}\n"
  else
    OTHER="${OTHER}- ${msg}\n"
  fi
done <<< "$COMMITS"

SHA=$(git rev-parse --short HEAD)
DATE=$(git log -1 --format=%ad --date=short)
echo "### $(date +%Y-%m-%d) — suggested from $RANGE (current HEAD: $SHA)"
echo
if [ -n "$FEATS" ]; then
  echo "#### Features"
  printf "%b" "$FEATS"
  echo
fi
if [ -n "$FIXES" ]; then
  echo "#### Fixes"
  printf "%b" "$FIXES"
  echo
fi
if [ -n "$TESTS" ]; then
  echo "#### Tests"
  printf "%b" "$TESTS"
  echo
fi
if [ -n "$DOCS" ]; then
  echo "#### Docs"
  printf "%b" "$DOCS"
  echo
fi
if [ -n "$CHORES" ]; then
  echo "#### Chores"
  printf "%b" "$CHORES"
  echo
fi
if [ -n "$OTHER" ]; then
  echo "#### Other"
  printf "%b" "$OTHER"
  echo
fi
echo
echo "# Copy-paste this block into CHANGELOG.md under the next release header."
