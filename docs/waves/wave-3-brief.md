# Wave 3 — Tool Ecosystem

**Goal:** 12 production tools on the `BaseTool` interface (caching, rate-limit, graceful
degradation, audit emit). **Depends on W1. Parallel with W2.** Highly parallelizable — tools are
independent, so this wave fans out widely.

## Tasks (6 — group the 12 tools; each group is one worker)
| # | Task | Tools | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | Market data + fundamentals | MarketDataTool, FundamentalAnalysisTool | `src/finroot/tools/market.py`, `tools/fundamentals.py` | W1 |
| 02 | News + sentiment | NewsSearchTool, SentimentAnalysisTool (FinBERT) | `src/finroot/tools/news.py`, `tools/sentiment.py` | W1 |
| 03 | Risk + portfolio simulation | RiskCalculationTool, PortfolioSimulatorTool | `src/finroot/tools/risk.py`, `tools/portfolio_sim.py` | W1 |
| 04 | Indian tax engine (deterministic) | TaxRuleTool | `src/finroot/tools/tax.py`, `data/tax_rules.json` | W1 |
| 05 | Macro + currency | MacroDataTool, CurrencyConverterTool | `src/finroot/tools/macro.py`, `tools/currency.py` | W1 |
| 06 | Profile + document + watchlist | UserProfileTool, DocumentParserTool, WatchlistAlertTool | `src/finroot/tools/profile.py`, `tools/documents.py`, `tools/watchlist.py` | W1, W2(profile) |

## Contracts to freeze first
`tools.contract.md` — every tool: typed input/output Pydantic models, TTL cache, token-bucket rate
limit, retry+backoff, **loud failure (no synthetic data)**, audit-emit hook.

## Acceptance
```bash
pytest tests/unit -k tools -v           # each tool: schema, cache, rate-limit, loud-fail
pytest tests/integration -k tools -v    # tools run in Mock/keyless mode and degrade gracefully
```
Tax engine: deterministic, unit-tested against known LTCG/STCG + 80C cases (FM-06, no drift).

## Scoring relevance
Architecture (30%) — rich, robust tool ecosystem with engineering rigor; Reasoning (35%) — these are
the evidence sources every cited number comes from.
