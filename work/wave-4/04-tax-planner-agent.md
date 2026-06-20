# Task wave-4/04 — TaxPlannerAgent

> Read `work/WORKER_PROMPT.md` then build. Parallel with tasks 01-03.

## Objective
Implement `TaxPlannerAgent` — the ReAct sub-agent for Indian tax planning. Uses TaxRuleTool
(deterministic) and UserProfileTool (reads DigitalTwin for tax bracket).

## Writes (ONLY these)
- `src/finroot/agents/tax_agent.py`
- `tests/unit/test_agent_tax.py`

## Forbid
All other `src/finroot/agents/` and `src/finroot/workflows/` files.

## Contract
Read `.specify/specs/wave-4/contracts/graph.contract.md` § Sub-Agents.
Read `src/finroot/agents/base.py` for `BaseAgent`.
Read `src/finroot/tools/tax.py`, `profile.py` for tool APIs.

## Steps
1. `TaxPlannerAgent(BaseAgent)`:
   - `name = "tax_planner"`
   - `tools = [TaxRuleTool(), UserProfileTool()]`
   - `run(state: AgentState) -> AgentState`:
     - Extract gain amount and type from context/query
     - Load user profile to get tax_bracket_pct
     - Call TaxRuleTool with gain, gain_type, annual_income
     - Add tax breakdown + rule citation to tool_outputs
     - If gain type unclear: add diagnostic tool_output asking for clarification
     - Max 2 ReAct iterations (profile → tax compute)

2. Tests (minimum 10):
   - TaxPlanner with LTCG gain → correct tax in tool_outputs
   - TaxPlanner with STCG gain → correct tax
   - TaxPlanner with missing gain info → diagnostic output
   - Audit trail entries
   - Agent name correct

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_agent_tax.py -v
ruff check src/finroot/agents/tax_agent.py
```

## Report
`work/reports/wave-4/04-tax-planner-agent.report.md`
