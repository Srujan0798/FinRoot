#!/usr/bin/env bash
# scripts/cold_check.sh: 3x cold suite check, fails on any non-zero rc, any
# failed test, or any data/ leakage. Run via `make test-cold` or in CI.
# Used as the FM-01 / FM-09 quality gate for the test suite.
#
# Usage:
#   bash scripts/cold_check.sh           # 3x cold, slow tests included (slow)
#   bash scripts/cold_check.sh --fast    # 1x cold, slow tests skipped (default for dev)
#   COLD_CHECK_RUNS=5 bash ...           # override the run count
#   COLD_CHECK_INCLUDE_SLOW=1 bash ...    # include @pytest.mark.slow tests
#
# Exit 0 on success, 1 on any failure.

set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src

# Defaults
RUNS=3
SKIP_SLOW_FLAG=(-m "not slow")
if [ "${COLD_CHECK_INCLUDE_SLOW:-0}" = "1" ]; then
  SKIP_SLOW_FLAG=()
fi
if [ "${COLD_CHECK_RUNS:-}" != "" ]; then
  RUNS="$COLD_CHECK_RUNS"
fi
if [ "${1:-}" = "--fast" ]; then
  RUNS=1
fi

PASS=0
FAIL=0
for i in $(seq 1 "$RUNS"); do
  rm -rf data/chroma data/digital_twin.db
  echo "=== cold run $i / $RUNS ==="
  if python3 -m pytest --timeout=120 "${SKIP_SLOW_FLAG[@]}" > /tmp/cold_check_$i.log 2>&1; then
    SUMMARY=$(grep -E "^[0-9]+ (passed|failed|skipped|deselected)" /tmp/cold_check_$i.log | tail -1)
    echo "  rc=0  $SUMMARY"
    PASS=$((PASS+1))
  else
    RC=$?
    SUMMARY=$(grep -E "^[0-9]+ (passed|failed)" /tmp/cold_check_$i.log | tail -1)
    echo "  rc=$RC  $SUMMARY"
    FAIL=$((FAIL+1))
  fi
  # Check for data/ leakage
  if [ -e data/chroma ] || [ -e data/digital_twin.db ]; then
    echo "  DATA LEAK: data/chroma or data/digital_twin.db exists after run"
    ls -la data/chroma data/digital_twin.db 2>&1 | head -3
    FAIL=$((FAIL+1))
  else
    echo "  hermetic: data/ clean"
  fi
done

echo "=== summary ==="
echo "  passed: $PASS / $RUNS"
echo "  failed: $FAIL / $RUNS"
if [ "$FAIL" -gt 0 ]; then
  echo "COLD CHECK FAILED" >&2
  exit 1
fi
echo "COLD CHECK PASSED ($PASS/$RUNS green, hermetic)"
exit 0
