# Task wave-2/04 — Memory Manager (Unified Facade)

> Read `work/WORKER_PROMPT.md` then build. **Dispatch AFTER tasks 01+02+03 complete.**

## Objective
Implement `MemoryManager` — the single unified interface that wave-4 agents use for all memory
operations (working, semantic, digital twin). Composes all three tiers; wave-4 never touches
the underlying stores directly.

## Writes (ONLY these)
- `src/finroot/memory/manager.py`
- `tests/unit/test_memory_manager.py`
- `tests/integration/test_memory_integration.py`

## Forbid
`working.py`, `semantic.py`, `digital_twin.py`, `__init__.py` (those tasks own those files — import only).

## Contract
Read `.specify/specs/wave-2/contracts/memory.contract.md` § MemoryManager.

## Steps
1. `MemoryManager` class (contract exactly):
   - Constructor takes `WorkingMemory`, `SemanticMemory`, `DigitalTwinStore`, `user_id`.
   - `add_turn(role, content)` → delegates to `working.add()`; also calls `semantic.add()` if content > 50 chars (auto-remember long turns).
   - `get_context()` → `working.get_messages()`.
   - `remember(text, metadata=None)` → `semantic.add(text, metadata or {})` → doc_id.
   - `recall(query, k=5)` → `semantic.search(query, k)`.
   - `get_twin()` → `twin_store.load(user_id)` — raises `KeyError` if not found (FM-11).
   - `update_twin(**kwargs)` → load, update fields, save, return updated twin.
   - All methods fail loud; no bare except.
2. Convenience factory: `MemoryManager.create(user_id, chroma_dir="data/chroma", db_path="data/digital_twin.db")` → instantiates all three stores and returns `MemoryManager`.
3. Unit tests (minimum 12): each delegation, auto-remember threshold, update_twin partial update, get_twin missing raises.
4. Integration test: full round-trip — create manager, add 5 turns, recall last relevant, save twin, reload manager, twin persists.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_memory_manager.py -v
PYTHONPATH=src python3 -m pytest tests/integration/test_memory_integration.py -v
ruff check src/finroot/memory/manager.py
```

## Report
`work/reports/wave-2/04-memory-manager.report.md`
