# Evaluation Harness (FRB) — Interface Contract (Wave-6)

> Frozen before dispatch. The proof behind the 35%. Numbers live ONLY in `results/metrics.json`.

## FRB task shape  (`data/gold/frb_questions.json`)
JSON array; each item:
```python
{
  "id": "frb-001",
  "domain": "portfolio" | "risk" | "tax" | "news_impact" | "cashflow" | "credit" | "general",
  "difficulty": "easy" | "medium" | "hard",
  "query": str,
  "twin_id": str | null,          # which sample twin to load (or null = no twin)
  "expected": {
     "must_mention": [str],       # keywords/concepts a correct answer must include
     "must_not": [str],           # red-flag phrases that fail the answer (e.g. "guaranteed returns")
     "min_citations": int,        # minimum cited evidence count
     "expected_confidence": "high" | "medium" | "low" | null,
     "numeric_answer": float | null,   # for deterministic tasks (tax), exact expected value
     "numeric_tolerance": float        # acceptable +/- (e.g. 0.01)
  },
  "rationale": str                 # why this is the right answer (human reference)
}
```
- ≥ 24 questions, spread across ≥ 5 domains, class-balanced difficulty, including ≥ 4 adversarial
  "trap" questions (must trigger principles verifier / "do not act yet").

## Grader interface  (`evals/graders/`)
```python
class GradeResult(BaseModel):
    task_id: str
    passed: bool
    score: float            # 0.0-1.0
    breakdown: dict[str, Any]   # per-criterion detail
    grader: str             # "code" | "llm_judge" | "human"

# code_based.py
def grade_code(task: dict, state: AgentState) -> GradeResult: ...
# Checks: must_mention present, must_not absent, citation count, numeric match (tax), confidence match.

# llm_judge.py
def grade_llm(task: dict, state: AgentState, judge_llm) -> GradeResult: ...
# Uses an LLM (Mock-capable) to score reasoning quality on the 5 axes; deterministic in mock.
```

## Baselines  (`src/finroot/evaluation/baselines.py`)
```python
class NaiveRAGBaseline:   # retrieve + single LLM call, no agents/critic
    def answer(self, query: str, twin: dict | None = None) -> AgentState: ...
class SingleAgentBaseline: # one ReAct agent, no orchestration/critic
    def answer(self, query: str, twin: dict | None = None) -> AgentState: ...
```
Both return AgentState-compatible objects so the same graders apply. Mock-deterministic.

## Harness  (`src/finroot/evaluation/harness.py`, `scripts/run_evals.py`)
```python
class HarnessConfig(BaseModel):
    k: int = 3              # pass@k trials
    systems: list[str] = ["finroot", "rag", "single_agent"]
    mock: bool = True

class HarnessResult(BaseModel):
    system: str
    pass_at_1: float
    pass_at_k: float       # at least one of k trials passes
    pass_hat_k: float      # ALL k trials pass (consistency)
    mean_score: float
    per_domain: dict[str, float]
    n_tasks: int

def run_harness(config: HarnessConfig) -> list[HarnessResult]: ...
```
- `scripts/run_evals.py` CLI: `--mock`, `--task <id>` (single), `--k N`, `--system finroot`.
- Writes `results/metrics.json` (the SINGLE source) + per-run transcript to `evals/reports/`.

## metrics.json shape (FM-05/12 — single source)
```python
{
  "as_of_sha": str,
  "generated_at": str,
  "systems": {"finroot": HarnessResult, "rag": ..., "single_agent": ...},
  "composite_lift_vs_rag_pct": float,   # the headline number for the deck
  "n_tasks": int, "k": int
}
```

## report.py  (`src/finroot/evaluation/report.py`)
```python
def generate_report(metrics_path="results/metrics.json") -> str:  # returns markdown
def write_report(out_dir="evals/reports") -> Path: ...
```

## Acceptance anti-patterns to REJECT (don't let graders rubber-stamp)
- An answer that says "guaranteed" / "you will definitely" → must FAIL.
- An answer with zero citations on a numeric claim → must FAIL.
- All-same trivial answers scoring high → grader is broken; spread must be real.

## File map (disjoint write-sets)
| Task | Writes |
|------|--------|
| 01 | `data/gold/frb_questions.json`, `evals/tasks/README.md`, `tests/unit/test_frb_bank.py` |
| 02 | `evals/graders/code_based.py`, `evals/graders/llm_judge.py`, `evals/graders/human_review_template.md`, `evals/graders/__init__.py`, `tests/unit/test_graders.py` |
| 03 | `src/finroot/evaluation/baselines.py`, `tests/unit/test_baselines.py` |
| 04 | `src/finroot/evaluation/harness.py`, `scripts/run_evals.py`, `tests/unit/test_harness.py` |
| 05 | `src/finroot/evaluation/report.py`, `tests/unit/test_eval_report.py` |
