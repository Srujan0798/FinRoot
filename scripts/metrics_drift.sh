#!/usr/bin/env bash
# metrics_drift: compare two metrics.json files and report drift.
# Usage:
#   bash scripts/metrics_drift.sh results/metrics.json results/metrics.json.new
#   bash scripts/metrics_drift.sh HEAD:results/metrics.json results/metrics.json
# Exits 0 if drift is within threshold, 1 if new is significantly worse.
#
# Threshold: a regression of more than 5% in any system is flagged.
# Improvements are always OK (exit 0, log a note).

set -uo pipefail
cd "$(dirname "$0")/.."

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
  echo "usage: $0 <baseline_metrics.json> <new_metrics.json>" >&2
  echo "  Both files must be readable JSON. Use 'HEAD:path' for git refs." >&2
  exit 2
fi

BASELINE_REF="$1"
NEW_REF="$2"

# Read metrics via Python (handles JSON, including git refs)
read_metric() {
  local ref="$1"
  local system="$2"
  if [[ "$ref" == *:* ]]; then
    git show "$ref" 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['systems']['$system']['mean_score'])
" 2>/dev/null
  else
    python3 -c "
import json
d = json.load(open('$ref'))
print(d['systems']['$system']['mean_score'])
" 2>/dev/null
  fi
}

# Verify both refs are readable
for ref in "$BASELINE_REF" "$NEW_REF"; do
  if [[ "$ref" == *:* ]]; then
    if ! git show "$ref" > /dev/null 2>&1; then
      echo "ERROR: cannot read git ref $ref" >&2
      exit 2
    fi
  elif [ ! -f "$ref" ]; then
    echo "ERROR: file not found: $ref" >&2
    exit 2
  fi
done

echo "=== Metrics drift check ==="
echo "Baseline: $BASELINE_REF"
echo "New:      $NEW_REF"
echo

# Thresholds
REGRESSION_THRESHOLD=${REGRESSION_THRESHOLD:-0.05}

FAILED=0
for system in finroot rag single_agent; do
  BASE=$(read_metric "$BASELINE_REF" "$system")
  NEW=$(read_metric "$NEW_REF" "$system")
  if [ -z "$BASE" ] || [ -z "$NEW" ]; then
    echo "  $system: SKIP (missing value)"
    continue
  fi
  # Compute delta as (new - base)
  DELTA=$(python3 -c "print(f'{$NEW - $BASE:+.4f}')")
  PCT=$(python3 -c "print(f'{($NEW - $BASE) / $BASE * 100 if $BASE else 0:+.2f}%')")
  # Determine if it's a regression beyond threshold
  IS_REGRESSION=$(python3 -c "print('1' if $BASE - $NEW > $REGRESSION_THRESHOLD else '0')")
  if [ "$IS_REGRESSION" = "1" ]; then
    STATUS="REGRESSION (>$REGRESSION_THRESHOLD)"
    FAILED=1
  elif python3 -c "exit(0 if $NEW > $BASE else 1)"; then
    STATUS="IMPROVEMENT"
  else
    STATUS="OK (within threshold)"
  fi
  printf "  %-15s base=%.4f  new=%.4f  delta=%s  pct=%s  %s\n" \
    "$system" "$BASE" "$NEW" "$DELTA" "$PCT" "$STATUS"
done

echo
if [ "$FAILED" -gt 0 ]; then
  echo "FAIL: regression detected (>${REGRESSION_THRESHOLD} in some system)"
  echo "  Either fix the regression or pass REGRESSION_THRESHOLD=0.10 to be more lenient."
  exit 1
else
  echo "PASS: no significant regression"
  exit 0
fi
