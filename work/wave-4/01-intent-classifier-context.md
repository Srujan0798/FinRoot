# Task wave-4/01 — Intent Classifier + Context Assembly

> Read `work/WORKER_PROMPT.md` then build. Parallel with tasks 02-04.

## Objective
Implement `IntentClassifier` (classify user queries into Intent enum) and `ContextAssembler`
(build the reasoning context from AgentState + MemoryManager). These are the entry nodes of
the LangGraph pipeline.

## Writes (ONLY these)
- `src/finroot/agents/intent.py`
- `src/finroot/workflows/context.py`
- `tests/unit/test_intent.py`

## Forbid
All other `src/finroot/agents/` and `src/finroot/workflows/` files.

## Contract
Read `.specify/specs/wave-4/contracts/graph.contract.md` § Intent Classifier + Context Assembly.
Read `src/finroot/schemas/enums.py` for `Intent` enum values.
Read `src/finroot/memory/manager.py` for `MemoryManager` API.

## Steps
1. `IntentClassifier`:
   - `classify(query: str) -> IntentResult`
   - Keyword/pattern matching (deterministic in mock mode):
     - "portfolio", "allocation", "holdings", "rebalance" → PORTFOLIO_REVIEW
     - "risk", "var", "volatility", "drawdown" → RISK_ASSESSMENT
     - "tax", "capital gains", "ltcg", "stcg" → TAX_PLANNING
     - "price", "market", "stock", "fundamental" → MARKET_ANALYSIS
     - "hello", "hi", "help" → GREETING
     - default → GENERAL_ADVICE
   - Entity extraction: regex for NSE/BSE tickers (e.g., "RELIANCE.NS", "INFY"), timeframes ("1 year", "6 months")
   - Confidence: 1.0 for exact keyword match, 0.7 for partial, 0.5 for default

2. `ContextAssembler`:
   - `assemble(state: AgentState, memory: MemoryManager) -> dict`
   - Pulls: twin profile via `memory.get_twin()`, last 5 working memory turns, semantic recall for query
   - Returns dict with: query, twin_snapshot, relevant_history, intent, tools_available (tool names list)
   - Handles missing twin gracefully (empty twin dict, not error)

3. Tests (minimum 15):
   - Each intent classification with keyword match
   - Entity extraction (symbols, timeframes)
   - Default → GENERAL_ADVICE for ambiguous queries
   - Context assembly with mock memory
   - Context handles missing twin (KeyError caught, empty dict)
   - Confidence values correct

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_intent.py -v
ruff check src/finroot/agents/intent.py src/finroot/workflows/context.py
```

## Report
`work/reports/wave-4/01-intent-classifier.report.md`
