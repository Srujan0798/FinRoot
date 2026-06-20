#!/usr/bin/env bash
# post-merge-format: auto-format + quick lint after a merge (r1, auto-safe).
set -uo pipefail
cd "$(dirname "$0")/../.."
if command -v ruff >/dev/null 2>&1; then
  ruff format src/ tests/ 2>/dev/null || true
  ruff check --fix src/ tests/ 2>/dev/null || true
  echo "ruff format + autofix done"
else
  echo "ruff not installed; skipping format"
fi
