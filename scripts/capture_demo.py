"""Capture demo transcripts for screenshots/video narration.

Runs ``interface.core.answer()`` on 4 showcase queries in Mock mode and writes
formatted markdown transcripts to ``docs/demo/transcript_*.md``.

Usage::

    PYTHONPATH=src python3 scripts/capture_demo.py

Each transcript contains: query, answer card (summary + analysis + confidence),
reasoning trace (build_trace), critic verdict, and citations — formatted for
screenshots.  Fails loud if ``answer()`` import fails (FM-11).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — ensure src/ is importable
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent.parent
_SRC = _ROOT / "src"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ---------------------------------------------------------------------------
# Showcase queries — one per intent domain the judges will see
# ---------------------------------------------------------------------------
SHOWCASE_QUERIES: list[dict[str, str]] = [
    {
        "slug": "portfolio",
        "query": "What is my current portfolio allocation and risk level?",
    },
    {
        "slug": "tax_with_number",
        "query": "How much tax will I owe if I sell my equity holdings this year?",
    },
    {
        "slug": "news_impact",
        "query": "What is the impact of recent RBI policy changes on my debt fund holdings?",
    },
    {
        "slug": "trap_question",
        "query": "I want to put my entire emergency fund into a high-growth small-cap stock.",
    },
]

OUTPUT_DIR = _ROOT / "docs" / "demo"


def _format_answer_card(state: object) -> str:
    """Render the answer card from an AgentState as markdown."""
    rec = getattr(state, "candidate", None) or getattr(state, "final", None)
    if rec is None:
        return "**No recommendation produced.**"

    parts: list[str] = []
    parts.append(f"**Confidence:** `{getattr(rec, 'confidence', 'N/A')}`")

    summary = getattr(rec, "summary", "")
    if summary:
        parts.append(f"\n### Summary\n{summary}")

    analysis = getattr(rec, "analysis", "")
    if analysis:
        parts.append(f"\n### Analysis\n{analysis}")

    risks = getattr(rec, "risks", [])
    if risks:
        parts.append("\n### Risks")
        for r in risks:
            parts.append(f"- {r}")

    actions = getattr(rec, "actions", [])
    if actions:
        parts.append("\n### Recommended Actions")
        for a in actions:
            parts.append(f"- {a}")

    alternatives = getattr(rec, "alternatives", [])
    if alternatives:
        parts.append("\n### Alternatives")
        for alt in alternatives:
            parts.append(f"- {alt}")

    assumptions = getattr(rec, "assumptions", [])
    if assumptions:
        parts.append("\n### Assumptions")
        for asm in assumptions:
            parts.append(f"- {asm}")

    invalidation = getattr(rec, "invalidation_conditions", [])
    if invalidation:
        parts.append("\n### Invalidation Conditions")
        for inv in invalidation:
            parts.append(f"- {inv}")

    return "\n".join(parts)


def _format_citations(state: object) -> str:
    """Render citations from the recommendation as markdown."""
    rec = getattr(state, "candidate", None) or getattr(state, "final", None)
    if rec is None:
        return "*No citations.*"

    citations = getattr(rec, "citations", [])
    if not citations:
        return "*No citations (qualitative analysis only).*"

    parts: list[str] = ["| Source | Detail | Value | Retrieved At |",
                         "|--------|--------|-------|--------------|"]
    for c in citations:
        src = getattr(c, "source", "")
        detail = getattr(c, "detail", "")
        val = getattr(c, "value", "") or "—"
        ts = getattr(c, "retrieved_at", "")
        parts.append(f"| {src} | {detail} | {val} | {ts} |")
    return "\n".join(parts)


def _format_trace(events: list[dict]) -> str:
    """Render the reasoning trace events as markdown."""
    if not events:
        return "*No trace events.*"

    parts: list[str] = ["| Step | Node | Action | Detail |",
                         "|------|------|--------|--------|"]
    for evt in events:
        step = evt.get("step", "?")
        node = evt.get("node", "?")
        action = evt.get("action", "?")
        detail = str(evt.get("detail", ""))[:120]
        parts.append(f"| {step} | {node} | {action} | {detail} |")
    return "\n".join(parts)


def _format_critique(state: object) -> str:
    """Render the critic verdict as markdown."""
    critique = getattr(state, "critique", None)
    if not critique:
        return "*No critic verdict (critic not available).*"

    parts: list[str] = []
    summary = critique.get("summary", "")
    if summary:
        parts.append(f"**Verdict:** {summary}")

    axes = critique.get("axes") or critique.get("scores") or []
    if axes:
        parts.append("\n| Axis | Score |")
        parts.append("|------|-------|")
        for axis in axes:
            name = axis.get("name", axis.get("axis", "?"))
            score = axis.get("score", "?")
            parts.append(f"| {name} | {score} |")

    return "\n".join(parts) if parts else f"```json\n{critique}\n```"


def _format_verifier(state: object) -> str:
    """Render the prudence verifier verdict as markdown."""
    verdict = getattr(state, "verifier_verdict", None)
    if not verdict:
        return "*No prudence verdict (verifier not available).*"

    parts: list[str] = []
    compliant = verdict.get("compliant", None)
    parts.append(f"**Compliant:** `{compliant}`")

    warning = verdict.get("warning", "")
    if warning:
        parts.append(f"**Warning:** {warning}")

    checks = verdict.get("checks", [])
    if checks:
        parts.append("\n| Principle | Pass | Detail |")
        parts.append("|-----------|------|--------|")
        for chk in checks:
            principle = chk.get("principle", "?")
            passed = chk.get("pass", "?")
            detail = chk.get("detail", "")
            parts.append(f"| {principle} | {passed} | {detail} |")

    return "\n".join(parts)


def _build_transcript(index: int, slug: str, query: str, state: object, trace: list[dict]) -> str:
    """Assemble a full markdown transcript for one query."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sections = [
        f"# Demo Transcript {index}: {slug.replace('_', ' ').title()}",
        "",
        f"> Generated: {now}  ",
        "> Mode: Mock (offline, no API keys)",
        "",
        "---",
        "",
        "## Query",
        "",
        f"> {query}",
        "",
        "---",
        "",
        "## Answer Card",
        "",
        _format_answer_card(state),
        "",
        "---",
        "",
        "## Citations",
        "",
        _format_citations(state),
        "",
        "---",
        "",
        "## Reasoning Trace",
        "",
        _format_trace(trace),
        "",
        "---",
        "",
        "## Critic Verdict (5-Axis)",
        "",
        _format_critique(state),
        "",
        "---",
        "",
        "## Prudence Verifier",
        "",
        _format_verifier(state),
        "",
        "---",
        "",
        "*End of transcript.*",
        "",
    ]
    return "\n".join(sections)


def main() -> None:
    """Run answer() on each showcase query and write transcripts."""
    # Import with loud failure (FM-11)
    try:
        from interface.core import answer, build_trace
    except ImportError as exc:
        print(
            f"FATAL: Could not import interface.core — {exc}\n"
            "Ensure PYTHONPATH includes src/ and all dependencies are installed.",
            file=sys.stderr,
        )
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for idx, item in enumerate(SHOWCASE_QUERIES, start=1):
        slug = item["slug"]
        query = item["query"]
        filename = f"transcript_{idx}_{slug}.md"
        out_path = OUTPUT_DIR / filename

        print(f"[{idx}/4] Running answer() for: {query!r} ...", flush=True)

        try:
            state = answer(query, user_id="demo", mock=True)
        except Exception as exc:
            print(
                f"  ERROR: answer() raised {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            # Still write a transcript indicating the failure
            state = None  # type: ignore[assignment]

        if state is not None:
            trace = build_trace(state)
            transcript = _build_transcript(idx, slug, query, state, trace)
        else:
            transcript = (
                f"# Demo Transcript {idx}: {slug}\n\n"
                f"> Query: {query}\n\n"
                "**ERROR:** `answer()` failed — see terminal output.\n"
            )

        out_path.write_text(transcript, encoding="utf-8")
        written.append(str(out_path.relative_to(_ROOT)))
        print(f"  -> {out_path.relative_to(_ROOT)}")

    print(f"\nDone. {len(written)} transcript(s) written:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
