# tests/ — taxonomy (workers write these alongside their tasks)

> The OS-Setup provides the structure; workers add tests with the code they implement (per their
> task's acceptance). Tests run in **Mock mode** by default — deterministic, offline, seeded.

| Folder | What goes here | Owner wave |
|---|---|---|
| `unit/` | one module in isolation (schemas, providers, audit chain, each tool) | every wave |
| `integration/` | module interaction (memory↔tools, graph↔agents) | W2–W4 |
| `e2e/` | full query → recommendation through CLI/UI | W4, W7 |
| `golden/` | curated reasoning cases with expected qualities (not exact strings) | W5 |
| `fuzz/` | adversarial/garbled inputs; agent must fail safe, never fabricate | W5–W6 |
| `performance/` | latency budgets (PERFORMANCE_SLOS.md), Mock judge-path P95 | W6 |
| `security/` | no money-tool exists; injection resistance; no secret leakage | W6, audits |

## Conventions
- Deterministic: seed all RNG; `FINROOT_LLM_PROVIDER=mock`; fresh state per test (no shared pollution).
- Finance assertions check **properties** (number is cited, risk flagged, confidence set), not exact prose.
- Run: `pytest` (all) · `pytest tests/unit -k wave1` (foundation) · `make test`.
