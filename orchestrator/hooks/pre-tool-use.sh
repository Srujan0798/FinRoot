#!/usr/bin/env bash
# pre-tool-use: classify blast radius of a proposed command and gate it.
# Usage: pre-tool-use.sh "<command string>"   → exit 0 allow, 2 confirm, 3 block.
set -uo pipefail
CMD="${1:-}"

block() { echo "BLOCK (r5/T3): $1" >&2; exit 3; }
confirm() { echo "CONFIRM (r3+/T2): $1" >&2; exit 2; }

# r5 — money / destructive / data loss → block unconditionally
echo "$CMD" | grep -Eiq '(rm -rf /|drop +table|git +push +--force|force-push|place_order|execute_trade|transfer_funds|:money)' && block "$CMD"
# r3 — remote / live external calls → confirm
echo "$CMD" | grep -Eiq '(git +push|curl |wget |gh +(pr|release|repo) |alpha[_-]?vantage|newsapi|openai\.com|groq)' && confirm "$CMD"
# r2 — local services / db writes → confirm
echo "$CMD" | grep -Eiq '(alembic +upgrade|docker +compose +up|chroma|sqlite3 .*(insert|update|delete))' && confirm "$CMD"

exit 0   # r0/r1 — allow
