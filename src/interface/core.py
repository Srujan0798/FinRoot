"""Core entry point shared by CLI and UI.

Provides ``answer()`` — a single-call pipeline that builds memory + audit +
LLM, runs the FinRootOrchestrator, and returns the full ``AgentState`` for
the caller to render.  Also provides ``build_trace()`` which derives the
reasoning-trace event list from the state.

Writes: ``src/interface/core.py`` (wave-7, task 01).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from finroot.agents.orchestrator import FinRootOrchestrator
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.llm.factory import get_provider
from finroot.llm.mock import MockProvider
from finroot.memory.digital_twin import DigitalTwin, DigitalTwinStore
from finroot.memory.manager import MemoryManager
from finroot.memory.semantic import SemanticMemory
from finroot.memory.working import WorkingMemory
from finroot.schemas.state import AgentState

logger = logging.getLogger(__name__)

_TWIN_PROFILES_PATH = Path("data/samples/twin_profiles.json")


def _load_demo_twin(user_id: str) -> DigitalTwin | None:
    """Attempt to load a demo twin from the samples file.

    Looks for an exact ``user_id`` match first; if none is found (e.g. the
    default ``"demo"`` id), falls back to the FIRST sample profile so the
    demo path always has a populated twin (holdings, goals, risk profile).
    The returned twin's ``user_id`` is rebound to *user_id* so that
    ``MemoryManager.get_twin(user_id)`` resolves it after seeding.

    Returns ``None`` only if the file is missing or malformed — never raises
    (graceful degradation, FM-11: logs loud on failure).
    """
    if not _TWIN_PROFILES_PATH.exists():
        return None
    try:
        profiles: list[dict[str, Any]] = json.loads(
            _TWIN_PROFILES_PATH.read_text(encoding="utf-8")
        )
        if not profiles:
            return None
        chosen: dict[str, Any] | None = None
        for profile in profiles:
            if profile.get("user_id") == user_id:
                chosen = profile
                break
        if chosen is None:
            # No exact match — use the first profile so the demo is populated.
            chosen = dict(profiles[0])
            chosen["user_id"] = user_id
        return DigitalTwin.model_validate(chosen)
    except Exception as exc:
        logger.warning("Failed to load demo twin profiles: %s", exc)
    return None


def _normalize_holdings(holdings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add agent-required ``symbol`` / ``weight`` / ``shares`` / ``market_price``
    fields to fixture holdings (which carry ``asset_id`` / ``quantity`` /
    ``unit_price``).

    The portfolio optimizer needs ``symbol``; the portfolio simulator needs a
    numeric ``weight``. Weights are derived from market value
    (``quantity * unit_price``) and normalised to sum to 1.0. Rich fixture
    fields are preserved. Returns a new list (does not mutate input).
    """
    enriched: list[dict[str, Any]] = []
    values: list[float] = []
    for h in holdings:
        qty = float(h.get("quantity") or h.get("shares") or 0.0)
        price = float(h.get("unit_price") or h.get("market_price") or 0.0)
        values.append(qty * price)
    total = sum(values) or 1.0
    for h, val in zip(holdings, values, strict=False):
        item = dict(h)
        item.setdefault("symbol", h.get("symbol") or h.get("asset_id") or h.get("name", "UNKNOWN"))
        item.setdefault("shares", h.get("quantity", 0))
        item.setdefault("market_price", h.get("unit_price", 0.0))
        item["weight"] = round(val / total, 6)
        enriched.append(item)
    return enriched


def _build_memory(user_id: str) -> MemoryManager:
    """Build a ``MemoryManager`` bound to *user_id* with a demo twin if found."""
    working = WorkingMemory(max_turns=10)
    semantic = SemanticMemory(persist_dir="data/chroma")
    twin_store = DigitalTwinStore(db_path="data/digital_twin.db")

    # Try to seed the twin store with a demo profile
    demo = _load_demo_twin(user_id)
    if demo is not None:
        try:
            if demo.holdings:
                demo.holdings = _normalize_holdings(demo.holdings)
            twin_store.save(demo)
        except Exception as exc:
            logger.warning("Could not seed demo twin for %s: %s", user_id, exc)

    return MemoryManager(
        working=working,
        semantic=semantic,
        twin_store=twin_store,
        user_id=user_id,
    )


def answer(
    query: str,
    *,
    user_id: str = "demo",
    mock: bool = True,
) -> AgentState:
    """One-call pipeline: build memory + audit + LLM → orchestrator.run(query).

    Parameters
    ----------
    query:
        The raw user query string.
    user_id:
        Stable user identifier for memory / twin lookup.
    mock:
        If ``True`` (default), use the offline ``MockProvider``.
        If ``False``, resolve the real provider from the environment.

    Returns
    -------
    AgentState
        The fully-populated state (candidate, plan, tool_outputs, critique,
        audit_events, etc.) for the caller to render.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    # In mock mode, also put the TOOLS in offline mode: they read
    # FINROOT_LLM_PROVIDER from the env (market_data, news, macro, currency, …).
    # Without this only the LLM would be mocked while tools hit live APIs.
    if mock:
        os.environ["FINROOT_LLM_PROVIDER"] = "mock"

    llm: LLMProvider = MockProvider() if mock else get_provider()
    memory = _build_memory(user_id)
    audit = AuditTrail(Path(tempfile.mkdtemp()) / "audit.jsonl")

    orch = FinRootOrchestrator(memory=memory, audit=audit, llm=llm)
    state: AgentState = orch.run(query)

    # Wire W5 reasoning critic if available — degrade gracefully (FM-11)
    try:
        from finroot.reasoning.critic import SelfCritic

        critic = SelfCritic()
        verdict = critic.evaluate(state)
        state.critique = verdict.model_dump(mode="json")
    except ImportError as exc:
        logger.warning("Reasoning critic not available — skipping critique: %s", exc)
    except Exception as exc:
        logger.warning("Critic evaluation failed — skipping: %s", exc)

    # Wire W5 Rooted Prudence verifier — the 'do no harm' gate. If the advice
    # is non-compliant (e.g. touches the emergency fund, over-concentrates,
    # promises returns), record the verdict and downgrade confidence so the UI
    # surfaces the caution. Degrade gracefully (FM-11).
    try:
        from finroot.reasoning.principles import PrudentialVerifier

        prudential = PrudentialVerifier().verify(state)
        state.verifier_verdict = prudential.model_dump(mode="json")
        if not prudential.compliant:
            _apply_prudence_downgrade(state, prudential.model_dump(mode="json"))
    except ImportError as exc:
        logger.warning("Prudence verifier not available — skipping: %s", exc)
    except Exception as exc:
        logger.warning("Prudence verification failed — skipping: %s", exc)

    return state


def _apply_prudence_downgrade(state: AgentState, verdict: dict[str, Any]) -> None:
    """Downgrade the recommendation's confidence to LOW and prepend a specific
    caution naming the violated principle(s) when the prudence verifier flags
    the advice. Best-effort (never raises)."""
    failed = [
        f"{c['principle']} — {c['detail']}"
        for c in verdict.get("checks", [])
        if not c.get("pass")
    ]
    if failed:
        note = (
            "Prudence check failed: "
            + "; ".join(failed)
            + ". Recommendation: do not act yet — verify against your full financial picture."
        )
    else:
        note = verdict.get("warning") or "This advice may not be suitable — do not act yet."
    for rec in (state.final, state.candidate):
        if rec is None:
            continue
        try:
            from finroot.schemas.enums import ConfidenceLevel

            rec.confidence = ConfidenceLevel.LOW
        except Exception:
            logger.warning("Could not set confidence to LOW on recommendation")
        try:
            if note.lower() not in (rec.summary or "").lower():
                rec.summary = f"⚠️ {note}\n\n{rec.summary}"
        except Exception:
            logger.warning("Could not prepend prudence note to summary")


def build_trace(state: AgentState) -> list[dict[str, Any]]:
    """Derive the reasoning-trace event list from *state*.

    Combines ``audit_events``, ``plan``, and ``tool_outputs`` into a flat
    list of trace events shaped::

        {"step": int, "node": str, "action": str, "detail": str, "source": str | None}
    """
    events: list[dict[str, Any]] = []
    step = 0

    # 1. Pipeline steps from the plan
    for plan_item in state.plan:
        events.append({
            "step": step,
            "node": "planner",
            "action": "plan_step",
            "detail": plan_item,
            "source": None,
        })
        step += 1

    # 2. Tool outputs
    for out in state.tool_outputs:
        if not isinstance(out, dict):
            continue
        node = out.get("agent", out.get("tool", "unknown"))
        action = out.get("type", "tool_output")
        detail_parts: list[str] = []
        for k, v in out.items():
            if k not in ("agent", "tool", "type"):
                detail_parts.append(f"{k}={v}")
        detail = ", ".join(detail_parts) if detail_parts else str(out)
        events.append({
            "step": step,
            "node": str(node),
            "action": str(action),
            "detail": detail[:300],
            "source": out.get("tool"),
        })
        step += 1

    # 3. Critique verdict
    if state.critique:
        events.append({
            "step": step,
            "node": "critic",
            "action": "critique",
            "detail": state.critique.get("summary", "critique completed"),
            "source": "self_critic",
        })
        step += 1

    # 4. Audit events (hash-chain entries)
    for audit_event in state.audit_events:
        events.append({
            "step": step,
            "node": audit_event.type.split(".")[0] if "." in audit_event.type else audit_event.type,
            "action": audit_event.type,
            "detail": json.dumps(audit_event.payload, default=str)[:300],
            "source": "audit_trail",
        })
        step += 1

    # 5. Candidate / final recommendation summary
    rec = state.candidate or state.final
    if rec is not None:
        events.append({
            "step": step,
            "node": "synthesizer",
            "action": "recommendation",
            "detail": rec.summary[:300],
            "source": None,
        })
        step += 1

    return events


__all__ = ["answer", "build_trace"]
