# Task wave-10/02 — Improve Agent Pipeline for Higher pass@1

> Read `work/WORKER_PROMPT.md` then build. Directly boosts the 35% reasoning score.

## Objective
Improve the agent pipeline so more FRB tasks pass on first try. Current pass@1 is 0.346.
Target: 0.50+. Key failure modes: missing keywords, insufficient citations, wrong confidence.

## Writes (ONLY these)
- `src/finroot/workflows/synthesize.py` (improve synthesis to include more keywords + citations)
- `src/finroot/agents/orchestrator.py` (improve plan execution to produce better tool outputs)

## Forbid
`evals/**`, `data/gold/**`, `src/finroot/reasoning/**` (other tasks).

## Steps
1. Read `evals/graders/code_based.py` to understand what the grader checks:
   - must_mention: keywords in summary + analysis (case-insensitive)
   - min_citations: count of citations on final recommendation
   - confidence: must match expected
   - actionability: actions list non-empty
   - length: analysis >= 100 chars
2. Read `src/finroot/workflows/synthesize.py` — understand how the final Recommendation is built.
3. Read `src/finroot/agents/orchestrator.py` — understand how tool outputs are collected.
4. Improve synthesize.py:
   - Ensure the synthesis prompt includes the query keywords in the summary
   - Ensure citations from tool_outputs are properly attached to the Recommendation
   - Ensure actions list is populated with specific steps
   - Ensure analysis is substantive (>= 100 chars)
   - Ensure confidence is set based on evidence quality
5. Improve orchestrator.py:
   - Ensure all tool outputs are collected and passed to synthesis
   - Ensure the twin snapshot is properly injected into agent state
   - Ensure the plan includes all relevant agents for the query domain
6. Do NOT change the grader or the FRB questions — only improve the pipeline.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_synthesize.py tests/integration/test_orchestrator.py -v
PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1 2>&1 | tail -5
ruff check src/finroot/workflows/synthesize.py src/finroot/agents/orchestrator.py
```
Target: pass@1 >= 0.50 (from 0.346).

## Report
`work/reports/wave-10/02-improve-passat1.report.md`
