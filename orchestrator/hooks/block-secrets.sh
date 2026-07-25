#!/usr/bin/env bash
# block-secrets: scan staged changes for secrets before commit (FM-07 publish gate).
# Blocks real key shapes always. Loose words (api_key/secret/password/token)
# only fire when not clearly documentation / code-identifier / test prose.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit

# Exclude this hook (self-references the filter words).
DIFF=$(git diff --cached -U0 -- . ':!orchestrator/hooks/block-secrets.sh' 2>/dev/null || true)

# Pattern A: real-key shapes that are always secrets.
REAL_KEYS='(sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16,}|xox[baprs]-[A-Za-z0-9-]+|BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY)'

# Pattern B: loose assignment-like secret introduction (high signal).
# e.g. password = "hunter2", api_key: sk-...
ASSIGN_SECRETS='(api[_-]?key|secret|password|token|credentials)\s*[=:]\s*["'\''][^"'\'']{8,}'

# Pattern C: loose words — filtered heavily for doc/code false positives.
LOOSE='(api[_-]?key|secret|password|token|credentials)'

ALLOW_LOOSE='(
  \.env\.example|example|placeholder|<your|FINROOT_|
  no[ -]?secret|secret[ -]?scan|secret[ -]?detect|secret[ -]?free|secret[ -]?shape|
  real[ -]?key|secrets?\s+clean|secrets?\s+found|secrets?\s+scan|secrets?\s+in|
  secrets?\)|\(secrets?|secrets?,\s+internal|secrets?,|
  groq_api_key|openai_api_key|api[_-]?key\s*[=:]\s*None|
  block-secrets|hard-fail secrets|Secrets.*no trade|test_security_secrets|block.secrets|
  \.gitignore|
  # code / test / LLM / grader false positives
  numeric\s+token|token[ -]?by[ -]?token|max_tokens|num_predict|
  _NUM_TOKEN|NUM_TOKEN|TOKEN_RE|token_re|
  parse_reasoning|must_not|rate\s+token|token\s+that|token\s+—|token\s+-|
  no_api_key|mock_no_api|without\s+api|api\s+keys?|
  credentials\s+in\s+sealed|legacy\s+contact|
  soft-fail|hard-fail|pip-audit|
  # FRB / tax prose
  exemption|LTCG|STCG|10%|15%|30%|
  # UI / docs
  not\s+financial|mock\s+mode|single-user
)'

HITS=$(echo "$DIFF" | grep -nEi "$LOOSE" | grep -viE "$(echo "$ALLOW_LOOSE" | tr -d '\n' | sed 's/  //g')" || true)
ASSIGN_HITS=$(echo "$DIFF" | grep -nEi "$ASSIGN_SECRETS" | grep -viE '(\.env\.example|example|placeholder|None|FINROOT_|mock|test_)' || true)
KEY_HITS=$(echo "$DIFF" | grep -nEi "$REAL_KEYS" || true)

ALL_HITS="${HITS}${ASSIGN_HITS}${KEY_HITS}"
if [ -n "$ALL_HITS" ]; then
  echo "BLOCK: possible secret in staged changes (FM-07). Move to .env (gitignored) and rotate:" >&2
  echo "$ALL_HITS" >&2
  exit 3
fi
echo "secret scan clean"; exit 0
