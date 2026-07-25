#!/usr/bin/env bash
# doctor: smoke-check all FinRoot integrations.
# Fast (<30s). Exits 0 if all checks pass, 1 if any fail.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src

FAILED=0

check() {
  local label="$1"
  local cmd="$2"
  echo -n "  $label ... "
  if eval "$cmd" > /dev/null 2>&1; then
    echo "OK"
  else
    echo "FAIL"
    echo "    (run '$cmd' to debug)"
    FAILED=$((FAILED+1))
  fi
}

echo "=== FinRoot doctor ==="
echo

# 1. Python imports
check "Python: import finroot" \
  "python3 -c 'import finroot'"
check "Python: import interface" \
  "python3 -c 'import interface'"
check "Python: import config.settings" \
  "python3 -c 'from config.settings import get_settings'"
check "Python: import all agents" \
  "python3 -c 'from finroot.agents.market_agent import MarketAnalystAgent; from finroot.agents.tax_agent import TaxPlannerAgent; from finroot.agents.risk_agent import RiskAssessorAgent; from finroot.agents.portfolio_agent import PortfolioOptimizerAgent'"
check "Python: import all key tools" \
  "python3 -c 'from finroot.tools.market import MarketDataTool; from finroot.tools.profile import UserProfileTool; from finroot.tools.tax import TaxRuleTool; from finroot.tools.risk import RiskCalculationTool; from finroot.tools.documents import DocumentParserTool'"

# 2. CLI
check "CLI: --help exits 0" \
  "python3 -m interface.cli --help"
check "CLI: --mock runs end-to-end" \
  "python3 -m interface.cli --mock 'simple test'"

# 3. Pytest collection
check "pytest: collection works" \
  "python3 -m pytest --collect-only -q"

# 4. Validators
check "validate_execution.sh" \
  "bash orchestrator/scripts/validate_execution.sh"
check "validate_docs.sh" \
  "bash orchestrator/scripts/validate_docs.sh"
check "block-secrets.sh" \
  "bash orchestrator/hooks/block-secrets.sh"
check "ruff" \
  "ruff check src/ tests/ scripts/ config/"

# 5. Data integrity
check "FRB bank loads" \
  "python3 -c 'import json; d=json.load(open(\"data/gold/frb_questions.json\")); assert len(d) >= 83'"
check "Tax rules load" \
  "python3 -c 'import json; d=json.load(open(\"data/tax_rules.json\")); assert \"income_tax_slabs\" in d'"

# 6. Subprocess wrappers (conftest)
#    The conftest sets FINROOT_METRICS_PATH at module load. We test by
#    spawning a child process that imports it; the parent process env is
#    not modified by the conftest's autouse fixture.
check "conftest: FINROOT_METRICS_PATH set in child process" \
  "python3 -c 'import subprocess; r=subprocess.run([\"python3\", \"-c\", \"import tests.conftest, os; assert os.environ.get(\\\"FINROOT_METRICS_PATH\\\")\"], capture_output=True); assert r.returncode == 0'"

# 7. zip consistency (only if zip exists)
if [ -f finroot-submission.zip ]; then
  echo -n "  zip: contains results/metrics.json ... "
  if unzip -l finroot-submission.zip | grep -q "results/metrics.json"; then
    echo "OK"
  else
    echo "FAIL"
    FAILED=$((FAILED+1))
  fi
  SHA=$(git rev-parse --short HEAD)
  echo -n "  zip: internal metric matches HEAD ... "
  ZIP_SHA=$(unzip -p finroot-submission.zip results/metrics.json 2>/dev/null \
    | python3 -c "import json, sys; print(json.load(sys.stdin)['as_of_sha'])" 2>/dev/null || echo "?")
  if [ "$ZIP_SHA" = "$SHA" ]; then
    echo "OK"
  else
    echo "FAIL (zip=$ZIP_SHA HEAD=$SHA)"
    FAILED=$((FAILED+1))
  fi
else
  echo "  zip: SKIP (finroot-submission.zip not built)"
fi

echo
if [ "$FAILED" -gt 0 ]; then
  echo "FAILED: $FAILED check(s) failed"
  exit 1
fi
echo "All checks passed."
