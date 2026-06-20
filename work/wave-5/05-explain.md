# Task wave-5/05 — Explainability Assembly

> Read `work/WORKER_PROMPT.md` then build. **Dispatch AFTER tasks 01+03 complete.**

## Objective
Implement `ExplainabilityAssembly` — builds the human-readable reasoning trace that the UI
displays. This is what makes FinRoot's reasoning transparent and auditable.

## Writes (ONLY these)
- `src/finroot/reasoning/explain.py`
- `tests/unit/test_explain.py`

## Forbid
All other `src/finroot/reasoning/` files.

## Contract
Read `.specify/specs/wave-5/contracts/reasoning.contract.md` § Explainability Assembly.
Read `src/finroot/reasoning/critic.py` for `CriticVerdict` (task 01).
Read `src/finroot/reasoning/principles.py` for `PrudentialVerdict` (task 03).

## Steps
1. `ExplainabilityAssembly`:
   - `assemble(state: AgentState) -> dict`:
     - Extract reasoning steps from `state.audit_events` → `reasoning_chain`
     - Extract citations from `state.tool_outputs` → `citations`
     - Map critic scores to confidence label: overall >= 0.7 → HIGH, 0.4-0.7 → MEDIUM, < 0.4 → LOW
     - Include `principles_check` from state (if available)
     - Build `risk_summary` from tool_outputs that mention risk
     - Return dict with all fields per contract

2. Tests (minimum 10):
   - Full state with audit events → reasoning_chain populated
   - Empty audit events → empty reasoning_chain, not error
   - Citations extracted from tool_outputs correctly
   - Confidence label mapping correct for each threshold
   - Risk summary extracted from risk-related tool_outputs
   - Missing principles_check → default "not checked"

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_explain.py -v
ruff check src/finroot/reasoning/explain.py
```

## Report
`work/reports/wave-5/05-explain.report.md`
