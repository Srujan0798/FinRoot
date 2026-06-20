#!/usr/bin/env bash
# Render docs/architecture/architecture.mmd to PNG (or SVG fallback).
# Usage: bash scripts/render_diagram.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MMD="$REPO_ROOT/docs/architecture/architecture.mmd"
PNG="$REPO_ROOT/docs/architecture/architecture.png"
SVG="$REPO_ROOT/docs/architecture/architecture.svg"

if [ ! -f "$MMD" ]; then
  echo "ERROR: $MMD not found" >&2
  exit 1
fi

# Strip comment lines starting with %%
CLEAN=$(grep -v '^\s*%%' "$MMD" | sed '/^$/d')

render_mmdc() {
  if command -v mmdc &>/dev/null; then
    mmdc -i "$MMD" -o "$PNG" -b transparent 2>/dev/null
    echo "Rendered via mmdc -> $PNG"
    return 0
  fi
  return 1
}

render_mermaid_py() {
  python3 -c "
from mermaid import Mermaid
from mermaid.graph import Graph

script = '''$CLEAN'''
g = Graph('FinRoot Architecture', script)
m = Mermaid(g)
m.to_png('$PNG')
" 2>/dev/null
  echo "Rendered via mermaid-py -> $PNG"
  return 0
}

render_svg_fallback() {
  python3 "$SCRIPT_DIR/_render_svg.py" "$MMD" "$SVG" 2>/dev/null
  echo "Rendered SVG fallback -> $SVG"
  return 0
}

if render_mmdc; then
  exit 0
elif render_mermaid_py; then
  exit 0
elif render_svg_fallback; then
  exit 0
else
  echo "ERROR: All rendering methods failed" >&2
  exit 1
fi
