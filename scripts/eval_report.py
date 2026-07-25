"""Formatted evaluation report from results/metrics.json.

Loads the metrics file and prints a comparison table (FinRoot vs RAG),
per-domain breakdown, pass@1 and mean scores, highlights weak domains,
and prints improvement recommendations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

METRICS_PATH = Path("results/metrics.json")


def load_metrics(path: Path = METRICS_PATH) -> dict:
    """Load and return the metrics JSON."""
    if not path.exists():
        print(f"Error: {path} not found. Run `make evals` first.")
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _fmt_score(value: float) -> str:
    return f"{value:.4f}"


def _delta_color(finroot: float, rag: float) -> str:
    """Return ANSI color code based on delta."""
    delta = finroot - rag
    if delta > 0.1:
        return "\033[92m"  # green
    if delta > 0:
        return "\033[33m"  # yellow
    return "\033[91m"  # red


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def print_header(metrics: dict) -> None:
    """Print report header."""
    print(f"\n{BOLD}{'=' * 72}")
    print("  FinRoot Evaluation Report")
    print(f"{'=' * 72}{RESET}")
    print(
        f"  {DIM}SHA: {metrics['as_of_sha']}  |  Tasks: {metrics['n_tasks']}  |  k: {metrics['k']}{RESET}"
    )
    print(f"  {DIM}Generated: {metrics['generated_at']}{RESET}")
    print()


def print_comparison_table(metrics: dict) -> None:
    """Print FinRoot vs RAG comparison table."""
    systems = metrics["systems"]
    fr = systems.get("finroot", {})
    rag = systems.get("rag", {})

    print(f"{BOLD}{'─' * 72}")
    print("  Headline: FinRoot vs RAG")
    print(f"{'─' * 72}{RESET}")

    lift = metrics.get("composite_lift_vs_rag_pct", 0)
    lift_color = "\033[92m" if lift > 0 else "\033[91m"

    rows = [
        ("Mean Score", _fmt_score(fr.get("mean_score", 0)), _fmt_score(rag.get("mean_score", 0))),
        ("pass@1", _fmt_pct(fr.get("pass_at_1", 0)), _fmt_pct(rag.get("pass_at_1", 0))),
        ("pass@k", _fmt_pct(fr.get("pass_at_k", 0)), _fmt_pct(rag.get("pass_at_k", 0))),
        ("pass^k", _fmt_pct(fr.get("pass_hat_k", 0)), _fmt_pct(rag.get("pass_hat_k", 0))),
    ]

    header = f"  {'Metric':<16} {'FinRoot':>12} {'RAG':>12} {'Delta':>12}"
    print(header)
    print(f"  {'─' * 52}")

    for label, fr_val, rag_val in rows:
        fr_num = float(fr_val.rstrip("%")) if "%" in fr_val else float(fr_val)
        rag_num = float(rag_val.rstrip("%")) if "%" in rag_val else float(rag_val)
        delta = fr_num - rag_num
        delta_str = f"{delta:+.2f}%" if "%" in fr_val else f"{delta:+.4f}"
        color = "\033[92m" if delta > 0 else "\033[91m"
        print(f"  {label:<16} {fr_val:>12} {rag_val:>12} {color}{delta_str:>12}{RESET}")

    print(f"\n  {lift_color}{BOLD}Composite lift vs RAG: {lift:+.2f}%{RESET}")
    print()


def print_domain_breakdown(metrics: dict) -> None:
    """Print per-domain comparison table."""
    systems = metrics["systems"]
    fr = systems.get("finroot", {})
    rag = systems.get("rag", {})

    fr_domains = fr.get("per_domain", {})
    rag_domains = rag.get("per_domain", {})

    all_domains = sorted(set(fr_domains) | set(rag_domains))

    print(f"{BOLD}{'─' * 72}")
    print("  Per-Domain Breakdown")
    print(f"{'─' * 72}{RESET}")
    print(f"  {'Domain':<20} {'FinRoot':>10} {'RAG':>10} {'Delta':>10} {'Status':>10}")
    print(f"  {'─' * 60}")

    for domain in all_domains:
        fr_val = fr_domains.get(domain, 0)
        rag_val = rag_domains.get(domain, 0)
        delta = fr_val - rag_val

        color = _delta_color(fr_val, rag_val)
        if delta > 0.1:
            status = "✓ strong"
        elif delta > 0:
            status = "~ ok"
        elif delta > -0.05:
            status = "~ weak"
        else:
            status = "✗ weak"

        print(
            f"  {domain:<20} {_fmt_score(fr_val):>10} {_fmt_score(rag_val):>10} "
            f"{color}{delta:>+10.4f}{RESET} {color}{status:>10}{RESET}"
        )
    print()


def print_weak_domains(metrics: dict, threshold: float = 0.85) -> None:
    """Highlight domains where FinRoot underperforms or scores below threshold."""
    systems = metrics["systems"]
    fr = systems.get("finroot", {})
    rag = systems.get("rag", {})

    fr_domains = fr.get("per_domain", {})
    rag_domains = rag.get("per_domain", {})

    weak = []
    for domain in fr_domains:
        fr_val = fr_domains[domain]
        rag_val = rag_domains.get(domain, 0)
        delta = fr_val - rag_val
        if fr_val < threshold or delta < 0:
            weak.append((domain, fr_val, rag_val, delta))

    weak.sort(key=lambda x: x[3])

    print(f"{BOLD}{'─' * 72}")
    print(f"  Weak Domains (score < {threshold:.0%} or underperforming RAG)")
    print(f"{'─' * 72}{RESET}")

    if not weak:
        print(f"  {DIM}No weak domains found.{RESET}")
    else:
        print(f"  {'Domain':<20} {'Score':>10} {'RAG':>10} {'Delta':>10}")
        print(f"  {'─' * 50}")
        for domain, fr_val, rag_val, delta in weak:
            color = "\033[91m" if delta < 0 else "\033[33m"
            print(
                f"  {domain:<20} {_fmt_score(fr_val):>10} {_fmt_score(rag_val):>10} {color}{delta:>+10.4f}{RESET}"
            )
    print()


def print_recommendations(metrics: dict) -> None:
    """Print improvement recommendations based on analysis."""
    systems = metrics["systems"]
    fr = systems.get("finroot", {})
    rag = systems.get("rag", {})

    fr_domains = fr.get("per_domain", {})
    rag_domains = rag.get("per_domain", {})
    fr_mean = fr.get("mean_score", 0)

    print(f"{BOLD}{'─' * 72}")
    print("  Improvement Recommendations")
    print(f"{'─' * 72}{RESET}")

    recs: list[str] = []

    # Find domains where FinRoot underperforms RAG
    underperforming = []
    for domain in fr_domains:
        fr_val = fr_domains[domain]
        rag_val = rag_domains.get(domain, 0)
        if fr_val < rag_val:
            underperforming.append((domain, fr_val, rag_val))

    if underperforming:
        underperforming.sort(key=lambda x: x[2] - x[1])
        worst = underperforming[0]
        recs.append(
            f"Priority: Investigate '{worst[0]}' domain — FinRoot ({_fmt_score(worst[1])}) "
            f"trails RAG ({_fmt_score(worst[2])}). Review grader criteria and prompt templates."
        )

    # Find lowest scoring domains
    low_scoring = [(d, s) for d, s in fr_domains.items() if s < 0.85]
    low_scoring.sort(key=lambda x: x[1])
    if low_scoring:
        domains_str = ", ".join(f"{d} ({_fmt_score(s)})" for d, s in low_scoring[:3])
        recs.append(
            f"Focus on low-scoring domains: {domains_str}. "
            "Consider domain-specific prompt engineering or tool augmentation."
        )

    # pass@1 vs mean_score gap (consistency)
    pass1 = fr.get("pass_at_1", 0)
    if fr_mean - pass1 > 0.15:
        recs.append(
            f"High variance detected: mean_score ({_fmt_score(fr_mean)}) vs pass@1 ({_fmt_pct(pass1)}). "
            "Trials are inconsistent — investigate seed sensitivity."
        )

    # General recommendations
    if fr_mean < 0.95:
        recs.append(
            "To reach >0.95 mean score: ensure all citations are present, "
            "all required keywords are mentioned, and answers meet length thresholds."
        )

    if not recs:
        recs.append("FinRoot is performing well across all domains. No critical issues found.")

    for i, rec in enumerate(recs, 1):
        print(f"  {i}. {rec}")

    print()


def generate_report(path: Path = METRICS_PATH) -> str:
    """Generate the full report and return as string (for testing)."""
    import contextlib
    import io

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        metrics = load_metrics(path)
        print_header(metrics)
        print_comparison_table(metrics)
        print_domain_breakdown(metrics)
        print_weak_domains(metrics)
        print_recommendations(metrics)
    return f.getvalue()


def main() -> None:
    """Entry point for CLI."""
    metrics = load_metrics()
    print_header(metrics)
    print_comparison_table(metrics)
    print_domain_breakdown(metrics)
    print_weak_domains(metrics)
    print_recommendations(metrics)


if __name__ == "__main__":
    main()
