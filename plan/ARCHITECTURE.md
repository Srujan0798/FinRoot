# FinRoot — Architecture

> Living strategy doc #2 of 3. The "how". Pairs with `PRD.md` (what/why) and `EXECUTION.md`
> (when/status). Subsystem detail lives in `docs/architecture/`; ADRs in `docs/decisions/`.

## 1. Design principles
1. **Reasoning is a pipeline, not a prompt.** Decompose → evidence → scenario → risk → recommend
   → self-critique → verify → audit. Each stage is inspectable.
2. **Sovereign-first.** Local model + local data by default; cloud is opt-in, never required.
3. **Provider-agnostic at the edges.** LangChain/LangGraph core; LLM providers and data tools are
   swappable adapters (never a hard dependency).
4. **Numbers come from tools, never the model.** Every figure is tool-sourced and cited (FM-11).
5. **Everything is auditable.** Tamper-evident hash-chained log of every step.
6. **Typed boundaries.** Pydantic v2 everywhere data crosses a layer.

## 2. System overview
```
┌──────────────────────────────────────────────────────────────────────┐
│  INTERFACE         Streamlit (dark) · Typer CLI · FastAPI (optional)   │
└───────────────────────────────┬──────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  REASONING ORCHESTRATOR  (LangGraph state machine, Plan-and-Execute)   │
│    intent-classify → context-assemble → plan → execute → synthesize    │
│    → self-critique → rooted-prudence-verify → finalize → audit         │
└───────┬───────────┬───────────┬───────────┬───────────┬───────────────┘
        ▼           ▼           ▼           ▼           ▼
   ┌────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────┐
   │Market  │ │Risk     │ │Tax      │ │Portfolio │ │News       │   ReAct sub-agents
   │Analyst │ │Assessor │ │Planner  │ │Optimizer │ │Interpreter│   (tool-calling)
   └───┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘ └─────┬─────┘
       └───────────┴───────────┴───── TOOL ECOSYSTEM (12 tools) ────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  MEMORY (4-tier)   working · semantic(Chroma) · Digital-Twin(SQLite)   │
│                    · audit(hash-chained, append-only)                  │
└──────────────────────────────────────────────────────────────────────┘
```

## 3. Agent topology (LangGraph)
| Agent | Type | Responsibility |
|---|---|---|
| **Reasoning Orchestrator** | Plan-and-Execute (LangGraph supervisor) | Classify intent, assemble context, plan steps, route to sub-agents, synthesize, drive critique/verify. |
| **Market Analyst** | ReAct | Prices, history, technicals, fundamentals via market tools. |
| **Risk Assessor** | ReAct | VaR / Sharpe / beta / drawdown / stress tests. |
| **Tax Planner** | ReAct | Deterministic Indian tax engine; FY-end optimization. |
| **Portfolio Optimizer** | ReAct | Allocation, concentration, rebalancing, Monte-Carlo sim. |
| **News Interpreter** | ReAct | News retrieval, sentiment (FinBERT), impact + portfolio relevance. |
| **Self-Critic** | Custom chain | Scores the reasoning trace on 5 axes; triggers refinement. |
| **Rooted Prudence Verifier** | Custom chain | Enforces timeless wealth principles + safety guardrails. |
| **Audit Agent** | Deterministic | Emits the hash-chained trace record. |

LangGraph state object (`src/finroot/schemas/state.py`) carries: query, intent, digital-twin
snapshot, plan, per-step tool outputs, candidate answer, critique scores, verifier verdict,
final answer, confidence, citations, audit events.

## 4. Reasoning pipeline (the 35% weapon)
```
[1] Intent classify   → portfolio | risk | tax | news_impact | cashflow | credit | general
[2] Context assemble  → Digital Twin + relevant semantic memory + portfolio state
[3] Plan              → ordered steps: which sub-agents + params (Plan-and-Execute)
[4] Execute loop      → invoke sub-agents/tools; collect structured output; log each step
[5] Synthesize        → merge into a coherent candidate analysis
[6] Self-Critique     → score 5 axes (correctness, risk-awareness, actionability,
                        explainability, evidence); if below threshold → refine & re-run [5]-[6]
[7] Rooted-Prudence   → verify against principles + safety; may downgrade to "do not act yet"
[8] Finalize          → Summary + Analysis + Risks + Actions + Confidence + Citations
[9] Audit             → append hash-chained event record
```
Self-consistency option: generate N candidates → critic judges → best selected (configurable).

## 5. Memory architecture (4-tier)
| Tier | Implementation | Holds |
|---|---|---|
| **Working** | `ConversationBufferWindowMemory` (k≈20) | current conversation + active task context |
| **Semantic** | `VectorStoreRetrieverMemory` → ChromaDB (JSON fallback) | past analyses, rationales, financial concepts |
| **Digital Twin (structured)** | SQLite + Pydantic models | goals, risk tolerance, horizon, holdings, tax bracket, constraints |
| **Audit** | append-only hash-chained log (SQLite/JSONL) | every step, tool call, source, assumption, confidence, invalidation conditions |

Memory is a governed asset: reads/writes go through `src/finroot/memory/` interfaces, not ad hoc.

## 6. Tool ecosystem (12 tools — all with caching, rate-limit, graceful degradation, audit)
| Tool | Source | Output |
|---|---|---|
| MarketDataTool | yfinance / AlphaVantage | prices, OHLCV, technical indicators |
| FundamentalAnalysisTool | yfinance financials | P/E, EPS, debt ratios, growth |
| NewsSearchTool | NewsAPI / Serper | financial news items |
| SentimentAnalysisTool | FinBERT (local) | sentiment scores + evidence |
| RiskCalculationTool | numpy/scipy (custom) | VaR, Sharpe, beta, max drawdown |
| PortfolioSimulatorTool | numpy Monte-Carlo | scenario paths, percentiles |
| TaxRuleTool | `data/tax_rules.json` (deterministic) | LTCG/STCG, slabs, 80C, FY actions |
| MacroDataTool | public macro feeds | rates, inflation, indices |
| CurrencyConverterTool | FX feed | conversions (FX-aware reasoning) |
| UserProfileTool | Digital-Twin memory | read/update user state |
| DocumentParserTool | local parsers | statements/reports → structured |
| WatchlistAlertTool | local store | watchlist + threshold alerts |

Base tool (`src/finroot/tools/base.py`) standardizes: input/output Pydantic schema, TTL cache,
token-bucket rate limit, retry+backoff, loud-failure (no synthetic data), audit emit.

## 7. LLM provider abstraction
`src/finroot/llm/` exposes a single `LLMProvider` interface with adapters:
- **Mock** (deterministic, offline — CI + judging),
- **Ollama** (local sovereign default, e.g. `llama3.1:8b`),
- **Groq** / **OpenAI** (opt-in cloud, key-gated).
Cost-aware routing: cheap/local models for read-heavy/bulk steps; stronger model for synthesis +
critique (see `orchestrator/core/` routing notes). Each call extracts `<reasoning>` + `<confidence>`.

## 8. Sovereignty & trust layer
- Local model + local data; offline Mock mode; no telemetry by default.
- Citation requirement, confidence labeling, unsupported-claim rejection, unsafe-advice guardrails,
  "insufficient evidence" outputs, full trace export.
- r5 actions (move money) are **blocked**; FinRoot is decision-support only.

## 9. Evaluation architecture (proves the 35%)
`evals/` runs the **Financial Reasoning Benchmark (FRB)**: domain-spread questions, graded by
code-based asserts + LLM-judge rubric + periodic human review, across trials (pass@k / pass^k),
comparing baseline RAG → single-agent → full FinRoot. Outputs → `evals/reports/` + `results/metrics.json`.

## 10. Tech stack
Python 3.11 · LangChain + LangGraph · Pydantic v2 · ChromaDB + SQLite (+ JSON fallback) ·
Streamlit + Typer (+ FastAPI optional) · Ollama/Groq/OpenAI/Mock · Docker + compose · pytest · ruff.

## 11. Module → wave map (who builds what, when)
| Module | Wave |
|---|---|
| `llm/`, `schemas/`, `audit/` backbone, `config/` | W1 Foundation |
| `memory/` (4-tier) + Digital Twin | W2 |
| `tools/` (12) | W3 |
| `agents/` + `workflows/` (LangGraph orchestrator + sub-agents) | W4 |
| `reasoning/` (Self-Critic, Rooted Prudence, self-consistency) | W5 |
| `evaluation/` + `evals/` FRB harness | W6 |
| `interface/ui`, `interface/cli` | W7 |
| Docker, docs, submission package | W8 |

Detailed acceptance contracts per wave: `.specify/specs/wave-N/contracts/`.
