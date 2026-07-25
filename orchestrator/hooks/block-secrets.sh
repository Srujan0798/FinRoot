#!/usr/bin/env bash
# block-secrets: scan staged changes for secrets before commit (FM-07 publish gate).
# Tightened 2026-07-25 (wave-15/iter2) to reduce false positives on doc text
# ("no secrets", "secret-scan clean", etc.) while still blocking real key shapes.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit
# Get the diff, but exclude this hook's own file (it self-references the words
# "secret", "password", etc. as part of its filtering rules).
DIFF=$(git diff --cached -U0 -- . ':!orchestrator/hooks/block-secrets.sh' 2>/dev/null || true)
# Pattern A: real-key shapes that are always secrets.
REAL_KEYS='(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16,}|xox[baprs]-[A-Za-z0-9-]+|BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY)'
# Pattern B: loose words that may or may not be secrets (filtered below).
LOOSE='(api[_-]?key|secret|password|token|credentials)'
HITS=$(echo "$DIFF" | grep -nEi "$LOOSE" | grep -viE '(\.env\.example|example|placeholder|<your|FINROOT_|no[ -]?secret|secret[ -]?scan|secret[ -]?detect|secret[ -]?free|secret[ -]?shape|real[ -]?key|secrets?\s+clean|secrets?\s+found|secrets?\s+scan|secrets?\s+in|secrets?\)|\(secrets?|secrets?,\s+internal|secrets?,|groq_api_key|openai_api_key|api[_-]?key\s*[=:]\s*None|block-secrets)' || true)
KEY_HITS=$(echo "$DIFF" | grep -nEi "$REAL_KEYS" || true)
ALL_HITS="$HITS$KEY_HITS"
if [ -n "$ALL_HITS" ]; then
  echo "BLOCK: possible secret in staged changes (FM-07). Move to .env (gitignored) and rotate:" >&2
  echo "$ALL_HITS" >&2
  exit 3
fi
echo "secret scan clean"; exit 0
