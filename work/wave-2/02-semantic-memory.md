# Task wave-2/02 — Semantic Memory (ChromaDB + JSON fallback)

> Read `work/WORKER_PROMPT.md` then build. One self-contained task; stop when report is written.

## Objective
Implement `SemanticMemory` — a vector store backed by ChromaDB with automatic fallback to an
in-memory TF-IDF cosine similarity store (stdlib only) when ChromaDB is absent. Critical for
offline/Mock judging mode.

## Writes (ONLY these)
- `src/finroot/memory/semantic.py`
- `tests/unit/test_semantic_memory.py`

## Forbid
`src/finroot/memory/working.py`, `digital_twin.py`, `manager.py`, `__init__.py` (other tasks own those).

## Contract
Read `.specify/specs/wave-2/contracts/memory.contract.md` § SemanticMemory.

## Steps
1. `SemanticMemory` class:
   - Lazy-import `chromadb` inside `__init__` (G-0b). If `ImportError`, use JSON fallback.
   - `add(text, metadata)` → doc_id (UUID string)
   - `search(query, k=5)` → `list[{"text": ..., "metadata": {...}, "score": float}]` — never raises, returns `[]` on empty
   - `delete(doc_id)` → `None`
   - `clear()` → `None`
2. JSON fallback implementation:
   - Store as `list[{"id": str, "text": str, "metadata": dict, "tf_idf": list[float]}]`
   - TF-IDF vectors computed using stdlib `collections.Counter` (no numpy/sklearn)
   - Cosine similarity for `search` — deterministic, reproducible
3. Tests (minimum 10): add/search round-trip, delete, clear, k-limit, empty-search returns [], ChromaDB path mocked via monkeypatching the import, JSON fallback activated when chromadb absent, metadata preserved.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_semantic_memory.py -v
ruff check src/finroot/memory/semantic.py
```

## Report
`work/reports/wave-2/02-semantic-memory.report.md`
