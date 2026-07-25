#!/usr/bin/env bash
# session_start: print a one-page context summary for the start of a session.
# Use at the start of any new chat / agent context. Fast (<1s).
set -uo pipefail
cd "$(dirname "$0")/.."

HEAD=$(git rev-parse --short HEAD)
HEAD_MSG=$(git log -1 --format=%s)
BRANCH=$(git branch --show-current)
DATE=$(date +%Y-%m-%d)

echo "============================================================"
echo "FinRoot session context — $DATE"
echo "============================================================"
echo
echo "Repo:    $(basename "$PWD")"
echo "Branch:  $BRANCH"
echo "HEAD:    $HEAD — $HEAD_MSG"
echo

# Metric
if [ -f results/metrics.json ]; then
  METRIC_FINROOT=$(python3 -c "import json;d=json.load(open('results/metrics.json'));print(d['systems']['finroot']['mean_score'])" 2>/dev/null || echo "?")
  METRIC_RAG=$(python3 -c "import json;d=json.load(open('results/metrics.json'));print(d['systems']['rag']['mean_score'])" 2>/dev/null || echo "?")
  METRIC_SHA=$(python3 -c "import json;d=json.load(open('results/metrics.json'));print(d['as_of_sha'])" 2>/dev/null || echo "?")
  METRIC_LIFT=$(python3 -c "import json;d=json.load(open('results/metrics.json'));print(f\"{(d['systems']['finroot']['mean_score']/d['systems']['rag']['mean_score']-1)*100:.2f}%\")" 2>/dev/null || echo "?")
  echo "Metric:  FinRoot $METRIC_FINROOT vs RAG $METRIC_RAG = +$METRIC_LIFT lift"
  echo "         (stamped as_of_sha=$METRIC_SHA)"
  if [ "$METRIC_SHA" != "$HEAD" ]; then
    echo "         ⚠ metric is STALE (sha != HEAD); run \`make evals\` to refresh"
  fi
else
  echo "Metric:  MISSING — run \`make evals\` to generate"
fi
echo

# Tests
TEST_COUNT=$(PYTHONPATH=src python3 -m pytest --collect-only 2>/dev/null | grep -E "tests collected" | tail -1 | grep -oE "[0-9]+ tests? collected" | head -1 | awk '{print $1}')
if [ -n "$TEST_COUNT" ]; then
  echo "Tests:   $TEST_COUNT collected"
else
  echo "Tests:   (could not collect)"
fi
echo

# Working tree state
DIRTY=$(git status --short | head -5)
if [ -n "$DIRTY" ]; then
  echo "Working tree: dirty"
  echo "$DIRTY" | sed 's/^/  /'
  echo
else
  echo "Working tree: clean"
  echo
fi

# Sub-artifacts
[ -f finroot-submission.zip ] && echo "Zip:     finroot-submission.zip ($(stat -f%z finroot-submission.zip) bytes)"
echo

# Quick health checks
echo "Quick health:"
ruff check src/ tests/ scripts/ config/ 2>&1 | tail -1 | sed 's/^/  ruff: /'
bash orchestrator/scripts/validate_execution.sh 2>&1 | tail -1 | sed 's/^/  exec:  /'
bash orchestrator/scripts/validate_docs.sh 2>&1 | tail -1 | sed 's/^/  docs:  /'
echo
echo "============================================================"
echo "Next steps if needed:"
echo "  make install         # fresh deps"
echo "  make evals           # refresh metric at HEAD"
echo "  make test-cold --fast  # 1x cold suite (10min)"
echo "  make validate        # all structural checks"
echo "  bash scripts/make_submission.sh  # rebuild zip"
echo "============================================================"
