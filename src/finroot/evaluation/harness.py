"""Harness runner — executes the FRB benchmark across FinRoot + baselines.

Computes pass@1 / pass@k / pass^k (consistency) per system, writes the SINGLE
metrics source ``results/metrics.json`` (FM-05/12). Numbers never hand-typed.

Usage:
    from finroot.evaluation.harness import HarnessConfig, run_harness
    results = run_harness(HarnessConfig(k=2, mock=True))
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class HarnessConfig(BaseModel):
    """Configuration for an FRB run."""

    model_config = {"extra": "forbid"}

    k: int = Field(default=2, ge=1, le=5)
    systems: list[str] = Field(default_factory=lambda: ["finroot", "rag", "single_agent"])
    mock: bool = True
    max_tasks: int | None = None  # for fast CI; None = all
    frb_path: str = "data/gold/frb_questions.json"
    metrics_path: str = "results/metrics.json"


class HarnessResult(BaseModel):
    """Per-system results."""

    model_config = {"extra": "forbid"}

    system: str
    pass_at_1: float
    pass_at_k: float  # ≥1 of k trials passes
    pass_hat_k: float  # ALL k trials pass (consistency)
    mean_score: float
    per_domain: dict[str, float] = Field(default_factory=dict)
    per_difficulty: dict[str, float] = Field(default_factory=dict)
    n_tasks: int
    n_trials: int
    elapsed_sec: float


# ---------------------------------------------------------------------------
# System adapters — each returns an AgentState-compatible object.
# ---------------------------------------------------------------------------


def _run_finroot(query: str) -> Any:
    os.environ.setdefault("FINROOT_LLM_PROVIDER", "mock")
    from interface.core import answer  # noqa: PLC0415

    return answer(query, mock=True)


def _run_rag(query: str) -> Any:
    from finroot.evaluation.baselines import NaiveRAGBaseline  # noqa: PLC0415

    return NaiveRAGBaseline().answer(query)


def _run_single_agent(query: str) -> Any:
    from finroot.evaluation.baselines import SingleAgentBaseline  # noqa: PLC0415

    return SingleAgentBaseline().answer(query)


_SYSTEMS = {
    "finroot": _run_finroot,
    "rag": _run_rag,
    "single_agent": _run_single_agent,
}


# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------


def _ensure_final(state: Any) -> Any:
    """Promote candidate → final so graders work uniformly."""
    if getattr(state, "final", None) is None and getattr(state, "candidate", None) is not None:
        state.final = state.candidate
    return state


def _score_one(task: dict, state: Any) -> tuple[bool, float]:
    """Return (passed, score) using the deterministic code grader."""
    from evals.graders.code_based import grade_code  # noqa: PLC0415

    try:
        result = grade_code(task, _ensure_final(state))
        return result.passed, result.score
    except Exception:  # grader raised — treat as fail (FM-11 fail loud upstream)
        return False, 0.0


def _run_system(system: str, tasks: list[dict], k: int) -> HarnessResult:
    fn = _SYSTEMS[system]
    per_task_pass: list[bool] = []
    per_task_scores: list[float] = []
    per_domain_scores: dict[str, list[float]] = {}
    per_difficulty_scores: dict[str, list[float]] = {}
    t0 = time.time()

    for task in tasks:
        trial_results: list[tuple[bool, float]] = []
        for _trial in range(k):
            state = fn(task["query"])
            trial_results.append(_score_one(task, state))
        any_pass = any(r[0] for r in trial_results)
        first_score = trial_results[0][1]
        per_task_pass.append(any_pass)
        per_task_scores.append(first_score)
        per_domain_scores.setdefault(task.get("domain", "unknown"), []).append(first_score)
        per_difficulty_scores.setdefault(task.get("difficulty", "unknown"), []).append(first_score)

    elapsed = time.time() - t0
    n = len(tasks)
    return HarnessResult(
        system=system,
        pass_at_1=sum(1 for p in per_task_pass if p) / n if n else 0.0,
        pass_at_k=sum(1 for p in per_task_pass if p) / n if n else 0.0,
        pass_hat_k=(
            sum(1 for s in per_task_scores if s >= 0.99) / n if n else 0.0
        ),
        mean_score=statistics.mean(per_task_scores) if per_task_scores else 0.0,
        per_domain={d: statistics.mean(v) for d, v in per_domain_scores.items()},
        per_difficulty={d: statistics.mean(v) for d, v in per_difficulty_scores.items()},
        n_tasks=n,
        n_trials=k,
        elapsed_sec=round(elapsed, 2),
    )


def _git_short_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def run_harness(config: HarnessConfig | None = None) -> list[HarnessResult]:
    """Execute the FRB across every configured system and write metrics.json."""
    cfg = config or HarnessConfig()
    tasks = json.loads(Path(cfg.frb_path).read_text())
    if cfg.max_tasks is not None:
        tasks = tasks[: cfg.max_tasks]

    results: list[HarnessResult] = []
    for system in cfg.systems:
        results.append(_run_system(system, tasks, cfg.k))

    finroot_score = next((r.mean_score for r in results if r.system == "finroot"), 0.0)
    rag_score = next((r.mean_score for r in results if r.system == "rag"), 0.0)
    lift_pct = ((finroot_score - rag_score) / max(rag_score, 1e-9)) * 100.0

    payload = {
        "as_of_sha": _git_short_sha(),
        "generated_at": datetime.now(UTC).isoformat(),
        "k": cfg.k,
        "mock": cfg.mock,
        "n_tasks": len(tasks),
        "systems": {r.system: r.model_dump() for r in results},
        "composite_lift_vs_rag_pct": round(lift_pct, 1),
        "composite_lift_vs_rag_x": round(finroot_score / max(rag_score, 1e-9), 2),
        "headline_finroot_mean": round(finroot_score, 3),
        "headline_rag_mean": round(rag_score, 3),
    }

    out = Path(cfg.metrics_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    return results


if __name__ == "__main__":  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser(description="Run FinRoot FRB benchmark")
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--max-tasks", type=int, default=None)
    ap.add_argument("--task", default=None, help="run single task id")
    ap.add_argument("--system", default=None)
    ap.add_argument("--mock", action="store_true", default=True)
    args = ap.parse_args()

    if args.task:
        os.environ["FINROOT_LLM_PROVIDER"] = "mock"
        from evals.graders.code_based import grade_code  # noqa: PLC0415

        from interface.core import answer  # noqa: PLC0415

        tasks = [t for t in json.loads(Path("data/gold/frb_questions.json").read_text()) if t["id"] == args.task]
        if not tasks:
            raise SystemExit(f"task {args.task} not found")
        t = tasks[0]
        state = answer(t["query"], mock=True)
        if state.final is None and state.candidate is not None:
            state.final = state.candidate
        r = grade_code(t, state)
        print(f"{t['id']}: score={r.score:.3f} passed={r.passed}")
        print(f"summary: {state.final.summary[:200] if state.final else '<none>'}")
    else:
        results = run_harness(HarnessConfig(k=args.k, max_tasks=args.max_tasks, mock=True))
        print("wrote results/metrics.json")
        for r in results:
            print(f"  {r.system:14} mean={r.mean_score:.3f}  pass@1={r.pass_at_1:.3f}  pass^k={r.pass_hat_k:.3f}")
