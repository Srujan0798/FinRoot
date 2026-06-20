# Wave-1 Spec — Foundation

> Spec-driven dev (Spec-Kit). This wave builds the bedrock every later wave imports. No agent
> reasoning yet — just the typed, sovereign, auditable substrate.

## Goal
A runnable, typed, tested foundation: a pluggable LLM provider layer, the core Pydantic schemas +
LangGraph state object, the hash-chained audit backbone, config/settings, base Tool/Agent
interfaces, and green CI — all working in **Mock mode with zero external keys**.

## Why first
Waves 2–8 import these modules. Foundation collisions are the most expensive (FM-13), so the
shared substrate is built once, cleanly, before parallel work fans out.

## In scope
- LLM provider abstraction: `Mock`, `Ollama`, `Groq`, `OpenAI` adapters behind one interface.
- Core schemas: query, intent, recommendation, citation, confidence, audit event; LangGraph `AgentState`.
- Audit backbone: append-only, hash-chained event log with verify + replay.
- Config/settings loader (env + defaults), prompt registry.
- Base classes: `BaseTool` (cache/rate-limit/retry/loud-fail/audit hooks), `BaseAgent`.
- Project bootstrap: package layout, `__init__` exports, smoke test, CI green.

## Out of scope (later waves)
- Real memory tiers (W2), real tools (W3), real agents/graph (W4), critic (W5), evals (W6), UI (W7).
- Any live API calls beyond a keyless smoke check.

## Acceptance criteria (orchestrator runs these before approving — FM-09)
```bash
# 1. installs clean
pip install -r requirements.txt
# 2. lint clean
ruff check src/
# 3. smoke test: Mock provider answers, audit chain verifies, state round-trips
python scripts/smoke_test.py            # exit 0, prints "FOUNDATION OK"
# 4. unit tests for wave-1 pass
pytest tests/unit -k "wave1 or provider or audit or schema or config" -v
# 5. audit chain tamper-evidence holds
pytest tests/unit/test_audit_chain.py -v
# 6. CI workflow runs the above
```
**Done = all six pass with output captured in the task reports.**

## Success signals
- `from finroot.llm import get_provider; get_provider("mock")` works offline.
- `AgentState` serializes/deserializes losslessly (Pydantic).
- Tampering with one audit event breaks chain verification (test proves it).
- `scripts/smoke_test.py` runs end-to-end in < 2s with no keys.

## Risks for this wave
- Over-building the base classes → keep interfaces minimal; YAGNI beyond what W2–W5 need.
- Provider import errors when optional deps missing → lazy imports; Mock never needs extras.
