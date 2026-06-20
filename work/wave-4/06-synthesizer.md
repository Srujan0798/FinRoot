# Task wave-4/06 — Result Synthesizer

> Read `work/WORKER_PROMPT.md` then build. **Dispatch AFTER task 05 completes.**

## Objective
Implement `ResultSynthesizer` — the node that combines all sub-agent tool_outputs into a
structured `Recommendation` with citations, confidence labels, and risk flags.

## Writes (ONLY these)
- `src/finroot/workflows/synthesize.py`
- `tests/unit/test_synthesize.py`

## Forbid
All `src/finroot/agents/` files, `src/finroot/workflows/graph.py`, `context.py` (other tasks own those).

## Contract
Read `.specify/specs/wave-4/contracts/graph.contract.md` § Result Synthesizer.
Read `src/finroot/schemas/recommendation.py` for `Recommendation` model.
Read `src/finroot/schemas/state.py` for `AgentState`.

## Steps
1. `ResultSynthesizer`:
   - `synthesize(state: AgentState) -> AgentState`:
     - Collect all tool_outputs from state
     - Build `Recommendation`:
       - `answer`: summary text combining all findings
       - `evidence`: list of citations from tool outputs (each has source + data)
       - `risk_flags`: extract any risk warnings from tool_outputs
       - `confidence`: HIGH (all expected tools returned), MEDIUM (some), LOW (few)
       - `reasoning_steps`: list of "which agent did what"
     - Set `state.candidate = recommendation`
   - Confidence logic:
     - HIGH: ≥3 tool_outputs with citations, no errors
     - MEDIUM: 1-2 tool_outputs or some errors
     - LOW: 0 tool_outputs or all errors
   - Every number in `answer` must have a corresponding citation (FM-11)
   - If no tool_outputs: set `answer = "I don't have enough data to answer. Please provide more details."`, confidence=LOW

2. Tests (minimum 10):
   - Synthesize with 3 tool_outputs → HIGH confidence, citations present
   - Synthesize with 0 tool_outputs → LOW confidence, "don't have enough data"
   - Synthesize with error tool_outputs → MEDIUM/LOW, error noted
   - Risk flags extracted correctly
   - Reasoning steps populated
   - Recommendation round-trips through JSON

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_synthesize.py -v
ruff check src/finroot/workflows/synthesize.py
```

## Report
`work/reports/wave-4/06-synthesizer.report.md`
