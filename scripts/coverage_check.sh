#!/usr/bin/env bash
# coverage_check: run pytest with coverage, fail if total coverage drops below
# the threshold in .coverage-threshold (default 80%).
#
# Usage:
#   bash scripts/coverage_check.sh            # check vs threshold
#   bash scripts/coverage_check.sh 85         # set a new threshold
#   bash scripts/coverage_check.sh --baseline # save current as new baseline
#
# The check is fast (~9 min) and runs the full suite minus @pytest.mark.slow
# to keep the iteration loop quick.
set -uo pipefail
cd "$(dirname "$0")/.." || exit

THRESHOLD_FILE=".coverage-threshold"
DEFAULT_THRESHOLD=80
SAVING_BASELINE=0

if [ "${1:-}" = "--baseline" ]; then
  SAVING_BASELINE=1
elif [ -n "${1:-}" ] && [ "${1:-}" != "--baseline" ]; then
  echo "$1" > "$THRESHOLD_FILE"
  echo "Threshold set to $1% in $THRESHOLD_FILE"
  exit 0
fi

if [ -f "$THRESHOLD_FILE" ]; then
  THRESHOLD=$(cat "$THRESHOLD_FILE")
else
  THRESHOLD=$DEFAULT_THRESHOLD
fi

echo "Running pytest with coverage (threshold=${THRESHOLD}%)..."
export PYTHONPATH=src
COVERAGE_OUTPUT=$(python3 -m pytest --cov=src --cov-report=term --no-cov-on-fail -m "not slow" --timeout=60 -q 2>&1 || true)

# Parse the TOTAL line
TOTAL_LINE=$(echo "$COVERAGE_OUTPUT" | grep -E "^TOTAL\s+[0-9]+\s+[0-9]+\s+[0-9]+%" | tail -1)
if [ -z "$TOTAL_LINE" ]; then
  echo "ERROR: could not parse coverage output" >&2
  echo "$COVERAGE_OUTPUT" | tail -20
  exit 1
fi

# Extract the percentage: "TOTAL  5809  1085  81%"
COVERAGE_PCT=$(echo "$TOTAL_LINE" | awk '{print $NF}' | tr -d '%')
echo "Coverage: $COVERAGE_PCT% (threshold: $THRESHOLD%)"

# Check for failures
if echo "$COVERAGE_OUTPUT" | grep -qE "[0-9]+ failed"; then
  FAILURES=$(echo "$COVERAGE_OUTPUT" | grep -E "^[0-9]+ failed" | tail -1)
  echo "WARNING: tests had failures: $FAILURES"
fi

if [ "$SAVING_BASELINE" = "1" ]; then
  # Round down to whole number for the threshold
  ROUNDED=$(python3 -c "import math; print(int(math.floor($COVERAGE_PCT)))")
  echo "$ROUNDED" > "$THRESHOLD_FILE"
  echo "Saved baseline: ${ROUNDED}% → $THRESHOLD_FILE"
  exit 0
fi

# Compare (use python for float comparison to avoid bc dep)
PASS=$(python3 -c "print('1' if $COVERAGE_PCT >= $THRESHOLD else '0')")
if [ "$PASS" = "1" ]; then
  echo "PASS: coverage $COVERAGE_PCT% >= $THRESHOLD%"
  exit 0
else
  echo "FAIL: coverage $COVERAGE_PCT% < $THRESHOLD%"
  exit 1
fi
