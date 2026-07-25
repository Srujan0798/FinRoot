"""Tests for scripts/eval_report.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.eval_report import (
    generate_report,
    load_metrics,
    print_comparison_table,
    print_domain_breakdown,
    print_header,
    print_recommendations,
    print_weak_domains,
)


@pytest.fixture()
def sample_metrics(tmp_path: Path) -> Path:
    """Write a sample metrics.json to tmp_path and return the path."""
    data = {
        "as_of_sha": "abc1234",
        "generated_at": "2026-07-25T00:00:00Z",
        "systems": {
            "finroot": {
                "system": "finroot",
                "pass_at_1": 0.6265,
                "pass_at_k": 0.6265,
                "pass_hat_k": 0.6265,
                "mean_score": 0.9007,
                "per_domain": {
                    "behavioral": 0.8083,
                    "cashflow": 0.8797,
                    "credit": 0.9667,
                    "international": 0.795,
                    "tax": 0.8956,
                },
                "n_tasks": 83,
            },
            "rag": {
                "system": "rag",
                "pass_at_1": 0.2169,
                "pass_at_k": 0.2169,
                "pass_hat_k": 0.2169,
                "mean_score": 0.3403,
                "per_domain": {
                    "behavioral": 0.4286,
                    "cashflow": 0.3917,
                    "credit": 0.5038,
                    "international": 0.275,
                    "tax": 0.3033,
                },
                "n_tasks": 83,
            },
        },
        "composite_lift_vs_rag_pct": 164.6782,
        "n_tasks": 83,
        "k": 1,
    }
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def test_report_loads_metrics(sample_metrics: Path) -> None:
    """loads metrics.json without error."""
    metrics = load_metrics(sample_metrics)
    assert "systems" in metrics
    assert "finroot" in metrics["systems"]
    assert "rag" in metrics["systems"]
    assert metrics["n_tasks"] == 83


def test_report_loads_metrics_missing(tmp_path: Path) -> None:
    """Exits cleanly when metrics file is missing."""
    missing = tmp_path / "nope.json"
    with pytest.raises(SystemExit):
        load_metrics(missing)


def test_report_prints_comparison(sample_metrics: Path) -> None:
    """produces formatted output for comparison table."""
    import io
    from contextlib import redirect_stdout

    metrics = load_metrics(sample_metrics)
    f = io.StringIO()
    with redirect_stdout(f):
        print_header(metrics)
        print_comparison_table(metrics)
    output = f.getvalue()

    assert "FinRoot" in output
    assert "RAG" in output
    assert "Mean Score" in output
    assert "pass@1" in output
    assert "Composite lift" in output


def test_report_prints_domain_breakdown(sample_metrics: Path) -> None:
    """produces per-domain breakdown output."""
    import io
    from contextlib import redirect_stdout

    metrics = load_metrics(sample_metrics)
    f = io.StringIO()
    with redirect_stdout(f):
        print_domain_breakdown(metrics)
    output = f.getvalue()

    assert "Per-Domain Breakdown" in output
    assert "behavioral" in output
    assert "credit" in output
    assert "international" in output


def test_report_highlights_weak_domains(sample_metrics: Path) -> None:
    """identifies lowest-scoring domains."""
    import io
    from contextlib import redirect_stdout

    metrics = load_metrics(sample_metrics)
    f = io.StringIO()
    with redirect_stdout(f):
        print_weak_domains(metrics, threshold=0.85)
    output = f.getvalue()

    assert "Weak Domains" in output
    # international (0.795) and behavioral (0.8083) are below 0.85
    assert "international" in output
    assert "behavioral" in output


def test_report_prints_recommendations(sample_metrics: Path) -> None:
    """produces recommendations."""
    import io
    from contextlib import redirect_stdout

    metrics = load_metrics(sample_metrics)
    f = io.StringIO()
    with redirect_stdout(f):
        print_recommendations(metrics)
    output = f.getvalue()

    assert "Improvement Recommendations" in output
    assert "1." in output


def test_generate_report_returns_string(sample_metrics: Path) -> None:
    """generate_report returns the full report as a string."""
    report = generate_report(sample_metrics)
    assert isinstance(report, str)
    assert "FinRoot Evaluation Report" in report
    assert "Composite lift" in report
    assert "Per-Domain Breakdown" in report
    assert "Improvement Recommendations" in report
