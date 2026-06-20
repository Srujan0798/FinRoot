# Task wave-3/01 — MarketDataTool + FundamentalAnalysisTool

> Read `work/WORKER_PROMPT.md` then build. Parallel with other wave-3 tasks.

## Objective
Implement two tools extending `BaseTool`: live market price data (yfinance) and fundamental
analysis ratios, both with Mock canned responses for offline judging.

## Writes (ONLY these)
- `src/finroot/tools/market.py`
- `src/finroot/tools/fundamentals.py`
- `tests/unit/test_tools_market.py`

## Forbid
All other `src/finroot/tools/` files (other wave-3 tasks own those).

## Contract
Read `.specify/specs/wave-3/contracts/tools.contract.md` § MarketDataTool, § FundamentalAnalysisTool.
Read `src/finroot/tools/base.py` for `BaseTool` interface.

## Steps
1. `MarketDataTool(BaseTool)`:
   - `run(MarketDataInput)` → `MarketDataOutput`
   - Mock mode: 5 deterministic price points, `latest_price=100.0 * hash(symbol) % 500 + 100`, citation "Mock data (offline judging mode)"
   - Live mode: `yfinance` (lazy import). On `ImportError` or network error → `ToolError` (FM-11).
   - Cache TTL 300s (inherited).

2. `FundamentalAnalysisTool(BaseTool)`:
   - `run(FundamentalInput)` → `FundamentalOutput`
   - Mock mode: deterministic ratios (PE=22.5, PB=3.1, etc.) regardless of symbol.
   - Live mode: `yfinance.Ticker(symbol).info` — extract fields, handle missing as `None` (not error).
   - Cache TTL 3600s.

3. Tests (minimum 14):
   - Mock mode returns correct shape + citation
   - Input validation (empty symbol raises ValidationError)
   - Cache hit on second call (mock the underlying fetch)
   - Audit event emitted (check `trail.replay()` has 1 entry after one call)
   - Rate limiter doesn't raise on < 10 req/s
   - `ToolError` raised when yfinance unavailable in live mode (monkeypatch)

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_tools_market.py -v
ruff check src/finroot/tools/market.py src/finroot/tools/fundamentals.py
```

## Report
`work/reports/wave-3/01-market-fundamentals-tools.report.md`
