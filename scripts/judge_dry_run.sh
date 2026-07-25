#!/usr/bin/env bash
# FinRoot — cold stranger / judge dry-run (offline mock).
# One command a hostile judge can run after install.
# Usage: bash scripts/judge_dry_run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=src
export FINROOT_LLM_PROVIDER=mock

echo "=== [1/5] Foundation smoke ==="
python3 scripts/smoke_test.py | tail -5

echo "=== [2/5] Sacred golden + FR domain locks ==="
# NOTE: test_zip_consistency.py is deliberately excluded here. It checks
# finroot-submission.zip, which is gitignored and will not exist on a
# fresh `git clone` — that's a submission-packaging gate (see
# scripts/make_submission.sh), not part of the stranger/judge golden path.
python3 -m pytest \
  tests/golden/test_golden_paths_ps1.py \
  tests/golden/test_fr_domains.py \
  tests/unit/test_intent.py \
  tests/unit/test_principles.py \
  tests/unit/test_metrics_freshness.py \
  -q --tb=line
echo "pytest locks OK"

echo "=== [3/5] Live GP answer probes ==="
python3 - <<'PY'
from interface.core import answer

def run(q, checks):
    s = answer(q, user_id="demo", mock=True)
    rec = s.final or s.candidate
    assert rec is not None, q
    text = (rec.summary or "").lower()
    for pred, msg in checks:
        assert pred(s, rec, text), f"{msg}: {text[:200]}"
    print("OK", q[:60])

run(
    "Should I rebalance my 70/30 equity portfolio before FY-end?",
    [
        (lambda s, r, t: "market news impact" not in t, "portfolio not news"),
        (lambda s, r, t: str(s.intent).endswith("PORTFOLIO") or getattr(s.intent, "value", "") == "portfolio", "intent portfolio"),
    ],
)
run(
    "What is LTCG tax on ₹1,00,000 equity gains held 2 years in India?",
    [
        (lambda s, r, t: "market news impact" not in t, "tax not news"),
        (lambda s, r, t: any(k in t for k in ("tax", "ltcg", "cess", "exemption", "computed")), "tax content"),
    ],
)
run(
    "I have ₹2 lakh emergency fund. Should I put it all in a small-cap stock?",
    [
        (lambda s, r, t: "do not act" in t or "refuse" in t, "refuse language"),
        (lambda s, r, t: str(getattr(r.confidence, "value", r.confidence)).lower() == "low", "low conf"),
        (lambda s, r, t: (s.verifier_verdict or {}).get("compliant") is False, "prudence fail"),
    ],
)
run(
    "Should I take a personal loan to buy more stocks for higher returns?",
    [
        (lambda s, r, t: "market news impact" not in t, "not news"),
        (lambda s, r, t: str(s.intent).endswith("RISK") or getattr(s.intent, "value", "") == "risk", "intent risk"),
    ],
)
run(
    "Calculate VaR and max drawdown for my portfolio",
    [
        (lambda s, r, t: str(s.intent).endswith("RISK") or getattr(s.intent, "value", "") == "risk", "intent risk"),
        (lambda s, r, t: "market news impact" not in t, "not news"),
    ],
)
print("GP probes OK")
PY

echo "=== [4/5] API smoke ==="
bash scripts/api_smoke.sh | tail -15

echo "=== [5/5] Metrics snapshot ==="
python3 - <<'PY'
import json
from pathlib import Path
m=json.load(open("results/metrics.json"))
fr=m["systems"]["finroot"]
print(f"as_of_sha={m.get('as_of_sha')} pass@1={fr['pass_at_1']} mean={fr['mean_score']} lift={m.get('composite_lift_vs_rag_pct')}")
shots=list(Path("docs/demo/screenshots").glob("*.png"))
assert len(shots) >= 5, shots
print(f"screenshots={len(shots)} OK")
PY

echo ""
echo "JUDGE DRY-RUN OK — offline golden path locked."
