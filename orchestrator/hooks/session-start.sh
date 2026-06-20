#!/usr/bin/env bash
# session-start: orient a fresh orchestrator session. Prints current state, no mutations (r0).
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "=== FinRoot session start ==="
if [ -f HANDOFF.md ]; then
  echo "--- HANDOFF (active wave / next action) ---"
  grep -E "Active wave|Immediate next action|Phase" -A1 HANDOFF.md | head -12 || true
fi
if [ -f plan/EXECUTION.md ]; then
  echo "--- EXECUTION (wave table) ---"
  grep -E "^\| [0-9]" plan/EXECUTION.md || true
fi
LATEST=$(ls -t orchestrator/memory/session/*.events.jsonl 2>/dev/null | head -1 || true)
if [ -n "${LATEST:-}" ]; then
  echo "--- last 3 events ($LATEST) ---"
  tail -3 "$LATEST" || true
fi
echo "=== read CLAUDE.md, then run /status ==="
