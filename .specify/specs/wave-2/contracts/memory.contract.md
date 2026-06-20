# Memory & Digital Twin — Interface Contract (Wave-2)

> Frozen before dispatch. Workers code to this; do not deviate without an orchestrator ADR.

## 1. WorkingMemory  (`src/finroot/memory/working.py`)

```python
class WorkingMemory:
    """Sliding-window conversation buffer. Thread-safe, serialisable."""
    def __init__(self, max_turns: int = 10) -> None: ...
    def add(self, role: Literal["user", "assistant", "tool"], content: str) -> None: ...
    def get_messages(self) -> list[dict[str, str]]: ...  # [{"role": ..., "content": ...}]
    def clear(self) -> None: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_json(cls, data: str) -> WorkingMemory: ...
```
- Max turns enforced as a sliding window (oldest dropped when over limit).
- `role` validated — invalid role raises `ValueError` (FM-11, fail loud).

## 2. SemanticMemory  (`src/finroot/memory/semantic.py`)

```python
class SemanticMemory:
    """ChromaDB-backed vector store with JSON fallback for offline/Mock mode."""
    def __init__(self, persist_dir: str = "data/chroma", collection: str = "finroot") -> None: ...
    def add(self, text: str, metadata: dict[str, Any]) -> str: ...  # returns doc_id
    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]: ...
    # returns [{"text": ..., "metadata": {...}, "score": float}]
    def delete(self, doc_id: str) -> None: ...
    def clear(self) -> None: ...
```
- ChromaDB import is **lazy** (G-0b). Falls back to in-memory JSON store when `chromadb` unavailable.
- JSON fallback uses cosine similarity on TF-IDF vectors (stdlib only, no extra deps).
- `search` always returns list (empty if no results — never raises on miss).

## 3. DigitalTwin  (`src/finroot/memory/digital_twin.py`)

```python
class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class InvestmentHorizon(str, Enum):
    SHORT = "short"   # < 1 year
    MEDIUM = "medium" # 1–5 years
    LONG = "long"     # > 5 years

class DigitalTwin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    name: str
    age: int = Field(ge=18, le=120)
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    investment_horizon: InvestmentHorizon = InvestmentHorizon.MEDIUM
    monthly_income: float = Field(ge=0)
    monthly_expenses: float = Field(ge=0)
    tax_bracket_pct: float = Field(ge=0, le=50)  # Indian IT slab %
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    holdings: list[dict[str, Any]] = Field(default_factory=list)  # serialised Holding dicts
    created_at: datetime
    updated_at: datetime

class DigitalTwinStore:
    """SQLite-backed persistence with JSON fallback."""
    def __init__(self, db_path: str = "data/digital_twin.db") -> None: ...
    def save(self, twin: DigitalTwin) -> None: ...
    def load(self, user_id: str) -> DigitalTwin: ...  # raises KeyError if not found
    def list_ids(self) -> list[str]: ...
    def delete(self, user_id: str) -> None: ...
```
- SQLite schema written to `schema/db_struct.sql` (CREATE TABLE IF NOT EXISTS).
- JSON fallback: if SQLite unavailable, persist to `data/digital_twin_{user_id}.json`.
- `holdings` stored as JSON column; deserialized as `list[dict]` (not typed here — W4 casts to `Holding`).

## 4. MemoryManager  (`src/finroot/memory/manager.py`)

```python
class MemoryManager:
    """Unified facade: working + semantic + twin read/write."""
    def __init__(
        self,
        working: WorkingMemory,
        semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
        user_id: str,
    ) -> None: ...

    # Working memory
    def add_turn(self, role: str, content: str) -> None: ...
    def get_context(self) -> list[dict[str, str]]: ...

    # Semantic memory
    def remember(self, text: str, metadata: dict[str, Any] | None = None) -> str: ...
    def recall(self, query: str, k: int = 5) -> list[dict[str, Any]]: ...

    # Digital Twin
    def get_twin(self) -> DigitalTwin: ...  # loads from store; raises if not found
    def update_twin(self, **kwargs: Any) -> DigitalTwin: ...  # partial update + save
```
- `MemoryManager` is the only class wave-4 agents touch for memory operations.
- All methods fail loud (no silent fallbacks).

## 5. Synthetic fixtures  (`data/samples/`, `data/synthetic/`)

- `data/samples/twin_profiles.json` — 3 sample DigitalTwin dicts (conservative/moderate/aggressive)
- `data/synthetic/sample_conversation.json` — 10-turn conversation fixture for testing
- `data/samples/README.md` — documents what each fixture is for
- No real PII; all names/numbers are clearly synthetic.

## File map (disjoint write-sets)
| Task | Writes |
|------|--------|
| 01 | `src/finroot/memory/working.py`, `src/finroot/memory/__init__.py`, `tests/unit/test_working_memory.py` |
| 02 | `src/finroot/memory/semantic.py`, `tests/unit/test_semantic_memory.py` |
| 03 | `src/finroot/memory/digital_twin.py`, `schema/db_struct.sql`, `tests/unit/test_digital_twin.py` |
| 04 | `src/finroot/memory/manager.py`, `tests/unit/test_memory_manager.py`, `tests/integration/test_memory_integration.py` |
| 05 | `data/samples/twin_profiles.json`, `data/samples/README.md`, `data/synthetic/sample_conversation.json` |
