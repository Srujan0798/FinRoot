#!/usr/bin/env bash
# test_failures: print a summary of the most recent test failures, with
# the file:line of the failing assertion. Useful for triaging after a
# failed `make test`.
#
# Usage:
#   bash scripts/test_failures.sh                # use last pytest log
#   bash scripts/test_failures.sh /tmp/full.log  # use a specific log
#   bash scripts/test_failures.sh --rerun         # re-run pytest fast path, then summarize
set -uo pipefail
cd "$(dirname "$0")/.." || exit
export PYTHONPATH=src

LOG="${1:-/tmp/last_pytest.log}"
RERUN=0
if [ "$LOG" = "--rerun" ]; then
  RERUN=1
  LOG="/tmp/last_pytest.log"
fi

if [ "$RERUN" = "1" ]; then
  echo "Re-running pytest (fast path)..."
  python3 -m pytest --timeout=60 -m "not slow and not stress" > "$LOG" 2>&1 || true
fi

if [ ! -f "$LOG" ]; then
  echo "Log file $LOG not found."
  echo "  Run a test first (e.g. make test) or pass --rerun"
  exit 2
fi

echo "=== Test failure summary ==="
echo "Log: $LOG"
echo

# Extract failures
failures=$(grep -E "^FAILED " "$LOG" | sort -u)
if [ -z "$failures" ]; then
  # pytest sometimes uses "_____" header style or "X failed" summary line
  if grep -qE "[0-9]+ failed" "$LOG"; then
    n=$(grep -oE "[0-9]+ failed" "$LOG" | tail -1 | awk '{print $1}')
    if [ "$n" = "0" ]; then
      echo "No failures (0 failed)."
      exit 0
    fi
  fi
  echo "No FAILED lines found. Tail of log:"
  tail -20 "$LOG"
  exit 1
fi

echo "Failed tests:"
echo "$failures" | head -20
total=$(echo "$failures" | wc -l | tr -d ' ')
echo
echo "Total: $total failed tests"
echo

# For each failure, find the assertion error and the file:line
echo "=== Failure details (first 5) ==="
n=0
echo "$failures" | while read -r line; do
  n=$((n+1))
  if [ "$n" -gt 5 ]; then break; fi
  test_id=$(echo "$line" | sed -E 's/^FAILED //; s/ - .*//')
  echo
  echo "--- $test_id ---"
  # Find the AssertionError or similar in the log near this test_id
  grep -A 8 "$test_id" "$LOG" | grep -E "Error|assert|^E\s" | head -5
done
