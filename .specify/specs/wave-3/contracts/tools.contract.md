# Tool Ecosystem — Interface Contract (Wave-3)

> Frozen before dispatch. All tools extend `BaseTool` from `src/finroot/tools/base.py` (W1).
> Workers code to this; do not deviate without an orchestrator ADR.

## Universal tool contract (all 12 tools must satisfy)

Every tool:
1. Extends `BaseTool` — inherits `cache`, `rate_limiter`, `_audit_emit`.
2. Has a typed `Input` Pydantic model (`extra="forbid"`) and typed `Output` Pydantic model.
3. `run(input: Input) -> Output` is the only public method (plus `arun` for async variant).
4. **Fail loud (FM-11)**: on missing API key or network error, raise `ToolError` with message — never return synthetic data. Mock mode returns deterministic canned fixtures.
5. Mock mode activated by `FINROOT_LLM_PROVIDER=mock` or `mock=True` constructor arg.
6. Cache TTL: market/news = 300s; tax/profile = 3600s; fundamentals = 3600s.
7. Rate limit: ≤ 10 req/s per tool instance (token-bucket, inherited from BaseTool).
8. Audit emit: every `run()` call emits one `AuditEvent` with `{"tool": name, "input": ..., "output": ...}`.

## Tool definitions

### MarketDataTool  (`src/finroot/tools/market.py`)
```python
class MarketDataInput(BaseModel):
    symbol: str  # e.g. "RELIANCE.NS"
    period: str = "1d"  # "1d" | "5d" | "1mo" | "3mo" | "1y"

class PricePoint(BaseModel):
    date: str; open: float; high: float; low: float; close: float; volume: int

class MarketDataOutput(BaseModel):
    symbol: str; currency: str; prices: list[PricePoint]
    latest_price: float; change_pct: float
    source: str  # "yfinance" | "mock"
    citation: str  # e.g. "Yahoo Finance, 2026-06-19"
```
Mock: return 5 deterministic price points for any symbol.

### FundamentalAnalysisTool  (`src/finroot/tools/fundamentals.py`)
```python
class FundamentalInput(BaseModel):
    symbol: str

class FundamentalOutput(BaseModel):
    symbol: str; pe_ratio: float | None; pb_ratio: float | None
    eps: float | None; dividend_yield: float | None; market_cap: float | None
    revenue_ttm: float | None; debt_to_equity: float | None
    source: str; citation: str
```
Mock: return deterministic ratios for any symbol.

### NewsSearchTool  (`src/finroot/tools/news.py`)
```python
class NewsInput(BaseModel):
    query: str; max_results: int = Field(default=5, ge=1, le=20)

class NewsArticle(BaseModel):
    title: str; url: str; published_at: str; source: str; summary: str

class NewsOutput(BaseModel):
    articles: list[NewsArticle]; source: str; citation: str
```
Live: NewsAPI (key `FINROOT_NEWSAPI_KEY`). Mock: 3 canned articles.

### SentimentAnalysisTool  (`src/finroot/tools/sentiment.py`)
```python
class SentimentInput(BaseModel):
    texts: list[str]  # 1–20 items

class SentimentResult(BaseModel):
    text: str; label: Literal["positive", "negative", "neutral"]; score: float

class SentimentOutput(BaseModel):
    results: list[SentimentResult]; model: str; citation: str
```
Implementation: keyword-based heuristic (no FinBERT dep for Mock). When `transformers` available, use `ProsusAI/finbert`. Always falls back to heuristic if model unavailable.

### RiskCalculationTool  (`src/finroot/tools/risk.py`)
```python
class RiskInput(BaseModel):
    returns: list[float]  # daily returns, annualized internally
    confidence: float = Field(default=0.95, ge=0.9, le=0.99)

class RiskOutput(BaseModel):
    volatility_annual: float; var_95: float; cvar_95: float
    sharpe_ratio: float | None; max_drawdown: float
    citation: str  # "Computed from {n} daily returns, annualised"
```
Pure Python + stdlib math — no numpy required (but use if available). All formulas cited.

### PortfolioSimulatorTool  (`src/finroot/tools/portfolio_sim.py`)
```python
class SimInput(BaseModel):
    holdings: list[dict[str, Any]]  # [{"symbol": str, "weight": float}]
    horizon_years: int = Field(ge=1, le=30)
    scenarios: int = Field(default=1000, ge=100, le=10000)

class SimOutput(BaseModel):
    expected_return: float; p10_return: float; p90_return: float
    probability_of_loss: float; citation: str
```
Monte Carlo simulation (stdlib random). Deterministic seed in Mock mode.

### TaxRuleTool  (`src/finroot/tools/tax.py`)
```python
class TaxInput(BaseModel):
    gain: float            # absolute gain in INR
    gain_type: Literal["LTCG", "STCG", "STCG_EQUITY"]
    annual_income: float   # total annual income in INR (for slab)
    cess: bool = True

class TaxOutput(BaseModel):
    tax_amount: float; effective_rate_pct: float
    breakdown: dict[str, float]  # {"base_tax": ..., "cess": ..., "surcharge": ...}
    rule_applied: str  # e.g. "LTCG equity 10% > ₹1L (Budget 2024)"
    citation: str
```
Rules stored in `data/tax_rules.json`. Deterministic — no live API. Unit-tested against known cases.
Indian FY 2024-25 slabs + LTCG/STCG rules (10%/15% equity, 20%/slab for debt/others, 80C deduction not in scope of this tool — just the gain tax).

### MacroDataTool  (`src/finroot/tools/macro.py`)
```python
class MacroInput(BaseModel):
    indicator: Literal["gdp_growth", "inflation", "repo_rate", "unemployment"]
    country: str = "IN"

class MacroOutput(BaseModel):
    indicator: str; country: str; value: float; unit: str
    period: str; source: str; citation: str
```
Mock: canned Indian macro values. Live: World Bank API (no key required, public endpoint).

### CurrencyConverterTool  (`src/finroot/tools/currency.py`)
```python
class CurrencyInput(BaseModel):
    amount: float; from_currency: str; to_currency: str

class CurrencyOutput(BaseModel):
    converted_amount: float; rate: float
    from_currency: str; to_currency: str
    source: str; citation: str
```
Mock: fixed rates table (USD/INR=83.5, EUR/INR=90.2, etc.). Live: open.er-api.com (free tier).

### UserProfileTool  (`src/finroot/tools/profile.py`)
```python
class ProfileReadInput(BaseModel):
    user_id: str; fields: list[str] | None = None  # None = all fields

class ProfileWriteInput(BaseModel):
    user_id: str; updates: dict[str, Any]

class ProfileOutput(BaseModel):
    user_id: str; data: dict[str, Any]; citation: str
```
Reads/writes the DigitalTwin via a thin wrapper (imports `DigitalTwinStore` from W2 — task 06 depends on W2 task 03). Stub: if DigitalTwinStore not yet available, load from `data/samples/twin_profiles.json`.

### DocumentParserTool  (`src/finroot/tools/documents.py`)
```python
class DocParseInput(BaseModel):
    content: str  # raw text (PDF text extracted by caller, not here)
    doc_type: Literal["portfolio_statement", "bank_statement", "tax_return", "generic"]

class DocParseOutput(BaseModel):
    doc_type: str
    extracted: dict[str, Any]  # structured fields found
    confidence: float
    citation: str
```
Implementation: regex + keyword extraction. No OCR (caller provides text). Mock: deterministic extraction from fixture content.

### WatchlistAlertTool  (`src/finroot/tools/watchlist.py`)
```python
class WatchlistEntry(BaseModel):
    symbol: str; target_price: float; direction: Literal["above", "below"]
    alert_message: str

class AlertCheckInput(BaseModel):
    user_id: str; current_prices: dict[str, float]  # symbol → price

class AlertCheckOutput(BaseModel):
    triggered: list[WatchlistEntry]; citation: str
```
Persistence: JSON file at `data/watchlists/{user_id}.json`. No external API.

## File map (disjoint write-sets)
| Task | Writes |
|------|--------|
| 01 | `src/finroot/tools/market.py`, `src/finroot/tools/fundamentals.py`, `tests/unit/test_tools_market.py` |
| 02 | `src/finroot/tools/news.py`, `src/finroot/tools/sentiment.py`, `tests/unit/test_tools_news.py` |
| 03 | `src/finroot/tools/risk.py`, `src/finroot/tools/portfolio_sim.py`, `tests/unit/test_tools_risk.py` |
| 04 | `src/finroot/tools/tax.py`, `data/tax_rules.json`, `tests/unit/test_tools_tax.py` |
| 05 | `src/finroot/tools/macro.py`, `src/finroot/tools/currency.py`, `tests/unit/test_tools_macro.py` |
| 06 | `src/finroot/tools/profile.py`, `src/finroot/tools/documents.py`, `src/finroot/tools/watchlist.py`, `tests/unit/test_tools_profile.py` |
