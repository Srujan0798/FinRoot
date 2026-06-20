# Task wave-2/01 — Working Memory (ConversationBufferWindow)

> Read `work/WORKER_PROMPT.md` then build. One self-contained task; stop when report is written.

## Objective
Implement `WorkingMemory` — a sliding-window conversation buffer that stores the last N turns
(user/assistant/tool), is thread-safe, JSON-serialisable, and integrates with LangChain memory.

## Writes (ONLY these)
- `src/finroot/memory/working.py`
- `src/finroot/memory/__init__.py`
- `tests/unit/test_working_memory.py`

## Forbid
Everything else in `src/finroot/memory/` (semantic.py, digital_twin.py, manager.py — other tasks own those).

## Contract
Read `.specify/specs/wave-2/contracts/memory.contract.md` § WorkingMemory.

## Steps
1. `WorkingMemory` class:
   - `__init__(max_turns=10)` — validate `max_turns >= 1`
   - `add(role, content)` — validates role (`"user"` | `"assistant"` | `"tool"`); raises `ValueError` on unknown (FM-11); drops oldest turn when over limit
   - `get_messages()` — returns `list[dict[str,str]]` in insertion order
   - `clear()` — empties buffer
   - `to_json()` / `from_json()` — full round-trip serialisation
2. Thread safety: use `threading.Lock` around all mutations.
3. `src/finroot/memory/__init__.py` — re-export `WorkingMemory`.
4. Tests (minimum 12): max_turns sliding window, invalid role raises, round-trip, clear, thread-safe concurrent add (use `threading.Thread`).

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_working_memory.py -v
ruff check src/finroot/memory/working.py src/finroot/memory/__init__.py
```
All tests pass, ruff clean.

## Report
`work/reports/wave-2/01-working-memory.report.md`
