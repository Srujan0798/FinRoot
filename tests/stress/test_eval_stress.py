"""Stress tests for the FinRoot eval pipeline.

Catches:
- Race conditions when multiple eval runs hit the same paths simultaneously
- Resource exhaustion (memory, file handles) with very large inputs
- Idempotency: running the same eval twice should produce the same numbers

These are slow (each test takes seconds to minutes); not part of the default
test run. Marked @pytest.mark.stress; use `pytest -m stress` to run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.stress
def test_eval_is_idempotent(tmp_path: Path) -> None:
    """Running the eval twice with the same config should produce identical
    mean_scores (modulo the as_of_sha timestamp)."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["FINROOT_METRICS_PATH"] = str(tmp_path / "metrics_run1.json")
    result1 = subprocess.run(
        [sys.executable, "scripts/run_evals.py", "--mock", "--task", "frb-001", "--k", "1"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd=REPO_ROOT,
    )
    assert result1.returncode == 0, f"Run 1 failed: {result1.stderr}"

    data1 = json.loads((tmp_path / "metrics_run1.json").read_text())

    env["FINROOT_METRICS_PATH"] = str(tmp_path / "metrics_run2.json")
    result2 = subprocess.run(
        [sys.executable, "scripts/run_evals.py", "--mock", "--task", "frb-001", "--k", "1"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd=REPO_ROOT,
    )
    assert result2.returncode == 0, f"Run 2 failed: {result2.stderr}"

    data2 = json.loads((tmp_path / "metrics_run2.json").read_text())
    for sys_name in ("finroot", "rag", "single_agent"):
        assert (
            data1["systems"][sys_name]["mean_score"] == data2["systems"][sys_name]["mean_score"]
        ), f"{sys_name} mean_score differs across runs (not idempotent)"


@pytest.mark.stress
def test_concurrent_evals_no_corruption(tmp_path: Path) -> None:
    """Run 4 eval instances in parallel, each writing to its own output path.
    All 4 should succeed and produce identical scores (no cross-contamination)."""
    env_base = os.environ.copy()
    env_base["PYTHONPATH"] = "src"

    def run_one(i: int) -> tuple[int, float]:
        env = env_base.copy()
        env["FINROOT_METRICS_PATH"] = str(tmp_path / f"metrics_concurrent_{i}.json")
        result = subprocess.run(
            [sys.executable, "scripts/run_evals.py", "--mock", "--task", "frb-001", "--k", "1"],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd=REPO_ROOT,
        )
        data = json.loads((tmp_path / f"metrics_concurrent_{i}.json").read_text())
        return result.returncode, data["systems"]["finroot"]["mean_score"]

    start = time.time()
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run_one, i) for i in range(4)]
        results = [f.result() for f in as_completed(futures)]
    elapsed = time.time() - start

    # All 4 should succeed with the same finroot mean
    for rc, _score in results:
        assert rc == 0, f"One of the concurrent runs failed with rc={rc}"
    scores = [s for _, s in results]
    assert all(s == scores[0] for s in scores), (
        f"Concurrent runs produced different scores: {scores}"
    )
    # Sanity: should have finished in reasonable time
    assert elapsed < 180, f"4 concurrent evals took {elapsed:.1f}s; expected < 180s"


@pytest.mark.stress
def test_long_input_does_not_crash(tmp_path: Path) -> None:
    """Feed a 5000-character query into the CLI; it should not crash, even
    if the answer is degenerate."""
    long_query = "x" * 5000
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [sys.executable, "-m", "interface.cli", "--mock", long_query],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd=REPO_ROOT,
    )
    # The CLI may "succeed" (rc=0) with a degenerate answer, or "fail" with
    # a clear error message — both are acceptable. The failure mode we DON'T
    # want is a segfault, hang, or process crash with no output.
    assert result.returncode in (0, 1), (
        f"CLI exited with unexpected code {result.returncode}. "
        f"stdout={result.stdout[:200]!r} stderr={result.stderr[:200]!r}"
    )
    # Must produce some output (not a silent crash)
    assert len(result.stdout) > 0 or len(result.stderr) > 0, (
        "CLI produced no output for long input (silent crash?)"
    )
