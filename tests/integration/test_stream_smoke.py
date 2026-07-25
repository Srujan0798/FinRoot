"""stream_answer smoke test.

Verifies the streaming entry point yields progress events in the
expected order and includes a final 'result' event with a valid
AgentState. Fast (<5s).
"""

from __future__ import annotations

import pytest

from interface.core import stream_answer


def _event_types(events: list[dict]) -> list[str]:
    return [e.get("type", "?") for e in events]


def test_stream_answer_yields_progress_events() -> None:
    """The stream should yield multiple progress events before the final
    'result' event."""
    events = list(stream_answer("Should I rebalance my 70/30 portfolio?", mock=True))
    assert len(events) >= 3, (
        f"Expected at least 3 stream events, got {len(events)}: {events[:5]}"
    )


def test_stream_answer_first_event_is_status() -> None:
    """The first event should be a 'status' event (intent classification
    or similar), not the final 'result'."""
    events = list(stream_answer("test query", mock=True))
    assert _event_types(events)[0] == "status", (
        f"First event type should be 'status', got {_event_types(events)[0]}: {events[0]}"
    )


def test_stream_answer_last_event_is_result() -> None:
    """The last event should be a 'result' event containing a valid
    AgentState (or, on failure, an 'error' event)."""
    events = list(stream_answer("test query", mock=True))
    last_type = _event_types(events)[-1]
    assert last_type in ("result", "error"), (
        f"Last event should be 'result' or 'error', got {last_type}: {events[-1]}"
    )
    if last_type == "result":
        assert "state" in events[-1], (
            f"'result' event should have 'state' key: {events[-1]}"
        )


def test_stream_answer_rejects_empty_query() -> None:
    """An empty query should raise ValueError (not silently produce
    empty events)."""
    with pytest.raises(ValueError, match="non-empty"):
        list(stream_answer("", mock=True))
    with pytest.raises(ValueError, match="non-empty"):
        list(stream_answer("   ", mock=True))
