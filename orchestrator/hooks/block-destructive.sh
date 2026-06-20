#!/usr/bin/env bash
# block-destructive: hard stop on irreversible operations (T3). Usage: block-destructive.sh "<cmd>"
set -uo pipefail
CMD="${1:-}"
DESTRUCTIVE='(rm -rf (/|~|\*)|git +reset +--hard +origin|git +push +--force|drop +database|drop +table|truncate +table|mkfs|dd +if=)'
if echo "$CMD" | grep -Eiq "$DESTRUCTIVE"; then
  echo "BLOCKED (T3, irreversible): $CMD" >&2
  echo "If truly intended, a human must run it manually outside the agent." >&2
  exit 3
fi
exit 0
