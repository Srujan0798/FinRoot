#!/usr/bin/env bash
# context-budget-report: rough token estimate of the always-loaded context (FM-04).
set -uo pipefail
cd "$(dirname "$0")/../.."
est() { [ -f "$1" ] && awk 'END{printf "%d", NR}' "$1" >/dev/null; \
        local words; words=$(wc -w < "$1" 2>/dev/null || echo 0); echo $(( words * 4 / 3 )); }
total=0
echo "Approx token budget (words * 4/3):"
for f in CLAUDE.md HANDOFF.md plan/EXECUTION.md; do
  if [ -f "$f" ]; then t=$(est "$f"); total=$((total+t)); printf "  %-22s ~%5d\n" "$f" "$t"; fi
done
echo "  ----------------------------"
printf "  %-22s ~%5d\n" "always-loaded total" "$total"
[ "$total" -gt 6000 ] && echo "  WARN: kernel context heavy (>6k). Trim CLAUDE.md / compact HANDOFF."
echo "(active spec + one task file are loaded on demand, budget ~2k + ~1.5k each)"
