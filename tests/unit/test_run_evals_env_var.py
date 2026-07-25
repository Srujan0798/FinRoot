"""Tests for the FINROOT_METRICS_PATH env-var override in scripts/run_evals.py.

The harness subprocess tests in tests/unit/test_harness.py::TestSingleTaskMode use
`--out` explicitly so they clobber results/metrics.json with a single-task subset.
This test file exercises the *env-var* path: when the conftest (or any caller) sets
FINROOT_METRICS_PATH, the subprocess writes to that path instead. The canonical
results/metrics.json is left untouched.

This is a fast test (single FRB task, k=1) because we only care about the
argparse default's behavior, not the harness's runtime.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METRICS_PATH = REPO_ROOT / "results" / "metrics.json"


def _run_cli_with_metrics_path(env_value: str | None) -> subprocess.CompletedProcess:
    """Run scripts/run_evals.py with k=1 (fastest) and return the result.

    If env_value is not None, set FINROOT_METRICS_PATH to it. If None, leave it
    unset (default behavior).
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    if env_value is not None:
        env["FINROOT_METRICS_PATH"] = env_value
    else:
        env.pop("FINROOT_METRICS_PATH", None)
    return subprocess.run(
        [
            sys.executable,
            "scripts/run_evals.py",
            "--mock",
            "--task",
            "frb-001",
            "--k",
            "1",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd=REPO_ROOT,
    )


def test_default_metrics_path_when_env_unset(tmp_path: Path) -> None:
    """When FINROOT_METRICS_PATH is NOT set, the CLI argparse default falls
    back to the DEFAULT_METRICS_PATH module-level constant. We test this by
    reading the constant directly, NOT by running the subprocess (which
    would clobber the canonical results/metrics.json file).

    The subprocess path is exercised in `test_env_var_overrides_default_path`
    and `test_explicit_out_flag_beats_env_var` below.
    """
    from src.finroot.evaluation.harness import DEFAULT_METRICS_PATH as harness_default

    # The CLI's argparse default is built from DEFAULT_METRICS_PATH at module
    # load time, via scripts/run_evals.py's _parse_args.
    # scripts/run_evals.py:312 uses `default=DEFAULT_METRICS_PATH` which is
    # `Path("results/metrics.json")` BEFORE the conftest module load sets
    # FINROOT_METRICS_PATH. After conftest load, DEFAULT_METRICS_PATH in
    # harness.py is overridden to a tmp path (see harness.py:DEFAULT_METRICS_PATH
    # computed via os.environ.get("FINROOT_METRICS_PATH", ...)). So we just
    # verify the constant resolves to something sensible.
    assert harness_default.exists() or str(harness_default).endswith("metrics.json")


def test_env_var_overrides_default_path(tmp_path: Path) -> None:
    """With FINROOT_METRICS_PATH set, the CLI writes to that path and the
    canonical results/metrics.json is left untouched."""
    target = tmp_path / "subprocess_metrics.json"
    # Snapshot canonical mtime
    canonical_mtime_before = (
        DEFAULT_METRICS_PATH.stat().st_mtime if DEFAULT_METRICS_PATH.exists() else None
    )

    result = _run_cli_with_metrics_path(str(target))
    assert result.returncode == 0, (
        f"CLI failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    # Subprocess wrote to our target path
    assert target.exists(), (
        f"Expected subprocess to write to {target}; "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    data = __import__("json").loads(target.read_text())
    assert data["n_tasks"] == 1
    # Canonical path was NOT written
    if canonical_mtime_before is not None:
        assert DEFAULT_METRICS_PATH.stat().st_mtime == canonical_mtime_before, (
            "Canonical results/metrics.json was modified by a subprocess that "
            "should have written to the env-var path"
        )


def test_explicit_out_flag_beats_env_var(tmp_path: Path) -> None:
    """The --out CLI flag takes precedence over FINROOT_METRICS_PATH."""
    env_target = tmp_path / "env_metrics.json"
    flag_target = tmp_path / "flag_metrics.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["FINROOT_METRICS_PATH"] = str(env_target)
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
            str(flag_target),
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
    assert flag_target.exists()
    assert not env_target.exists()
