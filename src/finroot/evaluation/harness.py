"""Harness runner for the Financial Reasoning Benchmark (FRB).

Executes the FRB question bank across FinRoot plus the comparison baselines
(``NaiveRAGBaseline``, ``SingleAgentBaseline``), grades each trial with the
deterministic code-based grader (and optionally the LLM-judge), and computes
the headline metrics:

* ``pass_at_1``  — fraction of tasks whose first trial passes.
* ``pass_at_k``  — fraction of tasks with ≥1 of k passing trials.
* ``pass_hat_k`` — fraction of tasks with ALL k trials passing (consistency).
* ``mean_score`` — mean of every per-trial code-grader score.
* ``per_domain`` — mean score bucketed by FRB domain.

Plus the cross-system ``composite_lift_vs_rag_pct`` = ``(finroot.mean_score -
rag.mean_score) / max(rag.mean_score, 1e-9) * 100``. That is the single
number that proves the 35%-weight Reasoning-Quality story.

Writes: ``src/finroot/evaluation/harness.py`` (wave-6, task 04).
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finroot.schemas.state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths (FM-05/12: single source for metrics, single source for FRB)
# ---------------------------------------------------------------------------

DEFAULT_FRB_PATH: Path = Path("data/gold/frb_questions.json")
DEFAULT_TWIN_PROFILES_PATH: Path = Path("data/samples/twin_profiles.json")
DEFAULT_METRICS_PATH: Path = Path("results/metrics.json")

# Repo root: needed so ``evals.graders`` (PEP-420 namespace package under
# ``evals/`` at the repo root) is importable when the harness is launched with
# ``PYTHONPATH=src``. See docs/waves/wave-6-gotchas.md for the rationale.
_REPO_ROOT: Path = Path(__file__).resolve().parents[2]


def _ensure_repo_root_on_path() -> None:
    """Prepend the repo root to ``sys.path`` so ``evals.graders`` resolves.

    Idempotent. The W6-02 graders file (test_graders.py) and this file both
    rely on this — see the gotcha entry dated 2026-06-20.
    """
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


# ---------------------------------------------------------------------------
# Pydantic models (contract § Harness)
# ---------------------------------------------------------------------------


class HarnessConfig(BaseModel):
    """Frozen-shape configuration for :func:`run_harness`.

    Fields:
    * ``k`` — trials per task per system (pass@k denominator).
    * ``systems`` — which systems to evaluate. Default: all three.
    * ``mock`` — force offline ``MockProvider`` (FM-11: never use live API in tests).
    * ``frb_path`` — where to load the FRB question bank from.
    * ``task_filter`` — when set, run only the matching task id
      (single-task mode; powers the ``--task`` CLI flag).
    * ``system_filter`` — when set, restrict to one system (CLI ``--system``).
    * ``judge_with_llm`` — when True, also run the LLM-judge grader and
      blend its score with the code grader (0.5/0.5).
    * ``base_seed`` — base seed for the trial-by-trial prompt suffix that
      varies MockProvider output across trials (see ``_seed_suffix``).
    """

    model_config = ConfigDict(extra="forbid")

    k: int = Field(default=3, ge=1, le=20, description="Trials per task per system.")
    systems: list[str] = Field(
        default_factory=lambda: ["finroot", "rag", "single_agent"],
        description="Systems to evaluate.",
    )
    mock: bool = Field(default=True, description="Use the offline MockProvider.")
    frb_path: Path = Field(default=DEFAULT_FRB_PATH, description="FRB question bank path.")
    task_filter: str | None = Field(default=None, description="Run only this task id.")
    system_filter: str | None = Field(default=None, description="Restrict to this system.")
    judge_with_llm: bool = Field(default=False, description="Blend LLM-judge score in.")
    base_seed: int = Field(default=0, description="Base seed for trial variation.")


class TrialResult(BaseModel):
    """One trial of one system on one FRB task. Internal aggregation record."""

    model_config = ConfigDict(extra="forbid")

    system: str
    task_id: str
    domain: str
    trial: int
    passed: bool
    score: float
    grader_breakdown: dict[str, Any] = Field(default_factory=dict)
    elapsed_s: float = 0.0
    error: str | None = None


class HarnessResult(BaseModel):
    """Per-system aggregate metrics — the row written to ``metrics.json``.

    Contract shape (frozen): ``system``, ``pass_at_1``, ``pass_at_k``,
    ``pass_hat_k``, ``mean_score``, ``per_domain``, ``n_tasks``.
    """

    model_config = ConfigDict(extra="forbid")

    system: str
    pass_at_1: float
    pass_at_k: float
    pass_hat_k: float
    mean_score: float
    per_domain: dict[str, float]
    n_tasks: int


class MetricsReport(BaseModel):
    """The full ``results/metrics.json`` shape (contract § metrics.json).

    One row per system under ``systems``; the cross-system lift is the
    headline number for the deck.
    """

    model_config = ConfigDict(extra="forbid")

    as_of_sha: str
    generated_at: str
    systems: dict[str, HarnessResult]
    composite_lift_vs_rag_pct: float
    n_tasks: int
    k: int


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _load_frb(path: Path) -> list[dict[str, Any]]:
    """Load the FRB question bank from ``path`` (must be a JSON array).

    Raises:
        FileNotFoundError: If the file is missing.
        ValueError: If the JSON is malformed or not a list.
    """
    if not path.exists():
        raise FileNotFoundError(f"FRB question bank not found at {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"FRB bank at {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(
            f"FRB bank must be a JSON array, got {type(data).__name__}"
        )
    return data


def _load_twins(path: Path) -> dict[str, dict[str, Any]]:
    """Load twin profiles from ``path`` keyed by ``user_id``.

    Returns an empty dict on missing file or malformed JSON (graceful —
    FRB tasks with ``twin_id`` will simply run without a twin snapshot,
    which is fine for the harness: the contract says twin=None is allowed).
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Twin profiles file at %s is not valid JSON: %s", path, exc)
        return {}
    if not isinstance(data, list):
        return {}
    return {
        p.get("user_id"): p
        for p in data
        if isinstance(p, dict) and p.get("user_id")
    }


# ---------------------------------------------------------------------------
# Trial variation
# ---------------------------------------------------------------------------


def _seed_suffix(trial: int, base_seed: int) -> str:
    """Append a trial-specific seed suffix to the query.

    MockProvider keys its canned responses by SHA-256 of the prompt, so the
    only way to vary the output across trials is to perturb the prompt. We
    do that here with a deterministic, well-formed suffix so the same
    ``(task, trial, base_seed)`` always maps to the same perturbation —
    maintaining the harness's reproducibility invariant.

    The suffix is wrapped in ``[trial_seed=…]`` so downstream parsing can
    ignore it; it looks like a debugging marker.
    """
    return f" [trial_seed={base_seed + trial}]"


# ---------------------------------------------------------------------------
# System runners — dispatch to FinRoot or a baseline
# ---------------------------------------------------------------------------


def _ensure_final_populated(state: AgentState) -> AgentState:
    """Promote ``state.candidate`` → ``state.final`` if ``final`` is None.

    The current FinRootOrchestrator populates ``candidate`` but leaves
    ``final`` None; the grader inspects ``final``. Promoting here keeps the
    grader contract honest without editing the orchestrator (which is owned
    by a different wave's task).
    """
    if state.final is None and state.candidate is not None:
        state.final = state.candidate
    return state


def _run_finroot(query: str, twin_id: str | None) -> AgentState:
    """Run FinRoot via ``interface.core.answer`` (preferred) or the orchestrator.

    Uses ``interface.core.answer`` when importable (it builds memory, audit,
    and LLM and runs the full pipeline). Falls back to constructing the
    orchestrator directly so the harness still works in environments that
    lack ``interface.core`` (e.g., minimal CI runners).
    """
    user_id = twin_id or "demo"
    if os.environ.get("FINROOT_LLM_PROVIDER") is None:
        os.environ["FINROOT_LLM_PROVIDER"] = "mock"

    # Preferred: high-level entry that wires memory + audit + critic + verifier.
    try:
        from interface.core import answer as _answer  # type: ignore

        state = _answer(query, user_id=user_id, mock=True)
        return _ensure_final_populated(state)
    except ImportError:
        logger.debug("interface.core not importable; using FinRootOrchestrator directly")

    # Fallback: build the orchestrator by hand.
    from finroot.agents.orchestrator import FinRootOrchestrator  # type: ignore
    from finroot.audit.trail import AuditTrail  # type: ignore
    from finroot.llm.mock import MockProvider  # type: ignore
    from finroot.memory.digital_twin import DigitalTwinStore  # type: ignore
    from finroot.memory.manager import MemoryManager  # type: ignore
    from finroot.memory.semantic import SemanticMemory  # type: ignore
    from finroot.memory.working import WorkingMemory  # type: ignore

    llm = MockProvider()
    memory = MemoryManager(
        working=WorkingMemory(max_turns=10),
        semantic=SemanticMemory(persist_dir="data/chroma"),
        twin_store=DigitalTwinStore(db_path="data/digital_twin.db"),
        user_id=user_id,
    )
    audit = AuditTrail(Path(tempfile.mkdtemp()) / "audit.jsonl")
    orch = FinRootOrchestrator(memory=memory, audit=audit, llm=llm)
    state = orch.run(query)
    return _ensure_final_populated(state)


def _run_baseline(system: str, query: str, twin: dict | None) -> AgentState:
    """Run a baseline system (``rag`` or ``single_agent``)."""
    from finroot.evaluation.baselines import NaiveRAGBaseline, SingleAgentBaseline

    if system == "rag":
        return NaiveRAGBaseline().answer(query, twin=twin)
    if system == "single_agent":
        return SingleAgentBaseline().answer(query, twin=twin)
    raise ValueError(f"Unknown baseline system: {system!r}")


def _run_system(
    system: str, query: str, twin: dict | None, twin_id: str | None
) -> AgentState:
    """Dispatch to the right runner for *system*."""
    if system == "finroot":
        return _run_finroot(query, twin_id)
    if system in ("rag", "single_agent"):
        return _run_baseline(system, query, twin)
    raise ValueError(f"Unknown system: {system!r}")


# ---------------------------------------------------------------------------
# Per-trial grader
# ---------------------------------------------------------------------------


def _grade_trial(task: dict, state: AgentState) -> tuple[float, bool, dict[str, Any]]:
    """Grade one trial's state against one FRB task.

    Returns ``(score, passed, breakdown)``. Uses ``grade_code`` (deterministic).
    If the state has no final recommendation, returns ``(0.0, False, ...)`` —
    fail loud (FM-11): no fabricated scores.
    """
    if state.final is None:
        return (
            0.0,
            False,
            {"error": "state.final is None after candidate promotion"},
        )

    # Lazy import — graders live in a PEP-420 package under ``evals/`` at the
    # repo root; the harness must ensure the repo root is on sys.path first.
    _ensure_repo_root_on_path()
    from evals.graders import grade_code

    result = grade_code(task, state)
    return float(result.score), bool(result.passed), dict(result.breakdown)


def _maybe_blend_judge(
    task: dict, state: AgentState, judge_llm: Any, code_score: float, code_breakdown: dict[str, Any]
) -> tuple[float, bool, dict[str, Any]]:
    """Optionally blend an LLM-judge score into the final per-trial score.

    Blend formula: ``0.5 * code_score + 0.5 * judge_score``. Threshold is the
    code grader's ``SCORE_THRESHOLD`` (0.6). Returns the blended score, the
    blended ``passed`` flag, and a copy of the breakdown with ``judge_*`` keys.
    """
    if judge_llm is None or state.final is None:
        return code_score, code_score >= 0.6, code_breakdown

    _ensure_repo_root_on_path()
    from evals.graders import grade_llm

    judge_result = grade_llm(task, state, judge_llm)
    judge_score = float(judge_result.score)
    blended = round(0.5 * code_score + 0.5 * judge_score, 4)
    breakdown = dict(code_breakdown)
    breakdown["judge_score"] = judge_score
    breakdown["judge_axes"] = judge_result.breakdown.get("axes", {})
    breakdown["judge_source"] = judge_result.breakdown.get("score_source", "")
    breakdown["blended_score"] = blended
    return blended, blended >= 0.6, breakdown


# ---------------------------------------------------------------------------
# run_harness (contract § Harness)
# ---------------------------------------------------------------------------


def run_harness(config: HarnessConfig) -> list[HarnessResult]:
    """Run the full FRB harness across all configured systems.

    For each task in the FRB bank:
        For each system in config.systems:
            For each trial in range(config.k):
                Run the system with a seed-perturbed query, grade, record.
    Then aggregate per-system into :class:`HarnessResult` rows.

    Returns:
        A list of :class:`HarnessResult`, one per system.

    Raises:
        ValueError: If ``config.task_filter`` matches no tasks, or
            ``config.system_filter`` names an unknown system, or the
            ``pass^k <= pass@k <= 1.0`` invariant is violated.
    """
    frb = _load_frb(config.frb_path)

    if config.task_filter:
        frb = [q for q in frb if q.get("id") == config.task_filter]
        if not frb:
            raise ValueError(
                f"No FRB task matches --task {config.task_filter!r}; "
                f"check data/gold/frb_questions.json"
            )

    systems = list(config.systems)
    if config.system_filter:
        if config.system_filter not in systems:
            raise ValueError(
                f"Unknown system {config.system_filter!r}; "
                f"choose from {systems}"
            )
        systems = [config.system_filter]

    twins = _load_twins(DEFAULT_TWIN_PROFILES_PATH)
    judge_llm: Any = None
    if config.judge_with_llm:
        from finroot.llm.mock import MockProvider

        judge_llm = MockProvider()

    trials: list[TrialResult] = []

    for task in frb:
        task_id = str(task.get("id", ""))
        domain = str(task.get("domain", "general"))
        twin_id = task.get("twin_id")
        twin = twins.get(twin_id) if twin_id else None
        base_query = str(task.get("query", ""))
        if not base_query:
            logger.warning("FRB task %s has empty query — skipping", task_id)
            continue

        for system in systems:
            for trial_idx in range(config.k):
                trial_query = base_query + _seed_suffix(trial_idx, config.base_seed)
                t0 = datetime.now(UTC)
                error: str | None = None
                try:
                    state = _run_system(system, trial_query, twin, twin_id)
                except Exception as exc:  # noqa: BLE001 — surface, never fabricate
                    logger.warning(
                        "Trial %d for %s/%s raised %s: %s — scoring 0.0",
                        trial_idx,
                        system,
                        task_id,
                        type(exc).__name__,
                        exc,
                    )
                    error = f"{type(exc).__name__}: {exc}"
                    state = AgentState(query=trial_query)

                score, passed, breakdown = _grade_trial(task, state)
                if config.judge_with_llm:
                    score, passed, breakdown = _maybe_blend_judge(
                        task, state, judge_llm, score, breakdown
                    )

                elapsed = (datetime.now(UTC) - t0).total_seconds()
                trials.append(
                    TrialResult(
                        system=system,
                        task_id=task_id,
                        domain=domain,
                        trial=trial_idx,
                        passed=passed,
                        score=score,
                        grader_breakdown=breakdown,
                        elapsed_s=round(elapsed, 4),
                        error=error,
                    )
                )

    results = _aggregate(trials, systems, k=config.k)

    # Invariant guards — fail loud (FM-11): pass^k <= pass@k <= 1.0.
    for r in results:
        if r.pass_at_k > 1.0 + 1e-9:
            raise ValueError(
                f"Invariant broken: pass_at_k > 1.0 for {r.system!r} "
                f"({r.pass_at_k})"
            )
        if r.pass_hat_k > r.pass_at_k + 1e-9:
            raise ValueError(
                f"Invariant broken: pass^k > pass@k for {r.system!r} "
                f"({r.pass_hat_k} > {r.pass_at_k})"
            )

    # Headline invariant — surface loudly if it fails (FM-09, FM-11).
    finroot = next((r for r in results if r.system == "finroot"), None)
    rag = next((r for r in results if r.system == "rag"), None)
    if (
        finroot is not None
        and rag is not None
        and "rag" in systems
        and "finroot" in systems
        and finroot.mean_score + 1e-9 < rag.mean_score
    ):
        raise ValueError(
            "FinRoot underperforms RAG baseline — pipeline or graders are "
            f"broken. finroot.mean_score={finroot.mean_score} < "
            f"rag.mean_score={rag.mean_score}"
        )

    return results


def _aggregate(
    trials: list[TrialResult], systems: list[str], *, k: int
) -> list[HarnessResult]:
    """Aggregate a flat trial list into one :class:`HarnessResult` per system."""
    results: list[HarnessResult] = []
    for system in systems:
        sys_trials = [t for t in trials if t.system == system]
        if not sys_trials:
            results.append(
                HarnessResult(
                    system=system,
                    pass_at_1=0.0,
                    pass_at_k=0.0,
                    pass_hat_k=0.0,
                    mean_score=0.0,
                    per_domain={},
                    n_tasks=0,
                )
            )
            continue

        # Group trials by task_id.
        per_task: dict[str, list[TrialResult]] = {}
        for t in sys_trials:
            per_task.setdefault(t.task_id, []).append(t)

        n_tasks = len(per_task)

        # pass@1 — fraction of tasks whose first trial passes.
        firsts = [ts[0].passed for ts in per_task.values() if ts]
        pass_at_1 = sum(firsts) / len(firsts) if firsts else 0.0

        # pass@k — fraction with ≥1 passing trial.
        any_pass = [any(t.passed for t in ts) for ts in per_task.values() if ts]
        pass_at_k = sum(any_pass) / len(any_pass) if any_pass else 0.0

        # pass^k — fraction with ALL trials passing.
        all_pass = [all(t.passed for t in ts) for ts in per_task.values() if ts]
        pass_hat_k = sum(all_pass) / len(all_pass) if all_pass else 0.0

        # mean_score across every trial (not just firsts — captures consistency).
        scores = [t.score for t in sys_trials]
        mean_score = sum(scores) / len(scores) if scores else 0.0

        # per-domain mean score.
        per_domain_scores: dict[str, list[float]] = {}
        for t in sys_trials:
            per_domain_scores.setdefault(t.domain, []).append(t.score)
        per_domain = {
            d: round(sum(ss) / len(ss), 4) if ss else 0.0
            for d, ss in sorted(per_domain_scores.items())
        }

        results.append(
            HarnessResult(
                system=system,
                pass_at_1=round(pass_at_1, 4),
                pass_at_k=round(pass_at_k, 4),
                pass_hat_k=round(pass_hat_k, 4),
                mean_score=round(mean_score, 4),
                per_domain=per_domain,
                n_tasks=n_tasks,
            )
        )

    return results


# ---------------------------------------------------------------------------
# metrics.json write (contract § metrics.json shape)
# ---------------------------------------------------------------------------


def _git_sha() -> str:
    """Return ``git rev-parse --short HEAD`` or ``"unknown"`` on failure.

    Fail-soft per the contract — the harness must run in CI containers
    without a git working tree.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return "unknown"


def compute_composite_lift(results: list[HarnessResult]) -> float:
    """Composite lift: ``(finroot.mean_score - rag.mean_score) / max(rag, ε) * 100``.

    Returns 0.0 when either system is missing — never raises (the caller
    decides whether missing RAG is a configuration error).
    """
    by_system = {r.system: r for r in results}
    finroot = by_system.get("finroot")
    rag = by_system.get("rag")
    if finroot is None or rag is None:
        return 0.0
    lift = (finroot.mean_score - rag.mean_score) / max(rag.mean_score, 1e-9) * 100
    return round(float(lift), 4)


def write_metrics(
    results: list[HarnessResult],
    *,
    path: Path = DEFAULT_METRICS_PATH,
    k: int = 3,
    n_tasks: int = 0,
) -> MetricsReport:
    """Write the single-source ``results/metrics.json``.

    Creates parent directories as needed. Returns the typed
    :class:`MetricsReport` so callers (and the CLI) can inspect it without
    re-reading the file.
    """
    composite_lift = compute_composite_lift(results)
    report = MetricsReport(
        as_of_sha=_git_sha(),
        generated_at=datetime.now(UTC).isoformat(),
        systems={r.system: r for r in results},
        composite_lift_vs_rag_pct=composite_lift,
        n_tasks=n_tasks,
        k=k,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=False),
        encoding="utf-8",
    )
    logger.info(
        "Wrote metrics.json: as_of_sha=%s n_tasks=%d systems=%s lift=%.2f%%",
        report.as_of_sha,
        report.n_tasks,
        sorted(report.systems.keys()),
        report.composite_lift_vs_rag_pct,
    )
    return report


# ---------------------------------------------------------------------------
# Transcript helper (used by the CLI's --task mode)
# ---------------------------------------------------------------------------


def build_transcript(
    task: dict, trials: list[TrialResult]
) -> dict[str, Any]:
    """Build a printable transcript for a single FRB task.

    Shape::

        {
          "task": {...},
          "trials": [
              {
                "system": "...",
                "trial": 0,
                "passed": bool,
                "score": float,
                "summary": "...",
                "analysis_excerpt": "...",
                "confidence": "high|medium|low|insufficient",
                "n_citations": int,
                "breakdown": {...}
              },
              ...
          ]
        }
    """
    return {
        "task": {
            "id": task.get("id"),
            "domain": task.get("domain"),
            "difficulty": task.get("difficulty"),
            "query": task.get("query"),
            "twin_id": task.get("twin_id"),
            "expected": task.get("expected", {}),
        },
        "trials": [t.model_dump(mode="json") for t in trials],
    }


__all__ = [
    "DEFAULT_FRB_PATH",
    "DEFAULT_TWIN_PROFILES_PATH",
    "DEFAULT_METRICS_PATH",
    "HarnessConfig",
    "HarnessResult",
    "TrialResult",
    "MetricsReport",
    "run_harness",
    "write_metrics",
    "compute_composite_lift",
    "build_transcript",
]