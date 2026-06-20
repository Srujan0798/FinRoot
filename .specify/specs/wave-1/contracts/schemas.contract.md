# Contract — Core Schemas (wave-1, task 02)

> Frozen interface every wave-1 task imports. Owned by task 02. Changes require an ADR.
> Workers implement these in `src/finroot/schemas/`. Names and field types are the contract;
> internal helpers are the implementer's choice.

## Modules
- `schemas/enums.py` — `Intent`, `Domain`, `ConfidenceLevel`, `RiskBand`, `Provider`.
- `schemas/finance.py` — domain value objects.
- `schemas/recommendation.py` — the output contract.
- `schemas/state.py` — the LangGraph `AgentState`.
- `schemas/audit.py` — audit event shape (shared with task 03).

## Enums
```python
class Intent(str, Enum):
    PORTFOLIO = "portfolio"; RISK = "risk"; TAX = "tax"; NEWS_IMPACT = "news_impact"
    CASHFLOW = "cashflow"; CREDIT = "credit"; GENERAL = "general"

class ConfidenceLevel(str, Enum):
    HIGH = "high"; MEDIUM = "medium"; LOW = "low"; INSUFFICIENT = "insufficient"

class RiskBand(str, Enum):
    LOW = "low"; MODERATE = "moderate"; HIGH = "high"; SEVERE = "severe"

class Provider(str, Enum):
    MOCK = "mock"; OLLAMA = "ollama"; GROQ = "groq"; OPENAI = "openai"
```

## Citation + Recommendation (the user-facing output contract)
```python
class Citation(BaseModel):
    source: str            # tool name or data source
    detail: str            # what was retrieved
    value: str | None      # the figure/fact, if numeric
    retrieved_at: datetime

class Recommendation(BaseModel):
    summary: str
    analysis: str
    risks: list[str]
    actions: list[str]               # may include "do not act yet"
    alternatives: list[str] = []
    confidence: ConfidenceLevel
    citations: list[Citation]        # MUST be non-empty if analysis contains numbers (FM-11)
    assumptions: list[str] = []
    invalidation_conditions: list[str] = []
```

## LangGraph AgentState (carried through the pipeline)
```python
class AgentState(BaseModel):
    query: str
    intent: Intent | None = None
    twin_snapshot: dict = {}                 # Digital Twin (filled in W2)
    plan: list[str] = []                     # ordered steps
    tool_outputs: list[dict] = []            # structured per-step outputs
    candidate: Recommendation | None = None  # pre-critique
    critique: dict | None = None             # 5-axis scores (W5)
    verifier_verdict: dict | None = None     # Rooted Prudence (W5)
    final: Recommendation | None = None
    audit_events: list["AuditEvent"] = []
    model_config = ConfigDict(extra="forbid")
```

## AuditEvent (shared with task 03)
```python
class AuditEvent(BaseModel):
    ts: datetime
    seq: int
    type: str                # task.dispatched | tool.called | step.done | critique | merge ...
    payload: dict
    prev_hash: str           # hash of previous event (chain)
    hash: str                # sha256(prev_hash + canonical(payload) + ts + seq)
```

## Invariants
- All models `extra="forbid"` (catch typos at the boundary — Swiss-cheese layer 1).
- Datetimes are timezone-aware UTC.
- `Recommendation` with numeric content and empty `citations` is INVALID (validator enforces FM-11).
