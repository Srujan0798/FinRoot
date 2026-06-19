# Report wave-3/05 — MacroDataTool + CurrencyConverterTool

## Result
DONE

## What I built
- `src/finroot/tools/macro.py` — `MacroDataTool` (Pydantic v2 I/O, `BaseTool`,
  mock + live World Bank API, cache TTL 3600s, FM-11 loud failure on null
  value / network error / unknown indicator).
- `src/finroot/tools/currency.py` — `CurrencyConverterTool` (Pydantic v2
  I/O, `BaseTool`, mock fixed-rate table INR-anchored, live
  `open.er-api.com`, cache TTL 300s, zero-amount + same-currency identity
  shortcuts, cross-rate via INR).
- `tests/unit/test_tools_macro.py` — 35 tests covering mock + live + cache
  + Pydantic input guards for both tools.

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_tools_macro.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-5.0.0, locust-2.43.0, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 35 items

tests/unit/test_tools_macro.py ...................................       [100%]

============================== 35 passed in 0.69s ==============================
exit status: 0

$ ruff check src/finroot/tools/macro.py src/finroot/tools/currency.py
All checks passed!
exit status: 0
```

## Tests
- 35 tests added, all green in 0.69 s. Test classes:
  - `TestMacroMock` (11): each indicator's canned value, default country,
    explicit country, country upper-casing, unknown-indicator Literal
    guard, `extra="forbid"`, cache TTL, env-var mock activation.
  - `TestMacroLive` (4): HTTP stubbed via `mock.patch("urllib.request.urlopen")` —
    success path returns source `worldbank`, network failure raises
    `ToolCallError`, null value fails loud (FM-11), unexpected shape fails loud.
  - `TestCurrencyMock` (14): USD→INR=83.5, EUR→USD cross-rate (EUR/INR ÷
    USD/INR), INR→USD inverse, JPY→INR honour brief's 0.56 value,
    zero-amount shortcut, zero-amount does **not** call network (defence
    test), same-currency identity, currency-code normalisation,
    unknown-currency loud failure, `extra="forbid"`, short-code rejection,
    cache TTL, env-var mock activation, citation contains "2026-06".
  - `TestCurrencyLive` (3): HTTP stubbed — success returns source
    `open.er-api.com`, network failure loud, non-success payload loud.
  - `TestCache` (3): repeated same-input macro call hits cache, repeated
    same-input currency call hits cache, different macro indicators all
    invoke `_run` once each (cache key is per-input).
- No regressions: full unit suite is `366 passed in 77.26s` after my changes
  (was 331 before; +35 = 366). No files outside my Writes set were touched.

## Decisions / deviations
- **Live repo-rate proxy**: brief mandates `FM.RBL.BMNY.ZG` (broad money
  growth) as the "best proxy" for repo rate. I noted in code & docstring
  that this is a proxy; the canonical RBI policy rate is not in the World
  Bank API. Real repo rate is supplied by the mock (6.5%) and NewsSearchTool
  in mock mode already references "RBI holds repo rate steady at 6.5%".
- **`ToolCallError` not `ToolError`**: brief says "raises ToolError"; codebase
  canonical name is `ToolCallError` (defined in `src/finroot/tools/base.py`,
  used by `news.py` and `risk.py`). I followed the codebase to stay
  consistent with the rest of the tool ecosystem.
- **Country upper-casing**: `MacroInput.country` normalises to upper case
  via a `field_validator` (mirrors `CurrencyInput.from_currency /
  to_currency`). This makes the `MacroDataTool(country="in")` call
  symmetric with `CurrencyConverterTool(from_currency="usd")`.
- **Zero-amount + same-currency shortcuts in currency**: handled inside
  `_run` BEFORE the mock/env check so we never consult the rate table or
  the network for trivial inputs. Citation is explicit ("Zero amount:
  identity result, no rate lookup performed") — the audit trail still
  records the call.
- **Mock table note in docstring**: brief specifies `JPY/INR=0.56` (i.e. 1
  JPY = 0.56 INR), which is unrealistic; this is a deterministic dev/test
  fixture, and live mode is the path that returns real-world rates. The
  docstring states this explicitly so future readers don't think it's a
  bug.
- **HTTP library**: used stdlib `urllib.request` (matches `news.py`).
  `requests` is also in the dependencies; either would work.

## Surprises / gotchas
- Y — added to `docs/waves/wave-3-gotchas.md` as **G-3.5: BaseTool retry
  backoff slows down tests that expect loud failure**. First test run took
  48.4 s because the default `BaseTool` retries failed calls 3 times with
  exponential backoff (1+2+4 = 7 s per failing test). Workaround in the
  tests: set `tool.base_delay = 0.001`, `tool.max_retries = 0` on the
  instances that we expect to fail. After the fix, the file runs in 0.69 s.

## Follow-ups (for orchestrator triage — do NOT build now)
- **Better repo-rate source**: RBI publishes the policy repo rate directly
  on `rbi.org.in` (no key); for higher fidelity than the WB broad-money
  proxy, a future task could add an optional RBI RSS / JSON feed. Keep
  World Bank as the primary public-API path (no key, sovereign-friendly).
- **Historical time-series**: brief is point-in-time (`?mrv=1` → most
  recent value). A `period_count` parameter on `MacroInput` could fetch
  N most-recent values for trend analysis; out of scope for this task.
- **Per-currency mock table**: current mock table is INR-anchored. For
  multi-currency reasoning (e.g. EUR→JPY without going via INR), the
  cross-rate via INR is already correct; no follow-up needed.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13) — `git status` will
      show only `src/finroot/tools/macro.py`, `src/finroot/tools/currency.py`,
      `tests/unit/test_tools_macro.py`, `work/reports/wave-3/05-macro-currency-tools.report.md`,
      `docs/waves/wave-3-gotchas.md`. (Report and gotchas are the worker's
      output per the brief; `docs/waves/` is the documented "append on
      surprise" location per `work/WORKER_PROMPT.md`.)
- [x] No fabricated numbers; tool outputs cited (FM-11) — mock values are
      the canonical ones from the brief, live values come from the real
      API or raise loud; null values in the API response cause
      `ToolCallError("...refusing to fabricate (FM-11)")`.
- [x] No bare excepts / silent fallbacks — every error path is a typed
      `ToolCallError` with a contextual message naming the tool, the
      country/currency, and the underlying cause.
- [x] ruff clean, tests green (output above) — `ruff check` is clean on
      the two production files (and on the test file); 35/35 tests pass.
- [x] No secrets committed (FM-07) — no API keys hardcoded; both endpoints
      are no-key public APIs.
