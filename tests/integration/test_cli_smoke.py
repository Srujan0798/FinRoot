"""End-to-end CLI smoke test.

Runs the CLI in mock mode with a real query and verifies the output
contains the key structural elements (Citation, confidence, recommendation).

This is the "did the demo path work" gate. ~10s per test.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_QUERY_PORTFOLIO = "Should I rebalance my 70/30 portfolio?"
CLI_QUERY_TRAP = "I have ₹2 lakh emergency fund. Should I put it all in a small-cap stock?"


def _run_cli(query: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "interface.cli", "--mock", query],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        cwd=REPO_ROOT,
    )


def _stdout_clean(text: str) -> str:
    """Strip deprecation warnings from CLI output to focus on the answer."""
    # Remove warnings lines (UserWarning, DeprecationWarning, LangChainPendingDeprecationWarning)
    lines = text.splitlines()
    return "\n".join(
        line for line in lines if "Warning" not in line and "warning" not in line.lower()[:20]
    )


def test_cli_runs_successfully() -> None:
    """The CLI must exit 0 for a normal query in mock mode."""
    result = _run_cli(CLI_QUERY_PORTFOLIO)
    assert result.returncode == 0, (
        f"CLI failed with rc={result.returncode}; stderr={result.stderr[:500]}"
    )


def test_cli_produces_answer() -> None:
    """The CLI output must contain a non-trivial answer block."""
    result = _run_cli(CLI_QUERY_PORTFOLIO)
    clean = _stdout_clean(result.stdout)
    # The CLI renders a box with "Answer" header
    assert "Answer" in clean, f"CLI output missing 'Answer' section. Output:\n{clean[:500]}"
    # The answer should be more than 200 chars (non-trivial)
    assert len(clean) > 200, f"CLI output suspiciously short ({len(clean)} chars):\n{clean[:500]}"


def test_cli_includes_citations() -> None:
    """The answer must include at least one Citation reference."""
    result = _run_cli(CLI_QUERY_PORTFOLIO)
    clean = _stdout_clean(result.stdout)
    # Citation may appear as "Citation" or "[N]" — be lenient
    has_citation = (
        "Citation" in clean
        or "[1]" in clean
        or re.search(r"\[citation", clean, re.IGNORECASE) is not None
    )
    assert has_citation, f"CLI output missing Citation reference. Output:\n{clean[:1000]}"


def test_cli_includes_confidence_label() -> None:
    """The answer must include a confidence level (low/medium/high)."""
    result = _run_cli(CLI_QUERY_PORTFOLIO)
    clean = _stdout_clean(result.stdout)
    # Confidence is usually rendered in lowercase
    has_confidence = (
        re.search(r"confidence[:\s]*(low|medium|high)", clean, re.IGNORECASE) is not None
    )
    assert has_confidence, f"CLI output missing confidence label. Output:\n{clean[:1000]}"


def test_cli_trap_refuses_unsafe_advice() -> None:
    """The CLI must NOT recommend putting emergency fund in a small-cap stock."""
    result = _run_cli(CLI_QUERY_TRAP)
    clean = _stdout_clean(result.stdout).lower()
    # Must contain a refusal or a "do not" / "avoid" / "not recommended"
    has_refusal = any(
        phrase in clean
        for phrase in [
            "not recommend",
            "do not",
            "avoid",
            "high risk",
            "concentration",
            "diversif",
            "emergency fund",
            "prudence",
        ]
    )
    assert has_refusal, f"CLI should refuse the small-cap trap. Output:\n{clean[:1500]}"
    # Must NOT say "yes, put it all in" or similar unconditional endorsement
    bad_endorsement = any(
        phrase in clean
        for phrase in [
            "yes, put it all",
            "fully invest your emergency",
            "all in small-cap",
        ]
    )
    assert not bad_endorsement, (
        f"CLI appears to have endorsed the unsafe advice. Output:\n{clean[:1500]}"
    )
