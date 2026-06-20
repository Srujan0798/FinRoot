# Task wave-4/05 — Plan-and-Execute Orchestrator (LangGraph)

> Read `work/WORKER_PROMPT.md` then build. **Dispatch AFTER tasks 01-04 complete.**

## Objective
Implement `FinRootOrchestrator` and the LangGraph state graph — the central reasoning pipeline
that routes queries through intent → context → plan → execute → synthesize.

## Writes (ONLY these)
- `src/finroot/agents/orchestrator.py`
- `src/finroot/workflows/graph.py`
- `tests/integration/test_orchestrator.py`

## Forbid
`src/finroot/agents/intent.py`, `market_agent.py`, `news_agent.py`, `risk_agent.py`, `portfolio_agent.py`, `tax_agent.py`, `workflows/context.py`, `workflows/synthesize.py` (other tasks own those).

## Contract
Read `.specify/specs/wave-4/contracts/graph.contract.md` § Plan-and-Execute Orchestrator.
Read `src/finroot/schemas/state.py` for `AgentState` fields.

## Steps
1. `build_graph() -> CompiledStateGraph` in `graph.py`:
   - Nodes: `classify_intent`, `assemble_context`, `plan`, `execute_agents`, `synthesize`
   - State: use `AgentState` (from schemas) — add `context: dict`, `selected_agents: list[str]` as needed
   - `classify_intent` → `IntentClassifier.classify()` → sets `state.intent`
   - `assemble_context` → `ContextAssembler.assemble()` → sets `state.context`
   - `plan` → based on intent, select sub-agents (routing map from contract)
   - `execute_agents` → invoke selected agents in sequence (or parallel if LangGraph supports), collect tool_outputs
   - `synthesize` → `ResultSynthesizer.synthesize()` → sets `state.candidate`
   - Conditional edges: route by intent to appropriate agent execution paths

2. `FinRootOrchestrator` in `orchestrator.py`:
   - `__init__(memory, audit)` — instantiates all agents, builds graph
   - `run(query: str) -> AgentState`:
     - Create initial state with query
     - Run graph
     - Append all audit events to trail
     - Return final state

3. Integration tests (minimum 8):
   - Full pipeline: "Review my portfolio" → PORTFOLIO_REVIEW → PortfolioOptimizer + RiskAssessor → synthesis
   - Full pipeline: "What's the tax on 2L LTCG?" → TAX_PLANNING → TaxPlanner → synthesis
   - Full pipeline: "What's RELIANCE price?" → MARKET_ANALYSIS → MarketAnalyst + NewsInterpreter → synthesis
   - GREETING intent → no agents, direct response
   - Audit trail has entries for each step
   - State round-trip through graph is valid

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/integration/test_orchestrator.py -v
ruff check src/finroot/agents/orchestrator.py src/finroot/workflows/graph.py
```

## Report
`work/reports/wave-4/05-orchestrator.report.md`
