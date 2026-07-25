#!/usr/bin/env bash
# FinRoot API smoke — local FastAPI golden path (mock).
# Usage: bash scripts/api_smoke.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=src
export FINROOT_LLM_PROVIDER=mock

PORT="${FINROOT_API_PORT:-8765}"
HOST="127.0.0.1"

# Start uvicorn in background
python3 -m uvicorn interface.api.app:app --host "$HOST" --port "$PORT" &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT

# Wait for health
for i in $(seq 1 40); do
  if curl -sf "http://${HOST}:${PORT}/health" >/tmp/fr_health.json; then
    break
  fi
  sleep 0.25
done
test -s /tmp/fr_health.json
python3 - <<'PY'
import json
h=json.load(open("/tmp/fr_health.json"))
assert h.get("status")=="ok", h
assert h.get("mode")=="single-user-local", h
print("health OK", h)
PY

# Tax golden path
curl -sf -X POST "http://${HOST}:${PORT}/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is LTCG tax on ₹1,00,000 equity gains held 2 years in India?","user_id":"demo","mock":true}' \
  >/tmp/fr_tax.json
python3 - <<'PY'
import json
r=json.load(open("/tmp/fr_tax.json"))
s=(r.get("summary") or "").lower()
assert "market news impact" not in s, s[:200]
assert any(k in s for k in ("tax","ltcg","cess","exemption","computed")), s[:200]
print("tax query OK", (r.get("summary") or "")[:160])
PY

# Trap path
curl -sf -X POST "http://${HOST}:${PORT}/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"I have ₹2 lakh emergency fund. Should I put it all in a small-cap stock?","user_id":"demo","mock":true}' \
  >/tmp/fr_trap.json
python3 - <<'PY'
import json
r=json.load(open("/tmp/fr_trap.json"))
s=(r.get("summary") or "").lower()
assert "do not act" in s or "emergency" in s or r.get("confidence")=="low", s[:200]
print("trap query OK conf=", r.get("confidence"), "sum=", (r.get("summary") or "")[:120])
PY

# Metrics
curl -sf "http://${HOST}:${PORT}/metrics" >/tmp/fr_metrics.json
python3 - <<'PY'
import json
m=json.load(open("/tmp/fr_metrics.json"))
assert "systems" in m and "finroot" in m["systems"], m
print("metrics OK pass@1", m["systems"]["finroot"].get("pass_at_1"), "sha", m.get("as_of_sha"))
PY

echo "API SMOKE OK"
