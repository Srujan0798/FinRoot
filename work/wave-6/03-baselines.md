# Task wave-6/03 — Baselines (Naive RAG + Single-Agent) for comparison

> Read `work/WORKER_PROMPT.md` then build. Depends on W4 (done). The "what we beat".

## Objective
Two deliberately weaker baseline systems that produce AgentState-compatible answers so the same
graders measure the lift of the full FinRoot pipeline over them.

## Writes (ONLY these)
- `src/finroot/evaluation/baselines.py`
- `tests/unit/test_baselines.py`

## Forbid
`src/finroot/evaluation/harness.py`, `report.py`, `evals/**`, `data/gold/**` (other tasks).

## Contract
Read `.specify/specs/wave-6/contracts/evals.contract.md` § Baselines. AgentState from `finroot.schemas`.

## Steps
1. `NaiveRAGBaseline`:
   - `answer(query, twin=None) -> AgentState`: one LLM call (MockProvider) with retrieved context but NO agents, NO critic, NO principles. Produces a `Recommendation` with weak/absent citations and no risk framing — represents a typical RAG chatbot.
   - Deterministic in mock.
2. `SingleAgentBaseline`:
   - `answer(query, twin=None) -> AgentState`: a single ReAct-style agent that may call one tool, but no multi-agent orchestration, no self-critic, no consistency. Better than RAG, worse than full FinRoot.
3. Both populate `state.final` (Recommendation) and `state.plan` so graders work uniformly.
4. Keep them HONESTLY weaker — do NOT sandbag artificially, but do NOT give them the critic/principles (that's the whole point of the comparison). Document this in docstrings.
5. `tests/unit/test_baselines.py` (min 8): each baseline returns AgentState with a final Recommendation; RAG has fewer/no citations vs a typical FinRoot answer; deterministic in mock; handles twin=None.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_baselines.py -v
ruff check src/finroot/evaluation/baselines.py
```

## Report
`work/reports/wave-6/03-baselines.report.md`
