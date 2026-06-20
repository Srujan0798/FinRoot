# Task wave-3/06 — UserProfileTool + DocumentParserTool + WatchlistAlertTool

> Read `work/WORKER_PROMPT.md` then build. Parallel with wave-3; W2 task-03 recommended but not blocking.

## Objective
Three tools for user context management: read/write the Digital Twin profile, parse financial
documents (text-only, regex-based), and check watchlist price alerts.

## Writes (ONLY these)
- `src/finroot/tools/profile.py`
- `src/finroot/tools/documents.py`
- `src/finroot/tools/watchlist.py`
- `tests/unit/test_tools_profile.py`

## Forbid
All other `src/finroot/tools/` files. Do NOT write to `src/finroot/memory/`.

## Contract
Read `.specify/specs/wave-3/contracts/tools.contract.md` § UserProfileTool, § DocumentParserTool, § WatchlistAlertTool.

## Steps

### UserProfileTool (`profile.py`)
- `run(ProfileReadInput)` → `ProfileOutput`: load twin from `DigitalTwinStore`; if W2 not yet available, fall back to loading `data/samples/twin_profiles.json` and finding by `user_id`.
- `run(ProfileWriteInput)` → `ProfileOutput`: update twin fields and save.
- Use duck typing: try `from finroot.memory.digital_twin import DigitalTwinStore`, catch `ImportError` and use JSON fallback (G-0b pattern).
- citation: `"DigitalTwin profile for {user_id}"`

### DocumentParserTool (`documents.py`)
- `run(DocParseInput)` → `DocParseOutput`
- Regex patterns per doc_type:
  - `portfolio_statement`: extract total_value (₹ amounts), holdings (TICKER: N units), date
  - `bank_statement`: extract total_credits, total_debits, closing_balance
  - `tax_return`: extract gross_income, tax_paid, refund_amount
  - `generic`: extract any ₹ amounts and dates found
- `confidence`: fraction of expected fields found (0.0–1.0)
- Never raises on parse failure — returns empty `extracted` with `confidence=0.0` (this is a best-effort tool)
- citation: `"Regex extraction from {doc_type} document"`

### WatchlistAlertTool (`watchlist.py`)
- `run(AlertCheckInput)` → `AlertCheckOutput`
- Reads `data/watchlists/{user_id}.json`; returns empty `triggered=[]` if file absent (not an error — user may have no watchlist).
- `triggered`: entries where `current_prices[symbol]` crosses the `target_price` in `direction`.
- Persistence helpers: `add_to_watchlist(user_id, entry: WatchlistEntry)` and `remove_from_watchlist(user_id, symbol)` as module-level functions (not BaseTool subclasses — they're write ops, not query tools).
- citation: `"Watchlist check for {user_id}, {n} symbols evaluated"`

### Tests (minimum 14):
- Profile: read returns all fields, write updates specific field
- Profile: unknown user_id raises ToolError (FM-11 — not silent empty)
- Document: portfolio_statement extracts total_value
- Document: unknown doc_type still returns generic extraction
- Watchlist: alert triggered when price crosses target (above/below both)
- Watchlist: no alert when price hasn't crossed
- Watchlist: empty list when no watchlist file

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_tools_profile.py -v
ruff check src/finroot/tools/profile.py src/finroot/tools/documents.py src/finroot/tools/watchlist.py
```

## Report
`work/reports/wave-3/06-profile-document-watchlist-tools.report.md`
