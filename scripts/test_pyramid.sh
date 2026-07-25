#!/usr/bin/env bash
# test_pyramid: print a breakdown of the test suite by category.
# Shows unit, integration, e2e, security, slow, stress counts.
# Fast (<3s). Bash 3.2 compatible (no associative arrays).
set -uo pipefail
cd "$(dirname "$0")/.." || exit

# One collect pass; parse the listing (no -q so markers are visible)
COLLECT=$(PYTHONPATH=src python3 -m pytest --collect-only --no-header 2>/dev/null || true)
total=$(echo "$COLLECT" | grep -E "tests collected" | tail -1 | grep -oE "^[0-9]+")

# Per-folder counts by parsing the file path
count_in() {
  local prefix="$1"
  echo "$COLLECT" | grep -cE "^${prefix}/" || true
}

unit=$(count_in "tests/unit")
integration=$(count_in "tests/integration")
e2e=$(count_in "tests/e2e")
golden=$(count_in "tests/golden")
fuzz=$(count_in "tests/fuzz")
performance=$(count_in "tests/performance")
security=$(count_in "tests/security")
stress=$(count_in "tests/stress")

# Per-marker counts are collected via the per-folder loop below

echo "=== Test pyramid ==="
echo
printf "%-15s %6s\n" "CATEGORY" "COUNT"
printf "%-15s %6s\n" "-------" "-----"
printf "%-15s %6s\n" "TOTAL" "$total"
echo
printf "%-15s %6s\n" "unit" "$unit"
printf "%-15s %6s\n" "integration" "$integration"
printf "%-15s %6s\n" "e2e" "$e2e"
printf "%-15s %6s\n" "golden" "$golden"
printf "%-15s %6s\n" "fuzz" "$fuzz"
printf "%-15s %6s\n" "performance" "$performance"
printf "%-15s %6s\n" "security" "$security"
printf "%-15s %6s\n" "stress" "$stress"
echo
echo "Per-marker (overlaps with per-folder):"
for marker in slow stress security integration e2e golden; do
  count=$(PYTHONPATH=src python3 -m pytest --collect-only -m "$marker" --no-header 2>/dev/null \
    | grep -E "tests collected" | tail -1 | grep -oE "^[0-9]+" || true)
  count="${count:-0}"
  printf "  @pytest.mark.%-10s %6s\n" "$marker" "$count"
done
echo

# Test-file count delta vs previous commit (cheap heuristic)
if git rev-parse HEAD~1 > /dev/null 2>&1; then
  echo "Test files vs HEAD~1:"
  for cat in unit integration e2e golden fuzz performance security stress; do
    cur=$(find "tests/$cat" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
    prev=$(git ls-tree -r --name-only HEAD~1 "tests/$cat/" 2>/dev/null \
      | grep -c "test_.*\.py$" || true)
    prev="${prev:-0}"
    if [ "$cur" -gt "$prev" ]; then
      delta="+$((cur - prev))"
    elif [ "$cur" -lt "$prev" ]; then
      delta="$((cur - prev))"
    else
      delta="="
    fi
    printf "  %-13s %3s  (delta: %s)\n" "$cat" "$cur" "$delta"
  done
fi
echo

# Time budget estimate
total_int=${total:-0}
fast_min=$(python3 -c "print(f'{max(0, $total_int - 5) * 0.3 / 60:.1f}')")
full_min=$(python3 -c "print(f'{$total_int * 0.3 / 60:.1f}')")
echo "Time budget estimate (single run, 1 worker):"
echo "  full suite (no skips):     ~${full_min} min"
echo "  --fast (no slow/stress):   ~${fast_min} min"
echo "  --slow only:                ~5-10 min"
echo "  --stress only:              ~1 min"
