"""Comprehensive CLI integration tests.

Runs the CLI via subprocess in mock mode, verifying help, output structure,
edge-case handling, and that no API key is required.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_cli(*args: str, mock: bool = True) -> subprocess.CompletedProcess:
    """Run the CLI as a subprocess with a controlled environment."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env.pop("FINROOT_GROQ_API_KEY", None)
    env.pop("FINROOT_OPENAI_API_KEY", None)
    env.pop("FINROOT_OLLAMA_BASE_URL", None)
    env.pop("FINROOT_OLLAMA_MODEL", None)
    if mock:
        env["FINROOT_LLM_PROVIDER"] = "mock"
    else:
        env["FINROOT_LLM_PROVIDER"] = env.get("FINROOT_LLM_PROVIDER", "mock")

    cmd = [sys.executable, "-m", "interface.cli"]
    if mock:
        cmd.append("--mock")
    cmd.extend(args)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=REPO_ROOT,
    )


# ── Help ──────────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_cli_help_exits_zero():
    """--help should exit with code 0."""
    result = _run_cli("--help", mock=False)
    assert result.returncode == 0, (
        f"--help exited {result.returncode}; stderr={result.stderr[:300]}"
    )
    assert result.stdout.strip(), "--help produced no stdout"


# ── Mock output ───────────────────────────────────────────────────────────


@pytest.mark.integration
def test_cli_mock_produces_output():
    """A mock query must produce non-empty stdout."""
    result = _run_cli("What is compound interest?")
    assert result.returncode == 0, f"CLI exited {result.returncode}; stderr={result.stderr[:500]}"
    assert result.stdout.strip(), "CLI produced empty output"


@pytest.mark.integration
def test_cli_output_has_answer_section():
    """The rendered output should contain an 'Answer' header or markdown ##."""
    result = _run_cli("What is compound interest?")
    stdout = result.stdout
    has_answer = "Answer" in stdout or "##" in stdout
    assert has_answer, f"CLI output missing 'Answer' section. First 500 chars:\n{stdout[:500]}"


@pytest.mark.integration
def test_cli_output_has_confidence():
    """The output should include a confidence indicator."""
    result = _run_cli("What is compound interest?")
    stdout_lower = result.stdout.lower()
    has_confidence = "confidence" in stdout_lower
    assert has_confidence, (
        f"CLI output missing confidence indicator. First 500 chars:\n{result.stdout[:500]}"
    )


# ── Edge cases ────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_cli_empty_query_handled():
    """An empty query should not crash the CLI."""
    result = _run_cli("", mock=False)
    # Empty query is rejected with code 1 by the CLI; the important thing
    # is that the process does not crash (traceback / signal).
    assert result.returncode in (0, 1), (
        f"CLI crashed with rc={result.returncode}; stderr={result.stderr[:500]}"
    )
    # No Python traceback in stderr
    assert "Traceback" not in result.stderr, (
        f"CLI raised an unhandled exception:\n{result.stderr[:500]}"
    )


@pytest.mark.integration
def test_cli_special_chars_handled():
    """A query with special characters should not crash."""
    result = _run_cli("Invest ₹10k in !@#$%^&*() stocks?")
    # Should exit cleanly (0 for success or 1 for graceful error)
    assert result.returncode in (0, 1), (
        f"CLI crashed with rc={result.returncode}; stderr={result.stderr[:500]}"
    )
    assert "Traceback" not in result.stderr, (
        f"CLI raised an unhandled exception:\n{result.stderr[:500]}"
    )


# ── Exit code ─────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_cli_exit_code_zero():
    """A successful mock query should exit with code 0."""
    result = _run_cli("What is compound interest?")
    assert result.returncode == 0, (
        f"Expected exit code 0, got {result.returncode}; stderr={result.stderr[:500]}"
    )


# ── No API key needed ────────────────────────────────────────────────────


@pytest.mark.integration
def test_cli_mock_no_api_key():
    """Mock mode must work even when FINROOT_GROQ_API_KEY is absent."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["FINROOT_LLM_PROVIDER"] = "mock"
    # Explicitly remove all API keys
    env.pop("FINROOT_GROQ_API_KEY", None)
    env.pop("FINROOT_OPENAI_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "-m", "interface.cli", "--mock", "What is compound interest?"],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"Mock CLI failed without API key: rc={result.returncode}; stderr={result.stderr[:500]}"
    )
    assert result.stdout.strip(), "Mock CLI produced no output without API key"
