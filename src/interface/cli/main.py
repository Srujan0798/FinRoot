"""Typer CLI for FinRoot — the reasoning-first financial agent.

Writes: ``src/interface/cli/main.py`` (wave-7, task 01).
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from interface.core import answer, build_trace

app = typer.Typer(
    name="finroot",
    help="FinRoot — sovereign, reasoning-first AI financial agent.",
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console()


def _confidence_color(confidence: str) -> str:
    """Map a confidence level string to a Rich colour name."""
    mapping = {
        "high": "green",
        "medium": "yellow",
        "low": "red",
        "insufficient": "red",
    }
    return mapping.get(confidence.lower(), "white")


@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    query: str | None = typer.Argument(None, help="The financial question to ask FinRoot."),
    mock: bool = typer.Option(True, "--mock/--no-mock", help="Use mock (offline) provider."),
    user: str = typer.Option("demo", "--user", "-u", help="User ID for memory/twin lookup."),
) -> None:
    """FinRoot — sovereign, reasoning-first AI financial agent.

    Usage: finroot [--mock/--no-mock] [--user ID] "query"
    """
    if ctx.invoked_subcommand is not None:
        return
    if query is None:
        return
    _process_query(query, mock, user)


@app.command("ask")
def ask_cmd(
    query: str = typer.Argument(..., help="The financial question to ask FinRoot."),
    mock: bool = typer.Option(True, "--mock/--no-mock", help="Use mock (offline) provider."),
    user: str = typer.Option("demo", "--user", "-u", help="User ID for memory/twin lookup."),
) -> None:
    """Ask FinRoot a financial question and see the reasoning."""
    _process_query(query, mock, user)


def _process_query(query: str, mock: bool, user: str) -> None:
    """Shared logic: run answer() and render output."""
    if not query or not query.strip():
        console.print("[red]Error:[/red] query must be non-empty.")
        raise typer.Exit(code=1)

    try:
        state = answer(query, user_id=user, mock=mock)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    _render(state)


def _render(state: object) -> None:
    """Pretty-print the agent state to the terminal."""
    from finroot.schemas.state import AgentState  # avoid circular

    if not isinstance(state, AgentState):
        console.print("[red]Unexpected state type.[/red]")
        return

    rec = state.candidate or state.final
    if rec is None:
        console.print("[yellow]No recommendation produced.[/yellow]")
        return

    # --- Answer panel ---
    conf = rec.confidence.value if hasattr(rec.confidence, "value") else str(rec.confidence)
    conf_color = _confidence_color(conf)

    answer_text = Text()
    answer_text.append(rec.summary, style="bold")
    answer_text.append("\n\n")
    answer_text.append(rec.analysis)

    console.print(Panel(answer_text, title="Answer", border_style="blue"))

    # --- Confidence & Risk ---
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="bold")
    info_table.add_column("Value")
    info_table.add_row("Confidence", f"[{conf_color}]{conf}[/{conf_color}]")

    if rec.risks:
        risk_display = rec.risks[0] if len(rec.risks) == 1 else f"{len(rec.risks)} risks flagged"
        info_table.add_row("Risks", risk_display)

    console.print(info_table)

    # --- Reasoning trace ---
    trace = build_trace(state)
    if trace:
        console.print()
        console.print("[bold]Reasoning Steps[/bold]")
        for evt in trace:
            node = evt.get("node", "?")
            action = evt.get("action", "?")
            detail = evt.get("detail", "")
            step_num = evt.get("step", 0)
            console.print(f"  {step_num}. [{node}] {action}: {detail[:120]}")

    # --- Citations ---
    if rec.citations:
        console.print()
        console.print("[bold]Citations[/bold]")
        for i, cit in enumerate(rec.citations, 1):
            val = f" — {cit.value}" if cit.value else ""
            console.print(f"  {i}. {cit.source}: {cit.detail}{val}")

    # --- Critic verdict ---
    if state.critique:
        console.print()
        overall = state.critique.get("overall", "N/A")
        passed = state.critique.get("passed", False)
        verdict_color = "green" if passed else "red"
        verdict_word = "PASSED" if passed else "FAILED"
        console.print(
            f"[bold]Critic Verdict[/bold]: [{verdict_color}]{verdict_word}[/{verdict_color}]"
            f" (overall={overall})"
        )
        summary = state.critique.get("summary", "")
        if summary:
            console.print(f"  {summary}")


__all__ = ["app"]
