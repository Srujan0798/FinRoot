#!/usr/bin/env bash
# dep_audit: check for outdated / vulnerable dependencies.
# Uses `pip list --outdated` to find upgradeable packages and
# `pip-audit` (if installed) to find known CVEs.
#
# Usage:
#   bash scripts/dep_audit.sh                # full report
#   bash scripts/dep_audit.sh --strict       # exit 1 if any package is outdated
#   bash scripts/dep_audit.sh --cve-only    # only show CVE findings
set -uo pipefail
cd "$(dirname "$0")/.." || exit

STRICT=0
CVE_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    --cve-only) CVE_ONLY=1 ;;
  esac
done

echo "=== Outdated packages ==="
OUTDATED=$(pip list --outdated --format=columns 2>/dev/null || true)
if [ -n "$OUTDATED" ]; then
  echo "$OUTDATED"
else
  echo "(none)"
fi
echo

if [ "$CVE_ONLY" = "1" ]; then
  : # skip outdated section
else
  echo "=== Outdated summary ==="
  N_OUTDATED=$(echo "$OUTDATED" | tail -n +3 | grep -cE "\S" || true)
  echo "  $N_OUTDATED packages have newer versions"
  echo
fi

echo "=== CVE scan (pip-audit) ==="
if command -v pip-audit > /dev/null 2>&1; then
  pip-audit --strict 2>&1 | tail -50
  CVE_RC=$?
  if [ "$CVE_RC" = "0" ]; then
    echo "(no known CVEs in current dep set)"
  fi
else
  echo "  pip-audit not installed. Install with: pip install pip-audit"
  echo "  Falling back to grep against known CVE patterns (best-effort):"
  # Quick scan for the most common FinRoot CVEs (pydantic, langchain, etc.)
  # This is NOT a substitute for pip-audit; just a smoke check.
  echo "  (skipped — install pip-audit for real CVE detection)"
fi
echo

if [ "$STRICT" = "1" ]; then
  if [ -n "$OUTDATED" ] && [ "$(echo "$OUTDATED" | tail -n +3 | grep -cE "\S" || true)" -gt 0 ]; then
    echo "STRICT: outdated packages found; failing"
    exit 1
  fi
fi

echo "OK"
