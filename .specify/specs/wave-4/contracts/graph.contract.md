# Core Agents & Orchestration — Interface Contract (Wave-4)

> Frozen before dispatch. Workers code to this; do not deviate without an orchestrator ADR.
> Depends on W2 (MemoryManager) and W3 (all 12 tools). AgentState from W1 schemas.

## 1. Intent Classifier + Context Assembly  (`src/finroot/agents/intent.py`, `src/finroot/workflows/context.py`)

```python
# intent.py
class IntentClassifier:
    """Classify user query into Intent enum + extract entities."""
    def classify(self, query: str) -> IntentResult: ...

class IntentResult(BaseModel):
    intent: Intent  # from finroot.schemas.enums
    confidence: float  # 0.0-1.0
    entities: dict[str, Any]  # {"symbols": [...], "timeframe": "...", ...}
    reasoning: str  # why this intent
```

```python
# context.py
class ContextAssembler:
    """Build the context dict for the planner from AgentState + MemoryManager."""
    def assemble(self, state: AgentState, memory: MemoryManager) -> dict[str, Any]: ...
    # Returns: {"query": ..., "twin": {...}, "relevant_history": [...], "intent": ..., "tools_available": [...]}
```

- Intent enum values: `PORTFOLIO_REVIEW`, `RISK_ASSESSMENT`, `TAX_PLANNING`, `MARKET_ANALYSIS`, `GENERAL_ADVICE`, `GREETING`
- Classification: keyword + pattern matching (no LLM needed for mock); LLM-backed for live mode.
- Context assembly pulls twin profile, last 5 working memory turns, and semantic recall.

## 2. Sub-Agents (5 ReAct agents)

Each sub-agent extends `BaseAgent` (from W1). Each has:
- `name: str` — unique identifier
- `tools: list[BaseTool]` — the tools this agent can use
- `run(state: AgentState) -> AgentState` — processes state, adds tool_outputs, returns updated state
- ReAct loop: think → act (call tool) → observe → repeat (max 3 iterations)
- Every tool call logged to audit trail via `BaseTool._audit_emit`

### MarketAnalystAgent  (`src/finroot/agents/market_agent.py`)
- Tools: MarketDataTool, FundamentalAnalysisTask
- On `MARKET_ANALYSIS` intent: fetch price data + fundamentals for extracted symbols
- Output: adds tool_outputs with price/fundamental data

### NewsInterpreterAgent  (`src/finroot/agents/news_agent.py`)
- Tools: NewsSearchTool, SentimentAnalysisTool
- Searches news for query terms, runs sentiment on articles
- Output: adds tool_outputs with news + sentiment scores

### RiskAssessorAgent  (`src/finroot/agents/risk_agent.py`)
- Tools: RiskCalculationTool, PortfolioSimulatorTool
- On `RISK_ASSESSMENT` intent: compute VaR/volatility, run Monte Carlo simulation
- Output: adds tool_outputs with risk metrics + simulation results

### PortfolioOptimizerAgent  (`src/finroot/agents/portfolio_agent.py`)
- Tools: MarketDataTool, RiskCalculationTool, PortfolioSimulatorTool
- On `PORTFOLIO_REVIEW` intent: fetch current prices, compute risk, simulate rebalancing
- Output: adds tool_outputs with allocation analysis

### TaxPlannerAgent  (`src/finroot/agents/tax_agent.py`)
- Tools: TaxRuleTool, UserProfileTool
- On `TAX_PLANNING` intent: compute tax implications, check user's tax bracket
- Output: adds tool_outputs with tax breakdown + rule citations

## 3. Plan-and-Execute Orchestrator  (`src/finroot/agents/orchestrator.py`, `src/finroot/workflows/graph.py`)

```python
# orchestrator.py
class FinRootOrchestrator:
    """Plan-and-Execute orchestrator using LangGraph."""
    def __init__(self, memory: MemoryManager, audit: AuditTrail) -> None: ...
    async def run(self, query: str) -> AgentState: ...
```

```python
# graph.py
def build_graph() -> CompiledStateGraph:
    """Build the LangGraph reasoning pipeline.
    
    Nodes: classify_intent → assemble_context → plan → execute_agents → synthesize → (critic in W5)
    Edges: conditional routing by intent to appropriate sub-agents
    """
    ...
```

- Plan step: based on intent, select which sub-agents to invoke (can be multiple in parallel)
- Execute step: invoke selected agents, collect tool_outputs
- Routing map:
  - `PORTFOLIO_REVIEW` → PortfolioOptimizer + RiskAssessor
  - `RISK_ASSESSMENT` → RiskAssessor
  - `TAX_PLANNING` → TaxPlanner
  - `MARKET_ANALYSIS` → MarketAnalyst + NewsInterpreter
  - `GENERAL_ADVICE` → MarketAnalyst + RiskAssessor
  - `GREETING` → (no agents, direct response)

## 4. Result Synthesizer  (`src/finroot/workflows/synthesize.py`)

```python
class ResultSynthesizer:
    """Combine all tool_outputs into a structured Recommendation."""
    def synthesize(self, state: AgentState) -> AgentState: ...
    # Sets state.candidate = Recommendation(...)
    # Includes citations from tool outputs, confidence from completeness
```

- Maps tool_outputs → Recommendation fields (evidence, risk_flags, citations)
- Confidence: HIGH if all expected tools returned, MEDIUM if some missing, LOW if few
- Every number in the recommendation must trace to a tool_output (FM-11)

## File map (disjoint write-sets)
| Task | Writes |
|------|--------|
| 01 | `src/finroot/agents/intent.py`, `src/finroot/workflows/context.py`, `tests/unit/test_intent.py` |
| 02 | `src/finroot/agents/market_agent.py`, `src/finroot/agents/news_agent.py`, `tests/unit/test_agents_market_news.py` |
| 03 | `src/finroot/agents/risk_agent.py`, `src/finroot/agents/portfolio_agent.py`, `tests/unit/test_agents_risk_portfolio.py` |
| 04 | `src/finroot/agents/tax_agent.py`, `tests/unit/test_agent_tax.py` |
| 05 | `src/finroot/agents/orchestrator.py`, `src/finroot/workflows/graph.py`, `tests/integration/test_orchestrator.py` |
| 06 | `src/finroot/workflows/synthesize.py`, `tests/unit/test_synthesize.py` |
