"""Tests for the FRB harness runner (wave-6, task 04).

The harness is the runtime backbone for the 35%-weight Reasoning-Quality
score; its tests must guard every contract invariant listed in
``.specify/specs/wave-6/contracts/evals.contract.md`` plus the headline
"FinRoot beats baselines" promise.

Run with::

    PYTHONPATH=src python3 -m pytest tests/unit/test_harness.py -v

Per the W6-02 gotcha, ``evals.graders`` is a PEP-420 package under ``evals/``
at the repo root, so it is NOT importable with only ``PYTHONPATH=src``. The
harness internally prepends the repo root to ``sys.path``; these tests must
do the same.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Make `evals.graders` importable from this test module.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from finroot.evaluation import harness as harness_mod  # noqa: E402
from finroot.evaluation.harness import (  # noqa: E402
    DEFAULT_FRB_PATH,
    DEFAULT_METRICS_PATH,
    HarnessConfig,
    HarnessResult,
    MetricsReport,
    TrialResult,
    compute_composite_lift,
    run_harness,
    write_metrics,
)
from finroot.schemas.state import AgentState  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _small_config(**overrides: Any) -> HarnessConfig:
    """Build a HarnessConfig tuned for fast tests (small k, single task).

    Uses ``frb-001`` because it requires concrete content (mentions +
    citations) so failures and passes are distinguishable. Override with
    ``task_filter=None`` to run the full bank in slow tests.
    """
    defaults: dict[str, Any] = {
        "k": 2,
        "systems": ["finroot", "rag", "single_agent"],
        "mock": True,
        "frb_path": DEFAULT_FRB_PATH,
        "task_filter": "frb-001",
        "judge_with_llm": False,
        "base_seed": 0,
    }
    defaults.update(overrides)
    return HarnessConfig(**defaults)


def _full_minimal_config(**overrides: Any) -> HarnessConfig:
    """Full-bank config with k=1 for the speed-critical coverage test."""
    defaults: dict[str, Any] = {
        "k": 1,
        "systems": ["finroot", "rag", "single_agent"],
        "mock": True,
        "frb_path": DEFAULT_FRB_PATH,
    }
    defaults.update(overrides)
    return HarnessConfig(**defaults)


@pytest.fixture
def tmp_metrics_path(tmp_path: Path) -> Path:
    """Per-test metrics.json target — never write to the real results/."""
    return tmp_path / "metrics.json"


# ---------------------------------------------------------------------------
# 1. Loader & seed helpers
# ---------------------------------------------------------------------------


class TestLoaders:
    def test_load_frb_returns_list(self) -> None:
        tasks = harness_mod._load_frb(DEFAULT_FRB_PATH)
        assert isinstance(tasks, list)
        assert len(tasks) >= 24

    def test_load_frb_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            harness_mod._load_frb(tmp_path / "no_such_file.json")

    def test_load_frb_malformed_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError, match="not valid JSON"):
            harness_mod._load_frb(bad)

    def test_load_frb_wrong_shape_raises(self, tmp_path: Path) -> None:
        wrong = tmp_path / "wrong.json"
        wrong.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON array"):
            harness_mod._load_frb(wrong)

    def test_load_twins_empty_when_missing(self, tmp_path: Path) -> None:
        twins = harness_mod._load_twins(tmp_path / "no_twins.json")
        assert twins == {}

    def test_load_twins_handles_malformed(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad_twins.json"
        bad.write_text("not json", encoding="utf-8")
        # Graceful: empty dict, not exception.
        assert harness_mod._load_twins(bad) == {}

    def test_seed_suffix_is_deterministic(self) -> None:
        a = harness_mod._seed_suffix(0, base_seed=0)
        b = harness_mod._seed_suffix(0, base_seed=0)
        assert a == b
        assert "trial_seed=" in a

    def test_seed_suffix_varies_by_trial(self) -> None:
        assert harness_mod._seed_suffix(0, 0) != harness_mod._seed_suffix(1, 0)

    def test_seed_suffix_varies_by_base_seed(self) -> None:
        assert harness_mod._seed_suffix(0, 0) != harness_mod._seed_suffix(0, 1)


# ---------------------------------------------------------------------------
# 2. run_harness — core behaviour
# ---------------------------------------------------------------------------


class TestRunHarness:
    def test_returns_results_for_each_system(self) -> None:
        results = run_harness(_small_config())
        systems = {r.system for r in results}
        assert systems == {"finroot", "rag", "single_agent"}

    def test_single_task_returns_three_rows(self) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        # 1 task × 3 systems × k trials aggregated → 3 system rows
        assert len(results) == 3

    def test_every_result_has_required_fields(self) -> None:
        results = run_harness(_small_config())
        for r in results:
            assert isinstance(r, HarnessResult)
            assert 0.0 <= r.pass_at_1 <= 1.0
            assert 0.0 <= r.pass_at_k <= 1.0
            assert 0.0 <= r.pass_hat_k <= 1.0
            assert 0.0 <= r.mean_score <= 1.0
            assert r.n_tasks >= 0
            assert isinstance(r.per_domain, dict)

    def test_n_tasks_matches_filter(self) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        for r in results:
            assert r.n_tasks == 1

    def test_task_filter_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="No FRB task matches"):
            run_harness(_small_config(task_filter="frb-does-not-exist"))

    def test_system_filter_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown system"):
            run_harness(_small_config(system_filter="not_a_system"))

    def test_system_filter_restricts_to_one(self) -> None:
        results = run_harness(_small_config(system_filter="rag"))
        assert len(results) == 1
        assert results[0].system == "rag"


# ---------------------------------------------------------------------------
# 3. Invariants (the contract's hard guarantees)
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_pass_k_le_1(self) -> None:
        """pass@k is a fraction → ≤ 1.0 always."""
        results = run_harness(_small_config())
        for r in results:
            assert r.pass_at_k <= 1.0 + 1e-9, f"{r.system}: pass@k={r.pass_at_k}"

    def test_pass_hat_k_le_pass_at_k(self) -> None:
        """pass^k ≤ pass@k (consistency can't exceed any-pass)."""
        results = run_harness(_small_config())
        for r in results:
            assert r.pass_hat_k <= r.pass_at_k + 1e-9, (
                f"{r.system}: pass^k={r.pass_hat_k} > pass@k={r.pass_at_k}"
            )

    def test_pass_at_1_le_pass_at_k(self) -> None:
        """pass@1 (first trial) can't exceed pass@k (any trial)."""
        results = run_harness(_small_config())
        for r in results:
            assert r.pass_at_1 <= r.pass_at_k + 1e-9, (
                f"{r.system}: pass@1={r.pass_at_1} > pass@k={r.pass_at_k}"
            )

    def test_per_domain_values_in_unit_interval(self) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        for r in results:
            for d, v in r.per_domain.items():
                assert 0.0 <= v <= 1.0, f"{r.system}.{d}={v}"


# ---------------------------------------------------------------------------
# 4. The headline promise — FinRoot beats RAG
# ---------------------------------------------------------------------------


class TestFinRootBeatsRAG:
    def test_finroot_meets_or_exceeds_rag(self) -> None:
        """The whole point of the harness — surface loudly if it fails."""
        results = run_harness(_small_config(task_filter="frb-001"))
        by_sys = {r.system: r for r in results}
        assert "finroot" in by_sys and "rag" in by_sys
        finroot_score = by_sys["finroot"].mean_score
        rag_score = by_sys["rag"].mean_score
        # If this assertion fires, the pipeline or graders are broken.
        assert finroot_score + 1e-9 >= rag_score, (
            f"FinRoot underperforms RAG: finroot={finroot_score:.4f} "
            f"< rag={rag_score:.4f}"
        )

    def test_composite_lift_is_nonnegative_when_finroot_wins(self) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        lift = compute_composite_lift(results)
        # The lift is finroot vs rag. We asserted finroot >= rag above,
        # so the lift (as a percentage of rag) should be ≥ 0.
        assert lift >= -1e-9, f"Lift unexpectedly negative: {lift}"

    def test_composite_lift_zero_when_rag_missing(self) -> None:
        # No RAG in the system list → lift is undefined → 0.0 (no raise).
        results = run_harness(_small_config(systems=["finroot"]))
        assert compute_composite_lift(results) == 0.0


# ---------------------------------------------------------------------------
# 5. metrics.json write — single source for all numbers
# ---------------------------------------------------------------------------


class TestWriteMetrics:
    def test_write_metrics_creates_file(self, tmp_metrics_path: Path) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        report = write_metrics(
            results,
            path=tmp_metrics_path,
            k=2,
            n_tasks=1,
        )
        assert tmp_metrics_path.exists()
        assert isinstance(report, MetricsReport)

    def test_metrics_json_has_required_keys(self, tmp_metrics_path: Path) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        write_metrics(results, path=tmp_metrics_path, k=2, n_tasks=1)
        data = json.loads(tmp_metrics_path.read_text(encoding="utf-8"))

        for key in (
            "as_of_sha",
            "generated_at",
            "systems",
            "composite_lift_vs_rag_pct",
            "n_tasks",
            "k",
        ):
            assert key in data, f"missing required key: {key}"

        assert isinstance(data["as_of_sha"], str)
        assert isinstance(data["generated_at"], str)
        assert data["k"] == 2
        assert data["n_tasks"] == 1
        # All three systems present in the file.
        assert set(data["systems"].keys()) == {"finroot", "rag", "single_agent"}

    def test_metrics_systems_match_harness_result_shape(
        self, tmp_metrics_path: Path
    ) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        write_metrics(results, path=tmp_metrics_path, k=2, n_tasks=1)
        data = json.loads(tmp_metrics_path.read_text(encoding="utf-8"))
        for sys_name, sys_data in data["systems"].items():
            for key in (
                "system",
                "pass_at_1",
                "pass_at_k",
                "pass_hat_k",
                "mean_score",
                "per_domain",
                "n_tasks",
            ):
                assert key in sys_data, f"{sys_name}.{key} missing"

    def test_metrics_git_sha_is_string(self, tmp_metrics_path: Path) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        write_metrics(results, path=tmp_metrics_path, k=2, n_tasks=1)
        data = json.loads(tmp_metrics_path.read_text(encoding="utf-8"))
        # Either a hex-ish short sha OR "unknown" — never null/None.
        assert data["as_of_sha"] is not None
        assert isinstance(data["as_of_sha"], str)


# ---------------------------------------------------------------------------
# 6. Single-task mode (CLI surface)
# ---------------------------------------------------------------------------


class TestSingleTaskMode:
    def test_single_task_n_tasks_is_one(self) -> None:
        results = run_harness(_small_config(task_filter="frb-001"))
        for r in results:
            assert r.n_tasks == 1

    def test_single_task_per_domain_has_one_key(self) -> None:
        # frb-001 is portfolio domain.
        results = run_harness(_small_config(task_filter="frb-001"))
        for r in results:
            assert "portfolio" in r.per_domain

    def test_cli_single_task_runs(self) -> None:
        """The CLI's --task mode must produce a transcript + metrics.json."""
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_evals.py",
                "--mock",
                "--task",
                "frb-001",
                "--k",
                "1",
                "--out",
                str(DEFAULT_METRICS_PATH),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"CLI failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        # Metrics file must exist and contain the single-task subset.
        assert DEFAULT_METRICS_PATH.exists()
        data = json.loads(DEFAULT_METRICS_PATH.read_text(encoding="utf-8"))
        assert data["n_tasks"] == 1
        assert "finroot" in data["systems"]

    def test_cli_full_runs(self) -> None:
        """The CLI's full-bank mode produces the canonical metrics.json."""
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_evals.py",
                "--mock",
                "--k",
                "1",
                "--out",
                str(DEFAULT_METRICS_PATH),
            ],
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"CLI failed:\nSTDOUT:\n{result.stdout[:2000]}\nSTDERR:\n{result.stderr[:2000]}"
        )
        assert DEFAULT_METRICS_PATH.exists()
        data = json.loads(DEFAULT_METRICS_PATH.read_text(encoding="utf-8"))
        assert data["n_tasks"] >= 24  # contract: ≥ 24 questions


# ---------------------------------------------------------------------------
# 7. TrialResult aggregation
# ---------------------------------------------------------------------------


class TestAggregation:
    def test_aggregate_empty_trials(self) -> None:
        results = harness_mod._aggregate([], ["rag"], k=3)
        assert len(results) == 1
        assert results[0].system == "rag"
        assert results[0].n_tasks == 0
        assert results[0].mean_score == 0.0

    def test_aggregate_pass_k_invariant(self) -> None:
        """Manually constructed trials: pass@k ≥ pass^k, both ≤ 1."""
        trials = [
            TrialResult(
                system="rag",
                task_id="t1",
                domain="x",
                trial=0,
                passed=True,
                score=0.7,
            ),
            TrialResult(
                system="rag",
                task_id="t1",
                domain="x",
                trial=1,
                passed=False,
                score=0.4,
            ),
            TrialResult(
                system="rag",
                task_id="t2",
                domain="x",
                trial=0,
                passed=False,
                score=0.2,
            ),
            TrialResult(
                system="rag",
                task_id="t2",
                domain="x",
                trial=1,
                passed=False,
                score=0.3,
            ),
        ]
        results = harness_mod._aggregate(trials, ["rag"], k=2)
        assert len(results) == 1
        r = results[0]
        # t1: pass@1=True (first trial), pass@k=True (≥1 passes), pass^k=False
        # t2: pass@1=False, pass@k=False, pass^k=False
        assert r.pass_at_1 == 0.5  # 1 of 2 tasks
        assert r.pass_at_k == 0.5  # 1 of 2 tasks
        assert r.pass_hat_k == 0.0  # 0 of 2 tasks
        assert r.mean_score == pytest.approx((0.7 + 0.4 + 0.2 + 0.3) / 4, abs=1e-6)


# ---------------------------------------------------------------------------
# 8. TrialResult model contract
# ---------------------------------------------------------------------------


class TestTrialResultContract:
    def test_extra_forbid(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TrialResult(
                system="rag",
                task_id="t1",
                domain="x",
                trial=0,
                passed=True,
                score=0.5,
                evil="extra",
            )

    def test_default_breakdown_is_empty_dict(self) -> None:
        tr = TrialResult(
            system="rag",
            task_id="t1",
            domain="x",
            trial=0,
            passed=True,
            score=0.5,
        )
        assert tr.grader_breakdown == {}


# ---------------------------------------------------------------------------
# 9. Defensive behaviour
# ---------------------------------------------------------------------------


class TestDefensive:
    def test_state_with_no_final_does_not_crash(self) -> None:
        """A trial whose state has no final recommendation must score 0.0, not raise."""
        # Construct a state with final=None to mimic the orchestrator's
        # current behaviour (candidate populated, final None).
        state = AgentState(query="x")
        score, passed, breakdown = harness_mod._grade_trial(
            {"id": "t", "query": "x", "domain": "x", "expected": {}}, state
        )
        assert score == 0.0
        assert passed is False
        assert "error" in breakdown

    def test_unknown_system_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown system"):
            harness_mod._run_system("not_real", "x", None, None)

    def test_unknown_baseline_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown baseline"):
            harness_mod._run_baseline("not_real", "x", None)

    def test_repo_root_on_path_idempotent(self) -> None:
        before = sys.path[:]
        harness_mod._ensure_repo_root_on_path()
        harness_mod._ensure_repo_root_on_path()
        # Net effect: nothing duplicated, repo root still present.
        assert sys.path.count(str(REPO_ROOT)) == 1
        sys.path[:] = before