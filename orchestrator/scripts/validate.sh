#!/usr/bin/env bash
# validate: structural integrity checks for the FinRoot OS. Run before dispatch + in CI.
set -uo pipefail
cd "$(dirname "$0")/../.."
FAIL=0
note() { echo "  - $1"; }

echo "== FinRoot validate =="

# 1. Required root files exist
for f in CLAUDE.md KIMI.md AGENTS.md HANDOFF.md HIERARCHY.md README.md plan/PRD.md \
         plan/ARCHITECTURE.md plan/EXECUTION.md .specify/memory/constitution.md mcp.json Makefile; do
  [ -f "$f" ] || { note "MISSING: $f"; FAIL=1; }
done

# 2. KIMI.md / AGENTS.md identical to CLAUDE.md (interchangeable orchestrators)
if ! diff -q CLAUDE.md KIMI.md >/dev/null 2>&1; then note "KIMI.md differs from CLAUDE.md"; FAIL=1; fi
if ! diff -q CLAUDE.md AGENTS.md >/dev/null 2>&1; then note "AGENTS.md differs from CLAUDE.md"; FAIL=1; fi

# 3. Disjoint write-sets across pending wave task files (FM-13)
#    Parse ONLY the "## Writes" block of each task file (until the next "## " header), so
#    import-references and acceptance commands elsewhere in the file don't false-positive.
for wave in work/wave-*; do
  [ -d "$wave" ] || continue
  # emit "path<TAB>file" for each backtick path inside a Writes block, one path per file (dedup within file)
  PAIRS=$(for f in "$wave"/*.md; do
    [ -f "$f" ] || continue
    awk '/^## Writes/{inw=1; next} /^## /{inw=0} inw' "$f" \
      | grep -oE '`[^`]+`' | tr -d '`' \
      | grep -E '^(src|config|scripts|tests|data|schema)/' \
      | sed 's#/\*\*$##; s#\*\*##g' \
      | sort -u | sed "s#\$#\t$(basename "$f")#"
  done)
  # a path owned by >1 distinct file is a real collision
  DUPS=$(echo "$PAIRS" | awk -F'\t' 'NF==2{c[$1]++; who[$1]=who[$1]" "$2} END{for(p in c) if(c[p]>1) print p" -> owned by:"who[p]}')
  if [ -n "$DUPS" ]; then note "SHARED write target in $wave (FM-13):"; echo "$DUPS" | sed 's/^/      /'; FAIL=1; fi
done

# 4. No obvious secrets tracked (FM-07)
if git ls-files 2>/dev/null | grep -qx ".env"; then note ".env is tracked — must be gitignored"; FAIL=1; fi

[ "$FAIL" -eq 0 ] && echo "validate: OK" || echo "validate: ISSUES FOUND"
exit $FAIL
