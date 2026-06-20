# Self-Critic & Reasoning Layer — Interface Contract (Wave-5)

> Frozen before dispatch. Workers code to this; do not deviate without an orchestrator ADR.
> The 35% weapon — highest-leverage wave for scoring.

## 1. Self-Critic  (`src/finroot/reasoning/critic.py`)

```python
class CriticScore(BaseModel):
    axis: str  # "correctness" | "risk_awareness" | "actionability" | "explainability" | "evidence"
    score: float  # 0.0-1.0
    rationale: str  # why this score
    issues: list[str] = []  # specific problems found

class CriticVerdict(BaseModel):
    scores: list[CriticScore]  # 5 scores, one per axis
    overall: float  # weighted average
    passed: bool  # overall >= threshold
    summary: str  # human-readable verdict
    must_fix: list[str]  # issues that MUST be fixed before shipping

class SelfCritic:
    """5-axis reasoning quality scorer. The gate that prevents bad advice."""
    THRESHOLD: float = 0.6  # below this = FAIL
    WEIGHTS: dict[str, float] = {
        "correctness": 0.30,
        "risk_awareness": 0.25,
        "actionability": 0.20,
        "explainability": 0.15,
        "evidence": 0.10,
    }
    def evaluate(self, state: AgentState) -> CriticVerdict: ...
```

- **Correctness (30%)**: Are numbers accurate? Do they match tool outputs? No hallucinated values.
- **Risk-awareness (25%)**: Does the answer flag risks? Does it warn about downsides? Does it match user's risk tolerance?
- **Actionability (20%)**: Is the advice specific enough to act on? Does it include what/when/how?
- **Explainability (15%)**: Can the user understand the reasoning? Is the chain of thought clear?
- **Evidence (10%)**: Is every claim backed by a tool output citation? Are sources named?

The critic MUST catch bad answers (tested against HALL_OF_SHAME seed cases):
- "Put 100% in penny stocks" → FAIL (risk_awareness < 0.3)
- "Buy RELIANCE" with no reasoning → FAIL (explainability < 0.3, evidence < 0.3)
- "I don't know but here's a stock tip" → FAIL (correctness < 0.3)

## 2. Refinement Loop  (`src/finroot/reasoning/refine.py`)

```python
class RefinementLoop:
    """Critique → revise → re-score until quality threshold met or max iterations."""
    MAX_ITERATIONS: int = 3
    def refine(self, state: AgentState, critic: SelfCritic) -> AgentState: ...
```

- Loop: score → if passed, stop; else revise candidate → re-score
- Revision: adjust answer to address `must_fix` items (add risk warnings, add citations, soften overconfident claims)
- Stop conditions: `passed=True` OR `iterations >= 3`
- Each iteration logged to audit trail
- If still failing after 3 iterations: set `final.confidence = LOW` and append "This answer has not met quality standards. Please verify independently."

## 3. Rooted Prudence Principles  (`src/finroot/reasoning/principles.py`)

```python
class PrudentialVerdict(BaseModel):
    compliant: bool  # all critical checks pass
    checks: list[dict[str, Any]]  # [{"principle": str, "pass": bool, "detail": str}]
    warning: str | None  # if non-compliant

class PrudentialVerifier:
    """Financial prudence checklist — the 'do no harm' gate."""
    def verify(self, state: AgentState) -> PrudentialVerdict: ...
```

Principles checklist (all must pass for `compliant=True`):
1. **Emergency fund first**: Never recommend investing emergency fund
2. **Diversification**: Never recommend >40% in single asset/sector
3. **Risk match**: Advice must match user's risk_tolerance from twin
4. **No guarantees**: Never promise returns ("you will make 15%")
5. **Tax awareness**: Consider tax implications before recommending sells
6. **Horizon match**: Investment horizon must match user's stated horizon
7. **Insufficient evidence**: If evidence is weak, say "do not act yet" — never guess

## 4. Self-Consistency  (`src/finroot/reasoning/consistency.py`)

```python
class ConsistencyResult(BaseModel):
    candidates: list[Recommendation]  # N candidates
    winner: Recommendation  # majority-vote winner
    agreement_score: float  # 0.0-1.0 (how similar are the N candidates)
    dissenting_view: str | None  # if agreement < 0.7, note the dissent

class SelfConsistency:
    """Generate N candidates with varied temperature → pick the majority vote."""
    N_CANDIDATES: int = 3
    def check(self, state: AgentState) -> ConsistencyResult: ...
```

- Generate 3 candidates (using mock provider with different seeds/temperatures)
- Compare: if 2/3 agree on the core recommendation → pick that as winner
- If all 3 disagree → `agreement_score=0.0`, note "Low consensus — verify independently"
- Used for high-stakes queries (TAX_PLANNING, RISK_ASSESSMENT)

## 5. Explainability Assembly  (`src/finroot/reasoning/explain.py`)

```python
class ExplainabilityAssembly:
    """Build the human-readable reasoning trace from state."""
    def assemble(self, state: AgentState) -> dict[str, Any]: ...
    # Returns: {
    #   "reasoning_chain": [{"step": int, "action": str, "result": str, "source": str}],
    #   "risk_summary": str,
    #   "confidence_breakdown": {"label": str, "axes": {...}},
    #   "citations": [{"claim": str, "source": str, "data": Any}],
    #   "principles_check": {"compliant": bool, "warnings": [str]}
    # }
```

- Extracts reasoning steps from audit trail events
- Builds citation list from tool_outputs
- Maps critic scores to confidence label (HIGH/MEDIUM/LOW)
- Includes principles check result
- This is what the UI displays as the "reasoning trace" tab

## File map (disjoint write-sets)
| Task | Writes |
|------|--------|
| 01 | `src/finroot/reasoning/critic.py`, `tests/unit/test_critic.py` |
| 02 | `src/finroot/reasoning/refine.py`, `tests/unit/test_refine.py` |
| 03 | `src/finroot/reasoning/principles.py`, `tests/unit/test_principles.py` |
| 04 | `src/finroot/reasoning/consistency.py`, `tests/unit/test_consistency.py` |
| 05 | `src/finroot/reasoning/explain.py`, `tests/unit/test_explain.py` |
