#!/usr/bin/env bash
# stop: end-of-session hygiene. Reminds the orchestrator to leave the repo resumable.
set -uo pipefail
cd "$(dirname "$0")/../.."
echo "=== session stop checklist ==="
echo "[ ] HANDOFF.md rewritten to current truth (run /handoff)"
echo "[ ] EXECUTION.md matches reality (bash orchestrator/scripts/validate_execution.sh)"
echo "[ ] events.jsonl has the latest decisions"
echo "[ ] no secrets staged (bash orchestrator/hooks/block-secrets.sh)"
bash orchestrator/scripts/validate_execution.sh 2>/dev/null || echo "    -> EXECUTION drift detected, fix before leaving"
