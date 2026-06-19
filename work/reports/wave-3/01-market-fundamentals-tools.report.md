# Report wave-3/01 — MarketDataTool + FundamentalAnalysisTool

## Result
DONE

## What I built
- `src/finroot/tools/market.py` — `MarketDataInput`, `PricePoint`, `MarketDataOutput`, `ToolError` (contract alias for `ToolCallError`), `MarketDataTool`
- `src/finroot/tools/fundamentals.py` — `FundamentalInput`, `FundamentalOutput`, `FundamentalAnalysisTool`
- `tests/unit/test_tools_market.py` — 34 tests across 11 test classes (14 required by the brief)

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_tools_market.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 34 items

tests/unit/test_tools_market.py ..................................       [100%]

============================== 34 passed in 0.30s ==============================
exit 0

$ ruff check src/finroot/tools/market.py src/finroot/tools/fundamentals.py
All checks passed!
exit 0
```

Full unit suite (sanity — must not have regressed wave-1):
```
$ PYTHONPATH=src python3 -m pytest tests/unit/
366 passed in 67.23s (0:01:07)
```

## Tests
- 34 tests · 34 pass · 0 fail · 0 skip
- Classes: `TestMarketDataToolMock` (9), `TestMarketDataToolInputValidation` (4),
  `TestMarketDataToolCache` (3), `TestMarketDataToolAudit` (2),
  `TestMarketDataToolRateLimit` (1), `TestMarketDataToolLive` (2),
  `TestFundamentalAnalysisToolMock` (5),
  `TestFundamentalAnalysisToolInputValidation` (2),
  `TestFundamentalAnalysisToolCacheAndAudit` (3),
  `TestFundamentalAnalysisToolLive` (3)

Coverage of the six required test themes:
| Brief requirement | Test(s) |
|---|---|
| Mock mode returns correct shape + citation | `test_returns_market_data_output`, `test_citation_is_offline_judging`, `test_returns_exactly_5_price_points`, plus fundamentals mirror tests |
| Input validation (empty symbol raises ValidationError) | `test_empty_symbol_raises_validation_error` (both tools) |
| Cache hit on second call (mock the underlying fetch) | `test_cache_hit_on_second_call` (both tools, uses `_CountingMarketTool` / `_CountingFundamentalTool` to count `_run` invocations) |
| Audit event emitted (`trail.replay()` has 1 entry) | `test_audit_event_emitted_on_call` (both tools) |
| Rate limiter doesn't raise on < 10 req/s | `test_no_raise_under_10_req_per_sec` (sets `rate_per_sec=20`, fires 5 calls) |
| `ToolError` raised when yfinance unavailable in live mode (monkeypatch) | `test_yfinance_unavailable_raises_tool_error` (both tools, monkeypatches `_import_yfinance`) |

## Decisions / deviations
1. **`ToolError` is a subclass of `ToolCallError`, not an alias.** The contract
   names the exception `ToolError`; the wave-1 base class named it
   `ToolCallError`. Subclassing preserves the contract name while keeping
   `except ToolCallError` callers working. Defined once in `market.py`,
   re-imported by `fundamentals.py`.
2. **Stable hash for mock prices.** Python's `hash()` is randomised
   (`PYTHONHASHSEED`); using it for the contract formula
   `100.0 * hash(symbol) % 500 + 100` would make mock prices differ across
   processes. I use the first 4 bytes of SHA-256 instead — same formula,
   cross-process stable. The test `test_latest_price_matches_contract_formula`
   pins the exact value via the same helper.
3. **Live-mode import isolated to `_import_yfinance(self)`.** A separate
   method gives tests a clean monkeypatch seam without depending on whether
   yfinance is actually installed in the CI env, and without resorting to
   `sys.modules` trickery.
4. **Sentinel handling for `FundamentalAnalysisTool` live mode.** yfinance
   uses `1e308` and `NaN` to mean "not applicable" in `Ticker.info`;
   `FundamentalAnalysisTool._coerce_float` maps both to `None` so the UI
   can show "—" instead of `inf` / `nan`. Tested by
   `test_live_sentinel_values_surface_as_none`.
5. **TTL set explicitly on both classes.** Even though 300s is the
   `BaseTool` default, I set `ttl_seconds = 300` on `MarketDataTool`
   explicitly so the value is self-documenting and survives any future
   change to the base default.
6. **Single `ToolError` definition site.** The other wave-3 tasks (02–06)
   may also need a `ToolError`; they can import from `finroot.tools.market`
   or define their own. Either way, no FM-13 violation since each task
   owns its own write-set.

## Surprises / gotchas
- None hit that weren't already in `docs/waves/wave-1-gotchas.md`.
- `docs/waves/wave-3-gotchas.md` does not exist yet (the brief said to
  create it only if I hit a surprise) — not added.

## Follow-ups (for orchestrator triage — do NOT build now)
- **Centralize `ToolError` in `tools/base.py`.** Currently lives in
  `tools/market.py`; the other 5 wave-3 tool files will either need to
  re-import it or duplicate. Cleaner: promote to `base.py` in a future wave
  (or a wave-3 cross-cutting micro-task).
- **Period as `Literal` is good, but a richer enum with a yfinance interval
  hint (e.g. `"1d" → "1m"`, `"1y" → "1wk"`) would let the live path
  request appropriate bar granularity.** Out of scope for the brief, which
  only specifies the period strings.
- **Currency mapping for live mode could be richer.** Currently falls
  back to a suffix heuristic if `fast_info.currency` is missing. The
  authoritative answer requires either a static country→currency table
  or a yfinance-supported property we don't yet use.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13) — verified with `git status`
- [x] No fabricated numbers; tool outputs cited (FM-11) — mock numbers are
  derived from the contract formula, live numbers come from yfinance with
  `citation = "Yahoo Finance via yfinance, fetched <ISO date>"`
- [x] No bare excepts / silent fallbacks — all live-mode exceptions
  are mapped to `ToolError`; no `except: pass`
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
