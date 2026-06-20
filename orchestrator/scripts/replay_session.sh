#!/usr/bin/env bash
# replay_session: reconstruct minimal context for a wake() resume from the durable event log.
# Usage: replay_session.sh <wave> <task>   e.g. replay_session.sh wave-1 01
set -uo pipefail
cd "$(dirname "$0")/../.."
WAVE="${1:-}"; TASK="${2:-}"
DIR=orchestrator/memory/session

if [ -z "$WAVE" ]; then
  echo "Most recent session events across all tasks:"
  ls -t "$DIR"/*.events.jsonl 2>/dev/null | head -3 | while read -r f; do
    echo "--- $f ---"; tail -5 "$f"; done
  exit 0
fi

F="$DIR/${WAVE}-${TASK}.events.jsonl"
[ -f "$F" ] || { echo "no session log: $F"; exit 1; }
echo "=== replay $WAVE/$TASK ==="
echo "Last 8 events:"; tail -8 "$F"
echo "---"
echo "Last event type: $(tail -1 "$F" | grep -oE '"type": *"[^"]+"' | head -1)"
echo "Resume from the state implied by the last event above."
