"""Wave-1 smoke test — prints FOUNDATION OK and exits 0 or fails loud.

Exercises every task-01–05 module end-to-end with no external dependencies
(Mock provider, in-memory audit trail on a tmp file).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Ensure project root is on sys.path so `config/` package is importable
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _fail(msg: str) -> None:
    print(f"FOUNDATION FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def test_llm_mock() -> None:
    from finroot.llm import get_provider

    provider = get_provider("mock")
    result = provider.complete("What is the risk of holding 100% equities?")
    if not result.text:
        _fail("MockProvider returned empty text")


def test_audit_chain() -> None:
    from finroot.audit.trail import AuditTrail

    with tempfile.TemporaryDirectory() as tmp:
        trail = AuditTrail(path=Path(tmp) / "audit.jsonl")
        trail.append("smoke.event_1", {"step": 1, "msg": "foundation check"})
        trail.append("smoke.event_2", {"step": 2, "msg": "chain verify"})
        if not trail.verify_chain():
            _fail("AuditTrail.verify_chain() returned False after 2 events")
        events = trail.replay()
        if len(events) != 2:
            _fail(f"Expected 2 replay events, got {len(events)}")


def test_agent_state_roundtrip() -> None:
    from finroot.schemas import AgentState

    state = AgentState(query="Should I buy AAPL?")
    serialised = state.model_dump_json()
    state2 = AgentState.model_validate_json(serialised)
    if state2.query != state.query:
        _fail("AgentState round-trip query mismatch")


def test_base_interfaces() -> None:
    from finroot.agents.base import BaseAgent
    from finroot.tools.base import BaseTool

    if not issubclass(BaseTool, object):
        _fail("BaseTool not a class")
    if not issubclass(BaseAgent, object):
        _fail("BaseAgent not a class")


def main() -> None:
    steps = [
        ("LLM Mock provider", test_llm_mock),
        ("Audit chain (append + verify)", test_audit_chain),
        ("AgentState round-trip", test_agent_state_roundtrip),
        ("BaseTool / BaseAgent interfaces", test_base_interfaces),
    ]
    for name, fn in steps:
        try:
            fn()
            print(f"  OK  {name}")
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            _fail(f"{name} raised {type(exc).__name__}: {exc}")

    print("\nFOUNDATION OK")


if __name__ == "__main__":
    main()
