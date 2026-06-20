# Task wave-8/03 — Architecture Decision Records (ADRs)

> Read `work/WORKER_PROMPT.md` then build. Pure docs; depends on the built system (waves 1-5).

## Objective
Write 6 Architecture Decision Records (MADR format) documenting the key design decisions, so judges
see deliberate engineering reasoning (Code Implementation 20% + Architecture 30%).

## Writes (ONLY these)
- `docs/decisions/0003-langgraph-plan-and-execute.md`
- `docs/decisions/0004-four-tier-memory-and-digital-twin.md`
- `docs/decisions/0005-five-axis-self-critic.md`
- `docs/decisions/0006-sovereign-first-mock-default.md`
- `docs/decisions/0007-hash-chained-audit-trail.md`
- `docs/decisions/0008-deterministic-tax-engine.md`

## Forbid
All other files. (If `docs/decisions/0001-*` / `0002-*` exist, do not modify them.)

## Context (read these to ground the ADRs in the real code)
- `src/finroot/agents/orchestrator.py`, `src/finroot/workflows/graph.py` (LangGraph)
- `src/finroot/memory/` (4-tier memory + DigitalTwin)
- `src/finroot/reasoning/` (critic, principles, consistency)
- `src/finroot/audit/trail.py` (hash chain)
- `src/finroot/tools/tax.py` (deterministic engine)
- `CLAUDE.md` (scoring weights, non-negotiables)

## Steps
Each ADR (MADR format): Title · Status (Accepted) · Context · Decision · Consequences (positive + negative + neutral) · Alternatives considered.
1. **0003** LangGraph Plan-and-Execute: why a stateful graph + plan/execute/synthesize over a single chain; how it maps to Agent Architecture 30%.
2. **0004** 4-tier memory + Digital Twin: working/semantic/structured/audit; why the twin is the personalization moat (Idea 15%).
3. **0005** 5-axis Self-Critic: correctness/risk/actionability/explainability/evidence; why this is the 35% weapon; the threshold + refinement loop.
4. **0006** Sovereign-first / Mock default: local Ollama preference, offline judging, no blind cloud reliance; the privacy/sovereignty story.
5. **0007** Hash-chained audit trail: tamper-evidence, replayability, why finance needs it.
6. **0008** Deterministic tax engine: why rule-based not LLM for numbers; FM-11 (no fabricated financial data) + reproducibility.

Keep each ADR tight (200-400 words), concrete, referencing real modules/paths.

## Acceptance
```bash
ls docs/decisions/000[3-8]-*.md | wc -l   # expect 6
for f in docs/decisions/000[3-8]-*.md; do grep -q "## Decision" "$f" && grep -q "## Consequences" "$f" && echo "$f OK" || echo "$f MISSING SECTIONS"; done
```

## Report
`work/reports/wave-8/03-adrs.report.md`
