# Task wave-5/01 — Self-Critic (5-axis scoring)

> Read `work/WORKER_PROMPT.md` then build. Parallel with tasks 03, 04.

## Objective
Implement `SelfCritic` — the 5-axis reasoning quality scorer that evaluates whether a recommendation
is safe to ship. This is the gate that catches bad advice before it reaches the user.

## Writes (ONLY these)
- `src/finroot/reasoning/critic.py`
- `tests/unit/test_critic.py`

## Forbid
All other `src/finroot/reasoning/` files.

## Contract
Read `.specify/specs/wave-5/contracts/reasoning.contract.md` § Self-Critic.
Read `src/finroot/schemas/state.py` for `AgentState`.
Read `src/finroot/schemas/recommendation.py` for `Recommendation`.

## Steps
1. `SelfCritic` class:
   - `THRESHOLD = 0.6`, `WEIGHTS` per contract
   - `evaluate(state: AgentState) -> CriticVerdict`:
     - Score each axis 0.0-1.0 with rationale
     - **Correctness**: check if numbers in `candidate.answer` match tool_outputs (no hallucination)
     - **Risk-awareness**: check if answer mentions risks, warns about downsides
     - **Actionability**: check if advice is specific (has what/when/how)
     - **Explainability**: check if reasoning chain is present and clear
     - **Evidence**: check if claims have citations from tool_outputs
     - `overall = sum(weight * score for axis, weight in WEIGHTS)`
     - `passed = overall >= THRESHOLD`
     - `must_fix` = list of issues where score < 0.5

2. Tests (minimum 18):
   - Good recommendation (all 5 axes present) → passed=True, overall > 0.7
   - Bad recommendation ("buy RELIANCE" with no reasoning) → passed=False
   - Risky recommendation (no risk warnings) → risk_awareness < 0.4
   - Hallucinated numbers (answer has numbers not in tool_outputs) → correctness < 0.4
   - Missing citations → evidence < 0.4
   - Threshold boundary: overall=0.59 → passed=False, overall=0.60 → passed=True
   - must_fix populated when axis < 0.5
   - All weights sum to 1.0

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_critic.py -v
ruff check src/finroot/reasoning/critic.py
```

## Report
`work/reports/wave-5/01-critic.report.md`
