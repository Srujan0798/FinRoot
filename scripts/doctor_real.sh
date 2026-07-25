#!/usr/bin/env bash
# doctor_real: verify FinRoot works with a REAL LLM (not mock).
# Requires either Ollama running locally, or GROQ_API_KEY set.
set -uo pipefail
cd "$(dirname "$0")/.." || exit
export PYTHONPATH=src

FAILED=0

echo "=== FinRoot Reality Check ==="
echo

# Check 1: Is a real LLM available?
OLLAMA_OK=false
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('models',[])))" 2>/dev/null || echo "0")
  if [ "$MODELS" -gt 0 ]; then
    OLLAMA_OK=true
    echo "  Ollama: running with $MODELS model(s) ... OK"
  else
    echo "  Ollama: running but no models ... SKIP"
  fi
else
  echo "  Ollama: not running ... SKIP"
fi

GROQ_OK=false
if [ -n "${GROQ_API_KEY:-}" ]; then
  GROQ_OK=true
  echo "  Groq: GROQ_API_KEY set ... OK"
else
  echo "  Groq: no GROQ_API_KEY ... SKIP"
fi

if [ "$OLLAMA_OK" = false ] && [ "$GROQ_OK" = false ]; then
  echo
  echo "  No real LLM available. Set GROQ_API_KEY or start Ollama with a model."
  echo "  To install tinyllama: ollama pull tinyllama"
  echo
  exit 0
fi

# Check 2: Direct LLM call
echo
echo "  Testing direct LLM call ..."
if [ "$OLLAMA_OK" = true ]; then
  PROVIDER="ollama"
else
  PROVIDER="groq"
fi

RESULT=$(FINROOT_LLM_PROVIDER=$PROVIDER python3 -c "
from finroot.llm.factory import get_provider
p = get_provider('$PROVIDER')
r = p.complete('What is 2+2? Reply with just the number.')
print(r.provider, '|', r.model, '|', r.text[:100])
" 2>&1)

if [ $? -eq 0 ] && [ -n "$RESULT" ]; then
  echo "  Direct LLM call ($PROVIDER): $RESULT ... OK"
else
  echo "  Direct LLM call ($PROVIDER): FAILED"
  echo "  Error: $RESULT"
  FAILED=$((FAILED+1))
fi

# Check 3: Intent classification with real LLM
echo
echo "  Testing intent classification ..."
RESULT=$(FINROOT_LLM_PROVIDER=$PROVIDER python3 -c "
from finroot.agents.intent import IntentClassifier
ic = IntentClassifier()
r = ic.classify('Should I invest in LTCG or STCG?')
print(f'intent={r.intent.value} confidence={r.confidence}')
" 2>&1)

if echo "$RESULT" | grep -q "intent="; then
  echo "  Intent classification: $RESULT ... OK"
else
  echo "  Intent classification: FAILED"
  echo "  $RESULT"
  FAILED=$((FAILED+1))
fi

# Check 4: Full agent workflow with real LLM
echo
echo "  Testing full agent workflow ..."
RESULT=$(FINROOT_LLM_PROVIDER=$PROVIDER python3 -c "
from interface.core import answer
state = answer('What is compound interest?', mock=False)
rec = getattr(state, 'final', None) or getattr(state, 'candidate', None)
if rec:
    summary = getattr(rec, 'summary', '')[:200]
    confidence = getattr(rec, 'confidence', 'unknown')
    citations = len(getattr(rec, 'citations', []) or [])
    intent = getattr(state, 'intent', None)
    print(f'intent={intent} confidence={confidence} citations={citations}')
    print(f'summary={summary}')
else:
    print('ERROR: No recommendation')
" 2>&1)

if echo "$RESULT" | grep -q "intent="; then
  echo "  Full workflow: ... OK"
  echo "  $RESULT" | sed 's/^/    /'
else
  echo "  Full workflow: FAILED"
  echo "  $RESULT" | tail -3 | sed 's/^/    /'
  FAILED=$((FAILED+1))
fi

# Check 5: Tool imports work with real LLM environment
echo
echo "  Testing tool imports ..."
RESULT=$(FINROOT_LLM_PROVIDER=$PROVIDER python3 -c "
from finroot.tools.market import MarketDataTool
from finroot.tools.profile import UserProfileTool
from finroot.tools.tax import TaxRuleTool
from finroot.tools.risk import RiskCalculationTool
from finroot.tools.documents import DocumentParserTool
print('all_tools_imported=ok')
" 2>&1)

if echo "$RESULT" | grep -q "all_tools_imported"; then
  echo "  Tool imports: $RESULT ... OK"
else
  echo "  Tool imports: FAILED"
  echo "  $RESULT"
  FAILED=$((FAILED+1))
fi

echo
if [ "$FAILED" -gt 0 ]; then
  echo "FAILED: $FAILED check(s) failed"
  exit 1
fi
echo "All reality checks passed."
