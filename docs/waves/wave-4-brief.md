# Wave 4 — Core Agents & Orchestration

**Goal:** the LangGraph Plan-and-Execute orchestrator + 5 ReAct sub-agents, wired to the tools (W3)
and memory (W2). This is where the agent first *reasons end-to-end*. **Depends on W2 + W3.**

## Tasks (6)
| # | Task | Suggested agent role | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | Intent classifier + context assembly | NLP | `src/finroot/agents/intent.py`, `src/finroot/workflows/context.py` | W2 |
| 02 | Market Analyst + News Interpreter sub-agents | agent eng | `src/finroot/agents/market_agent.py`, `agents/news_agent.py` | W3 |
| 03 | Risk Assessor + Portfolio Optimizer sub-agents | agent eng | `src/finroot/agents/risk_agent.py`, `agents/portfolio_agent.py` | W3 |
| 04 | Tax Planner sub-agent | agent eng | `src/finroot/agents/tax_agent.py` | W3 |
| 05 | Plan-and-Execute orchestrator (LangGraph) | architecture | `src/finroot/agents/orchestrator.py`, `src/finroot/workflows/graph.py` | 01-04 |
| 06 | Result synthesizer | reasoning | `src/finroot/workflows/synthesize.py` | 05 |

## Contracts to freeze first
`graph.contract.md` — the LangGraph node interface, `AgentState` transitions (from W1 state
contract), sub-agent input/output schema, routing-by-intent map.

## Acceptance
```bash
pytest tests/integration -k "graph or orchestrator or agents" -v
python -m src.interface.cli --mock "Review my 70/30 portfolio for FY-end rebalancing"
# expect: a structured Recommendation with plan → tool calls → synthesis, all in the audit trail
```
Every sub-agent step logs to the audit trail; every number traces to a tool call (FM-11).

## Scoring relevance
**Agent Architecture (30%) — the centerpiece.** Effective LangChain/LangGraph agents, chains, tools,
memory, multi-step workflow. Also sets up Reasoning (35%).
