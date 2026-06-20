# Task wave-4/02 — MarketAnalystAgent + NewsInterpreterAgent

> Read `work/WORKER_PROMPT.md` then build. Parallel with tasks 01, 03, 04.

## Objective
Implement two ReAct sub-agents: `MarketAnalystAgent` (price + fundamentals) and
`NewsInterpreterAgent` (news search + sentiment). Both extend `BaseAgent` from W1.

## Writes (ONLY these)
- `src/finroot/agents/market_agent.py`
- `src/finroot/agents/news_agent.py`
- `tests/unit/test_agents_market_news.py`

## Forbid
All other `src/finroot/agents/` and `src/finroot/workflows/` files.

## Contract
Read `.specify/specs/wave-4/contracts/graph.contract.md` § Sub-Agents.
Read `src/finroot/agents/base.py` for `BaseAgent` interface.
Read `src/finroot/tools/market.py`, `fundamentals.py`, `news.py`, `sentiment.py` for tool APIs.

## Steps
1. `MarketAnalystAgent(BaseAgent)`:
   - `name = "market_analyst"`
   - `tools = [MarketDataTool(), FundamentalAnalysisTool()]`
   - `run(state: AgentState) -> AgentState`:
     - Extract symbols from `state.tool_outputs` or from context (assembled by intent classifier)
     - Call MarketDataTool for each symbol → add to tool_outputs
     - Call FundamentalAnalysisTool for each symbol → add to tool_outputs
     - Max 3 ReAct iterations (think → act → observe)
     - Every tool call emits audit event (inherited from BaseTool)
   - Returns updated state with new tool_outputs appended

2. `NewsInterpreterAgent(BaseAgent)`:
   - `name = "news_interpreter"`
   - `tools = [NewsSearchTool(), SentimentAnalysisTool()]`
   - `run(state: AgentState) -> AgentState`:
     - Search news for query terms
     - Run sentiment on article summaries
     - Add news + sentiment results to tool_outputs

3. Tests (minimum 12):
   - MarketAnalyst with mock tools returns price + fundamental data in tool_outputs
   - NewsInterpreter with mock tools returns news + sentiment in tool_outputs
   - Empty symbols list → no tool calls, state unchanged
   - Audit trail has entries after agent runs
   - Agent name correct

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_agents_market_news.py -v
ruff check src/finroot/agents/market_agent.py src/finroot/agents/news_agent.py
```

## Report
`work/reports/wave-4/02-market-news-agents.report.md`
