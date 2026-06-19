# Wave 2 — Memory & Financial Digital Twin

**Goal:** the 4-tier memory system + the Financial Digital Twin (the user-state model that makes
FinRoot personal and contextual). **Depends on W1. Runs in parallel with W3.**

## Tasks (5)
| # | Task | Suggested agent role | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | Working memory (ConversationBufferWindow) | backend | `src/finroot/memory/working.py` | W1 |
| 02 | Semantic memory (Chroma + JSON fallback) | ML/data | `src/finroot/memory/semantic.py` | W1 |
| 03 | Digital Twin model + SQLite persistence | data modeling | `src/finroot/memory/digital_twin.py`, `schema/db_struct.sql` | W1 |
| 04 | Memory manager (unified read/write facade) | architecture | `src/finroot/memory/manager.py` | 01,02,03 |
| 05 | Sample synthetic Digital Twins + fixtures | data | `data/samples/**`, `data/synthetic/**` | 03 |

## Contracts to freeze first
`memory.contract.md` — interfaces for `MemoryManager`, `DigitalTwin` (goals, risk tolerance,
horizon, holdings, tax bracket, constraints), retrieval API. (Orchestrator writes this in /plan.)

## Acceptance
```bash
pytest tests/unit -k memory -v          # working/semantic/twin round-trip
pytest tests/integration -k twin -v     # twin persists + reloads; retrieval returns relevant items
```
Semantic memory MUST degrade gracefully to JSON when ChromaDB is absent (no hard dep for Mock).

## Scoring relevance
Architecture (30%) — real LangChain memory + structured state; Reasoning (35%) — context the agent
reasons over; Idea (15%) — the Digital Twin is a core differentiator.
