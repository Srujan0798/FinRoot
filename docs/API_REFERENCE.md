# FinRoot API Reference

Comprehensive reference for all FinRoot interfaces: CLI, REST API, configuration, tools, memory, and evaluation.

---

## CLI Usage

The CLI is a Typer application with the following flags and subcommands.

### Global Flags

| Flag | Default | Description |
|---|---|---|
| `--mock` / `--no-mock` | `--mock` | Use offline mock provider (no API keys needed) |
| `--user` / `-u` | `demo` | User ID for memory/twin lookup |
| `--help` | — | Show help message and exit |
| `--version` | — | Show version and exit |

### Usage

```bash
# Direct query
finroot [--mock|--no-mock] [--user ID] "Your financial question"

# Explicit ask subcommand
finroot ask [--mock|--no-mock] [--user ID] "Your financial question"

# Via Makefile
make cli ARGS="--mock 'What is compound interest?'"
make cli ARGS="--no-mock --user alice 'Should I rebalance my portfolio?'"
```

### Output

The CLI renders:
- **Answer panel** — summary + detailed analysis
- **Confidence** — high / medium / low / insufficient (color-coded)
- **Risks** — flagged risks from the prudence verifier
- **Reasoning Steps** — step-by-step plan with node, action, and detail
- **Citations** — sourced evidence with detail and value
- **Critic Verdict** — PASSED/FAILED with 5-axis overall score

---

## API Endpoints

Start the API server:
```bash
PYTHONPATH=src uvicorn interface.api.app:app --port 8000
```

### `GET /health`

Basic health check.

**Response** (`HealthResponse`):
```json
{
  "status": "ok",
  "version": "0.1.0",
  "test_count": 42
}
```

### `POST /query`

Run the full FinRoot reasoning pipeline.

**Request** (`QueryRequest`):
| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Financial question (min 1 char) |
| `user_id` | string | no | `"demo"` | Stable user identifier |
| `mock` | boolean | no | `true` | Use offline mock LLM provider |

**Response** (`QueryResponse`):
| Field | Type | Description |
|---|---|---|
| `summary` | string | Concise answer summary |
| `confidence` | string | `high` / `medium` / `low` / `insufficient` |
| `risk_band` | string | Risk classification from verifier |
| `citations` | array[dict] | Sourced evidence objects |
| `reasoning_trace` | array[dict] | Step-by-step reasoning trace |
| `audit_events` | array[dict] | Hash-chained audit trail events |

### `GET /metrics`

Return FRB benchmark metrics from `results/metrics.json`.

**Response**: The contents of `results/metrics.json`, or an error object if unavailable.

---

## Configuration

All settings are loaded via `pydantic-settings` with the `FINROOT_` environment variable prefix.

| Variable | Type | Default | Description |
|---|---|---|---|
| `FINROOT_LLM_PROVIDER` | `str` | `"mock"` | LLM provider: `mock`, `ollama`, `groq`, or `openai` |
| `FINROOT_OLLAMA_BASE_URL` | `str` | `http://localhost:11434` | Ollama server URL |
| `FINROOT_OLLAMA_MODEL` | `str` | `llama3.1:8b` | Ollama model name |
| `FINROOT_GROQ_API_KEY` | `str \| None` | `None` | Groq API key |
| `FINROOT_OPENAI_API_KEY` | `str \| None` | `None` | OpenAI API key |
| `FINROOT_CHROMA_DIR` | `str` | `data/chroma` | ChromaDB persist directory |
| `FINROOT_DIGITAL_TWIN_DB` | `str` | `data/digital_twin.db` | SQLite path for Digital Twin |
| `FINROOT_AUDIT_PATH` | `str` | `logs/audit.jsonl` | Audit trail log path |
| `FINROOT_NEWSAPI_KEY` | `str \| None` | `None` | NewsAPI key (live news only) |
| `FINROOT_SENTIMENT_MODEL` | `str` | `""` | Set to `"finbert"` for FinBERT sentiment |

### Provider Modes

- **`mock`** — fully offline, deterministic, no API keys. Default for CI/judging.
- **`ollama`** — local inference via Ollama. Set `FINROOT_OLLAMA_BASE_URL` if not localhost.
- **`groq`** — cloud inference via Groq. Requires `FINROOT_GROQ_API_KEY`.
- **`openai`** — cloud inference via OpenAI. Requires `FINROOT_OPENAI_API_KEY`.

---

## Tools

All tools extend `BaseTool[In, Out]` and provide TTL caching, token-bucket rate limiting, retry with exponential backoff, and audit-trail emission.

| Tool Class | `name` | Description |
|---|---|---|
| `MarketDataTool` | `market_data` | Live OHLCV price data via yfinance (mock: deterministic hash-based prices) |
| `FundamentalAnalysisTool` | `fundamental_analysis` | Fundamental ratios (P/E, P/B, EPS, dividend yield, market cap, D/E) via yfinance |
| `NewsSearchTool` | `news_search` | Financial news articles via NewsAPI (mock: canned topic-based articles) |
| `SentimentAnalysisTool` | `sentiment_analysis` | Sentiment analysis using keyword heuristic or FinBERT model |
| `RiskCalculationTool` | `risk_calculation` | Risk dashboard: VaR, CVaR, Sharpe, Sortino, Calmar, max drawdown, HHI, stress tests, scenario analysis |
| `PortfolioSimulatorTool` | `portfolio_simulator` | Monte Carlo simulation under GBM with optional rebalancing, SIP contributions, and tax-aware returns |
| `TaxRuleTool` | `tax_rule` | Deterministic Indian capital gains tax calculator (FY 2024-25 rules from `data/tax_rules.json`) |
| `CurrencyConverterTool` | `currency_converter` | FX conversion via open.er-api.com (mock: fixed INR-anchored rate table) |
| `MacroDataTool` | `macro_data` | Indian macro indicators (GDP, inflation, repo rate, unemployment) via World Bank API |
| `GoalPlannerTool` | `goal_planner` | Goal-based financial planning: inflation-adjusted corpus, required SIP, recommended allocation |
| `UserProfileTool` | `user_profile` | Read/write Digital Twin profile (DigitalTwinStore with JSON fallback) |
| `DocumentParserTool` | `document_parser` | Regex-based extraction from portfolio statements, bank statements, tax returns |
| `WatchlistAlertTool` | `watchlist_alert` | Check price alerts against watchlist entries (local JSON persistence) |
| `PDFIngestionTool` | `pdf_ingestion` | Extract holdings from PDF statements (CDSL/NSDL CAS, AMC, bank) and build Digital Twin |

### BaseTool API

```python
class BaseTool(ABC, Generic[In, Out]):
    name: str               # Subclass must set
    ttl_seconds: int = 300  # Cache TTL
    rate_per_sec: float = 5.0  # Token-bucket rate
    max_retries: int = 3    # Retry attempts after first failure
    base_delay: float = 1.0 # Initial backoff delay (doubles each attempt)

    def __call__(self, inp: In) -> Out: ...
    def _run(self, inp: In) -> Out: ...  # Subclass implements this
```

Cache key is SHA-256 of `str(inp)`. Failed tool calls raise `ToolCallError` after all retries are exhausted.

---

## Memory

### MemoryManager

Unified facade over three memory tiers. Agents interact only with this class.

```python
from finroot.memory.manager import MemoryManager

mm = MemoryManager.create(user_id="demo")

# Working memory (conversation buffer)
mm.add_turn("user", "What is compound interest?")
context = mm.get_context()

# Semantic memory (vector search)
mm.remember("Compound interest earns interest on interest", {"topic": "finance"})
results = mm.recall("compound interest", k=5)

# Digital Twin
twin = mm.get_twin()
updated = mm.update_twin(risk_tolerance="aggressive")
```

**Key behaviors:**
- `add_turn()` auto-remembers content > 50 chars into semantic memory
- `update_twin()` rejects `user_id` changes to prevent orphaned rows
- Factory `MemoryManager.create()` builds all three stores in one call

### SemanticMemory

ChromaDB-backed vector store with stdlib TF-IDF fallback.

```python
from finroot.memory.semantic import SemanticMemory

sm = SemanticMemory(persist_dir="data/chroma", collection="finroot")
doc_id = sm.add("text content", {"key": "value"})
results = sm.search("query", k=5)  # [{"text": ..., "metadata": ..., "score": ...}]
sm.delete(doc_id)
sm.clear()
```

- Uses ChromaDB if installed, otherwise falls back to TF-IDF cosine similarity (no external deps)
- Scores: ChromaDB returns `1.0 - distance`; TF-IDF returns cosine similarity

### DigitalTwinStore

SQLite persistence for the user's `DigitalTwin` (with JSON fallback).

```python
from finroot.memory.digital_twin import DigitalTwin, DigitalTwinStore

store = DigitalTwinStore(db_path="data/digital_twin.db")
twin = store.load("demo")
store.save(twin)
ids = store.list_ids()
store.delete("demo")
```

**DigitalTwin fields:**

| Field | Type | Constraints |
|---|---|---|
| `user_id` | `str` | Primary key |
| `name` | `str` | — |
| `age` | `int` | 18–120 |
| `risk_tolerance` | `RiskTolerance` | `conservative`, `moderate`, `aggressive` |
| `investment_horizon` | `InvestmentHorizon` | `short`, `medium`, `long` |
| `monthly_income` | `float` | ≥ 0 |
| `monthly_expenses` | `float` | ≥ 0 |
| `tax_bracket_pct` | `float` | 0–50 |
| `goals` | `list[str]` | — |
| `constraints` | `list[str]` | — |
| `holdings` | `list[dict]` | — |
| `created_at` | `datetime` | UTC-aware |
| `updated_at` | `datetime` | UTC-aware |

### WorkingMemory

Sliding-window conversation buffer (in-memory, configurable `max_turns`).

```python
from finroot.memory.working import WorkingMemory

wm = WorkingMemory(max_turns=10)
wm.add("user", "Hello")
messages = wm.get_messages()  # [{"role": "user", "content": "Hello"}]
```

---

## Evaluation

### Running the FRB Benchmark

```bash
# Full benchmark (83 tasks, 11 domains)
make evals

# Python directly
python3 scripts/run_evals.py --all

# With specific k for pass@k
PYTHONPATH=src python3 -m scripts.run_evals --mock --k 3
```

### Interpreting Results

Results are written to `results/metrics.json` (single source of truth).

**Key metrics:**

| Metric | Description |
|---|---|
| `pass@1` | Fraction of tasks with at least 1 passing sample |
| `pass@k` | Fraction of tasks with at least 1 passing sample out of k trials |
| `pass^k` | Fraction of tasks where ALL k trials pass |
| `mean_score` | Mean 0–1 quality score across all tasks |
| `composite_lift_vs_rag_pct` | FinRoot's improvement over RAG baseline |

**Per-domain scores** are broken down by: general, tax, risk, international, portfolio, behavioral, credit, cashflow, news_impact, estate_planning, insurance.

### Metrics Drift Check

```bash
# Compare HEAD's metrics with on-disk version
make metrics-drift
```

Exits with code 1 if a regression exceeds the threshold.
