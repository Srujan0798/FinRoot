#!/usr/bin/env bash
# validate_doc_links: check that internal .md cross-references resolve.
# Scans all .md files for:
#   - Standard markdown links: [text](relative/path.md)
#   - Backtick code references: `relative/path.md`
# and verifies each target exists. Ignores http(s)://, mailto:, and anchor-only refs.
# Fast (<1s). Bash 3.2 compatible.
set -uo pipefail
# cd to repo root (script lives in orchestrator/scripts/)
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

FAILED=0
CHECKED=0

# Find .md files, but skip orchestrator-internal docs (they reference files
# that exist relative to the repo root, but live in orchestrator/ subdirs)
# The user-facing docs (HANDOFF, README, business/, etc.) are checked.
MD_FILES=$(find . -name "*.md" \
  -not -path "./.*" \
  -not -path "*/node_modules/*" \
  -not -path "*/__pycache__/*" \
  -not -path "./orchestrator*" \
  -not -path "./.specify/*" \
  -not -path "./work/*" \
  2>/dev/null || true)

while IFS= read -r md; do
  [ -z "$md" ] && continue

  # 1. Standard markdown links: [text](path)
  links=$(grep -oE '\[[^]]+\]\([^)]+\)' "$md" 2>/dev/null | sed -E 's/\[[^]]+\]\(([^)]+)\)/\1/' || true)
  while IFS= read -r link; do
    [ -z "$link" ] && continue
    case "$link" in
      http://*|https://*|mailto:*|ftp://*|\#*) continue ;;
    esac
    link="${link%%#*}"
    [ -z "$link" ] && continue
    md_dir=$(dirname "$md")
    # Resolve file-relative first, then fall back to repo-root-relative —
    # this codebase's convention (e.g. src/README.md's wave-task map) commonly
    # writes repo-root-relative backtick/link paths regardless of the
    # referencing file's own location.
    if [ -f "$md_dir/$link" ] || [ -f "$link" ]; then
      CHECKED=$((CHECKED+1))
    else
      echo "BROKEN LINK in $md: $link"
      FAILED=$((FAILED+1))
    fi
  done <<< "$links"

  # 2. Backtick code references to .md files: `path/to/foo.md`
  #    Only check if the file is .md (other file types are checked elsewhere).
  md_links=$(grep -oE '`[A-Za-z0-9_./-]+\.md`' "$md" 2>/dev/null | sed -E 's/`([^`]+)`/\1/' || true)
  while IFS= read -r link; do
    [ -z "$link" ] && continue
    md_dir=$(dirname "$md")
    if [ -f "$md_dir/$link" ] || [ -f "$link" ]; then
      CHECKED=$((CHECKED+1))
    else
      echo "BROKEN DOC REF in $md: \`$link\`"
      FAILED=$((FAILED+1))
    fi
  done <<< "$md_links"
done <<< "$MD_FILES"

echo "=== Doc link validation ==="
echo "  Checked: $CHECKED refs"
echo "  Broken:  $FAILED"
if [ "$FAILED" -gt 0 ]; then
  echo "FAIL"
  exit 1
fi
echo "OK"
