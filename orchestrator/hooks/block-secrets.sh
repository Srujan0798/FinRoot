#!/usr/bin/env bash
# block-secrets: scan staged changes for secrets before commit (FM-07 publish gate).
set -uo pipefail
cd "$(dirname "$0")/../.."
DIFF=$(git diff --cached -U0 2>/dev/null || true)
PATTERNS='(api[_-]?key|secret|password|token|BEGIN (RSA|OPENSSH) PRIVATE KEY|sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})'
HITS=$(echo "$DIFF" | grep -nEi "$PATTERNS" | grep -viE '(\.env\.example|example|placeholder|<your|FINROOT_)' || true)
if [ -n "$HITS" ]; then
  echo "BLOCK: possible secret in staged changes (FM-07). Move to .env (gitignored) and rotate:" >&2
  echo "$HITS" >&2
  exit 3
fi
echo "secret scan clean"; exit 0
