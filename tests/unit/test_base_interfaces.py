"""Tests for the base tool & agent interfaces (wave-1, task 05).

Covers:
* TTL cache: same result within TTL, expires after.
* Rate limiter: enforced (calls are delayed or blocked).
* Loud failure: ``ToolCallError`` propagates; no silent fallback.
* Audit emission: every call emits an audit event.
* BaseAgent: tool dispatch via ``_call_tool``, unknown tool raises,
  ``act`` is abstract.
"""

from __future__ import annotations

import time
from pathlib import Path
from tempfile import mkdtemp

import pytest

from finroot.agents.base import BaseAgent
from finroot.audit import AuditTrail
from finroot.llm.mock import MockProvider
from finroot.schemas.state import AgentState
from finroot.tools.base import BaseTool, ToolCallError

# ---------------------------------------------------------------------------
# Dummy tools for testing
# ---------------------------------------------------------------------------

class _DummyCounterTool(BaseTool[int, int]):
    """Returns an incrementing counter each time ``_run`` is actually called.
    Used to verify cache hits vs. misses.
    """
    name = "counter"
    ttl_seconds = 3600  # long enough for testing
    rate_per_sec = 1000.0  # effectively unlimited

    def __init__(self, audit: AuditTrail | None = None) -> None:
        super().__init__(audit=audit)
        self.call_count = 0

    def _run(self, inp: int) -> int:
        self.call_count += 1
        return self.call_count


class _DummyFailingTool(BaseTool[str, str]):
    """Always raises — used to test loud-failure propagation."""
    name = "failing"
    max_retries = 2
    base_delay = 0.01  # fast for testing

    def _run(self, inp: str) -> str:
        msg = f"intentional failure for {inp!r}"
        raise ValueError(msg)


class _DummySlowTool(BaseTool[str, str]):
    """Tool with a low rate limit — used to test rate limiting."""
    name = "slow"
    rate_per_sec = 0.5  # 1 token per 2 seconds

    def _run(self, inp: str) -> str:
        return f"processed:{inp}"


class _DummyAddTool(BaseTool[tuple[int, int], int]):
    """Simple additive tool for agent dispatch tests."""
    name = "add"

    def _run(self, inp: tuple[int, int]) -> int:
        return inp[0] + inp[1]


# ---------------------------------------------------------------------------
# BaseTool — cache
# ---------------------------------------------------------------------------


class TestBaseToolCache:
    def test_returns_cached_result_within_ttl(self) -> None:
        tool = _DummyCounterTool()
        assert tool(1) == 1  # _run called
        assert tool(1) == 1  # cached — _run NOT called
        assert tool.call_count == 1

    def test_different_inputs_are_not_cached(self) -> None:
        tool = _DummyCounterTool()
        assert tool(1) == 1
        assert tool(2) == 2  # different key, _run called again
        assert tool.call_count == 2

    def test_cache_expires_after_ttl(self) -> None:
        tool = _DummyCounterTool()
        tool.ttl_seconds = 0.01  # expire almost immediately
        assert tool(1) == 1
        time.sleep(0.02)
        assert tool(1) == 2  # expired, _run called again
        assert tool.call_count == 2


# ---------------------------------------------------------------------------
# BaseTool — rate limiter
# ---------------------------------------------------------------------------


class TestBaseToolRateLimit:
    def test_rate_limit_enforced(self) -> None:
        tool = _DummySlowTool()
        t1 = time.monotonic()
        tool("a")  # first call waits for initial token
        t2 = time.monotonic()
        tool("b")  # second call waits for token bucket to refill
        t3 = time.monotonic()
        # At least one of the two calls should have been delayed noticeably
        total_slow = (t2 - t1) + (t3 - t2)
        assert total_slow >= 2.0


# ---------------------------------------------------------------------------
# BaseTool — loud failure
# ---------------------------------------------------------------------------


class TestBaseToolLoudFailure:
    def test_failing_run_raises_tool_call_error(self) -> None:
        tool = _DummyFailingTool()
        with pytest.raises(ToolCallError) as exc:
            tool("hello")
        assert "failing" in str(exc.value)
        assert "intentional failure" in str(exc.value)

    def test_no_synthetic_data_on_failure(self) -> None:
        tool = _DummyFailingTool()
        with pytest.raises(ToolCallError):
            tool("world")
        # The error propagates; no result is returned (FM-11).


# ---------------------------------------------------------------------------
# BaseTool — audit
# ---------------------------------------------------------------------------


class TestBaseToolAudit:
    def test_emits_audit_event_on_success(self) -> None:
        tmpdir = Path(mkdtemp())
        audit_path = tmpdir / "audit.jsonl"
        audit = AuditTrail(audit_path)
        tool = _DummyCounterTool(audit=audit)

        tool(42)

        events = audit.replay()
        assert len(events) == 1
        assert events[0].type == "tool.called"
        assert events[0].payload["tool"] == "counter"

    def test_emits_audit_event_on_failure(self) -> None:
        tmpdir = Path(mkdtemp())
        audit_path = tmpdir / "audit.jsonl"
        audit = AuditTrail(audit_path)
        tool = _DummyFailingTool(audit=audit)

        with pytest.raises(ToolCallError):
            tool("boom")

        events = audit.replay()
        # At least one "tool.failed" event (possibly preceded by retries)
        failed_types = [e.type for e in events]
        assert "tool.failed" in failed_types

    def test_no_audit_without_trail(self) -> None:
        tool = _DummyCounterTool(audit=None)
        tool(1)
        # No error — audit is optional
        assert tool.call_count == 1


# ---------------------------------------------------------------------------
# BaseAgent
# ---------------------------------------------------------------------------


class _ConcreteAgent(BaseAgent):
    """Minimal concrete agent for testing."""
    name = "test_agent"
    tools = []

    def act(self, state: AgentState) -> AgentState:
        state.tool_outputs.append({"agent": "ran"})
        return state


class TestBaseAgentDispatch:
    def test_calls_tool_and_records_output(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = _ConcreteAgent(
            llm=MockProvider(),
            tools=[_DummyAddTool(audit=audit)],
            audit=audit,
        )
        state = AgentState(query="add 1+2")
        result = agent._call_tool(state, "add", (1, 2))

        assert result == 3
        assert len(state.tool_outputs) == 1
        assert state.tool_outputs[0]["tool"] == "add"

    def test_uknown_tool_raises(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = _ConcreteAgent(
            llm=MockProvider(),
            tools=[_DummyAddTool(audit=audit)],
            audit=audit,
        )
        state = AgentState(query="unknown")
        with pytest.raises(ValueError, match="no tool named"):
            agent._call_tool(state, "nonexistent", 1)

    def test_act_is_abstract(self) -> None:
        # BaseAgent itself cannot be instantiated.
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        with pytest.raises(TypeError):
            BaseAgent(  # type: ignore[abstract]
                llm=MockProvider(),
                tools=[],
                audit=audit,
            )

    def test_concrete_agent_act_works(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = _ConcreteAgent(
            llm=MockProvider(),
            tools=[],
            audit=audit,
        )
        state = AgentState(query="hello")
        result = agent.act(state)
        assert result.tool_outputs == [{"agent": "ran"}]


class TestBaseAgentInit:
    def test_init_required_fields(self) -> None:
        tmpdir = Path(mkdtemp())
        audit = AuditTrail(tmpdir / "audit.jsonl")
        agent = _ConcreteAgent(
            llm=MockProvider(),
            tools=[],
            audit=audit,
        )
        assert agent.name == "test_agent"
        assert agent.tools == []
        assert agent.llm is not None
        assert agent.audit is not None
