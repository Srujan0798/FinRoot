#!/usr/bin/env bash
# validate_execution: catch drift in plan/EXECUTION.md (FM-01). Run after /merge + /ship + in CI.
set -uo pipefail
cd "$(dirname "$0")/../.."
F=plan/EXECUTION.md
[ -f "$F" ] || { echo "EXECUTION.md missing"; exit 1; }
FAIL=0

# 1. No duplicate wave numbers in the status table
DUPS=$(grep -E '^\| [0-9]+ \|' "$F" | awk -F'|' '{gsub(/ /,"",$2); print $2}' | sort | uniq -d)
if [ -n "$DUPS" ]; then echo "DRIFT: duplicate wave rows: $DUPS"; FAIL=1; fi

# 2. Active wave matches HANDOFF.md
WE=$(grep -E '^\*\*Active wave:\*\*' "$F" | grep -oE 'wave-[0-9]+' | head -1)
WH=$(grep -iE 'Active wave' HANDOFF.md | grep -oE 'wave-[0-9]+' | head -1)
if [ -n "$WE" ] && [ -n "$WH" ] && [ "$WE" != "$WH" ]; then
  echo "DRIFT: EXECUTION active=$WE but HANDOFF active=$WH"; FAIL=1; fi

# 3. Every SHIPPED wave has a commit hash (not the em-dash placeholder)
if grep -E 'SHIPPED' "$F" | grep -qE '\| +— +\|'; then
  echo "DRIFT: a SHIPPED wave has no commit hash:"; grep -E 'SHIPPED' "$F" | grep -E '\| +— +\|'; FAIL=1; fi

[ "$FAIL" -eq 0 ] && echo "EXECUTION.md is clean" || true
exit $FAIL
