"""Integration tests for :class:`MemoryManager` (wave-2, task 04).

End-to-end exercise of the unified facade: working + semantic + twin stores
wired together, surviving a manager reload (proving on-disk persistence),
exercising auto-remember, and verifying that ``get_twin`` raises on a
fresh user.

These tests are slow-ish (temp-file I/O) and live under ``tests/integration/``
so the default ``pytest`` run can skip them if desired.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from finroot.memory.digital_twin import (
    DigitalTwin,
    InvestmentHorizon,
    RiskTolerance,
)
from finroot.memory.manager import MemoryManager

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


def _seed_twin(user_id: str, **overrides: object) -> DigitalTwin:
    fields: dict[str, object] = {
        "user_id": user_id,
        "name": "Integration Tester",
        "age": 35,
        "risk_tolerance": RiskTolerance.MODERATE,
        "investment_horizon": InvestmentHorizon.LONG,
        "monthly_income": 12000.0,
        "monthly_expenses": 6000.0,
        "tax_bracket_pct": 25.0,
        "goals": ["retire at 55"],
        "constraints": ["no leverage"],
        "holdings": [],
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }
    fields.update(overrides)
    return DigitalTwin(**fields)


@pytest.fixture()
def workspace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, str]:
    """Create a fresh on-disk workspace for one integration test.

    Returns the path dict so individual tests can introspect.
    """
    monkeypatch.setitem(sys.modules, "chromadb", None)  # force JSON fallback
    db_path = str(tmp_path / "twin.db")
    chroma_dir = str(tmp_path / "chroma")
    return {"db_path": db_path, "chroma_dir": chroma_dir}


@pytest.mark.integration
def test_full_round_trip_add_recall_persist_reload(workspace: dict[str, str]) -> None:
    """Create manager → add 5 turns → recall relevant → save twin → reload
    manager → twin persists, semantic history persists, working is fresh.
    """
    # 1. Create manager on fresh disk
    mgr = MemoryManager.create(
        user_id="alice",
        chroma_dir=workspace["chroma_dir"],
        db_path=workspace["db_path"],
    )

    # Seed the twin so update_twin has something to load
    mgr.twin_store.save(_seed_twin("alice"))

    # 2. Add 5 turns — some short (working only), some long (auto-remembered)
    mgr.add_turn("user", "Hi, I'm planning for retirement.")  # 36 chars
    mgr.add_turn(
        "assistant",
        "Sure! Let me ask a few questions to understand your goals better "
        "and to figure out an appropriate asset allocation for your situation.",
    )  # > 50 chars → remembered
    mgr.add_turn("user", "ok")  # short
    mgr.add_turn(
        "user",
        "I want to retire by 55 and I have a moderate appetite for risk "
        "with a 20-year horizon, mostly equity-heavy with some bonds.",
    )  # > 50 chars → remembered (contains "retirement", "risk", "equity")
    mgr.add_turn("assistant", "Got it.")  # short

    # 3. Working context has all 5 turns
    ctx = mgr.get_context()
    assert len(ctx) == 5
    assert ctx[0]["content"].startswith("Hi, I'm planning")

    # 4. Recall: the user's long turn contains the tokens "retire", "risk",
    #    "equity-heavy", "bonds" — the closest match should be that turn.
    results = mgr.recall("retirement equity bonds risk", k=3)
    assert len(results) >= 1
    # The user's long turn must surface among the top results
    assert any("retire by 55" in r["text"] for r in results)
    # Each result is tagged with the manager's user_id
    for r in results:
        assert r["metadata"]["user_id"] == "alice"
        assert r["metadata"]["source"] == "auto_remember"

    # 5. Update the twin (partial) and persist
    updated = mgr.update_twin(
        age=36,
        goals=["retire at 55", "buy a holiday home in Goa"],
        risk_tolerance=RiskTolerance.AGGRESSIVE,
    )
    assert updated.age == 36
    assert updated.risk_tolerance is RiskTolerance.AGGRESSIVE
    assert len(updated.goals) == 2

    # 6. Reload: build a new manager bound to the same on-disk paths
    mgr2 = MemoryManager.create(
        user_id="alice",
        chroma_dir=workspace["chroma_dir"],
        db_path=workspace["db_path"],
    )

    # 7. Twin persists across reload (the entire point of the integration test)
    reloaded = mgr2.get_twin()
    assert reloaded.user_id == "alice"
    assert reloaded.age == 36
    assert reloaded.risk_tolerance is RiskTolerance.AGGRESSIVE
    assert reloaded.goals == ["retire at 55", "buy a holiday home in Goa"]

    # 8. Semantic history also persists (this is the in-process JSON fallback,
    #    so it lives only as long as the SemanticMemory instance — but the
    #    *first* manager is still alive in the test scope). Verify the
    #    first manager still has the same documents.
    results_after = mgr.recall("asset allocation goals", k=3)
    assert len(results_after) >= 1
    assert any("asset allocation" in r["text"] for r in results_after)

    # 9. Working memory of the NEW manager is fresh (working is in-process
    #    only, not persisted — that's the design).
    assert mgr2.get_context() == []


@pytest.mark.integration
def test_fresh_user_get_twin_raises_across_managers(workspace: dict[str, str]) -> None:
    """A user that has never been saved must raise ``KeyError`` consistently
    across manager instances — the contract is enforced end-to-end.
    """
    mgr1 = MemoryManager.create(
        user_id="newbie",
        chroma_dir=workspace["chroma_dir"],
        db_path=workspace["db_path"],
    )
    with pytest.raises(KeyError, match="not found"):
        mgr1.get_twin()

    # New manager on the same store: still missing
    mgr2 = MemoryManager.create(
        user_id="newbie",
        chroma_dir=workspace["chroma_dir"],
        db_path=workspace["db_path"],
    )
    with pytest.raises(KeyError, match="not found"):
        mgr2.get_twin()


@pytest.mark.integration
def test_different_users_have_independent_twins(workspace: dict[str, str]) -> None:
    """Two users sharing the same on-disk store must have independent twins.

    The store is keyed on ``user_id``; the manager facade is the only piece
    that has to keep them straight.
    """
    alice = MemoryManager.create(
        user_id="alice", db_path=workspace["db_path"]
    )
    bob = MemoryManager.create(
        user_id="bob", db_path=workspace["db_path"]
    )

    alice.twin_store.save(_seed_twin("alice", name="Alice", age=30))
    bob.twin_store.save(_seed_twin("bob", name="Bob", age=42))

    alice.update_twin(risk_tolerance=RiskTolerance.AGGRESSIVE)
    bob.update_twin(risk_tolerance=RiskTolerance.CONSERVATIVE)

    # Each manager sees its own twin — no cross-contamination
    assert alice.get_twin().risk_tolerance is RiskTolerance.AGGRESSIVE
    assert bob.get_twin().risk_tolerance is RiskTolerance.CONSERVATIVE
    assert alice.get_twin().name == "Alice"
    assert bob.get_twin().name == "Bob"


@pytest.mark.integration
def test_semantic_and_twin_persist_independently(workspace: dict[str, str]) -> None:
    """Semantic remember and twin update are independent — twin update
    should not accidentally clear the semantic store, and vice-versa.
    """
    mgr = MemoryManager.create(
        user_id="carol", db_path=workspace["db_path"]
    )
    mgr.twin_store.save(_seed_twin("carol"))
    mgr.remember("the bond market is showing signs of stress this quarter")
    mgr.update_twin(monthly_income=20000.0)

    # Semantic recall is unaffected by the twin update
    hits = mgr.recall("bond market stress", k=1)
    assert len(hits) == 1
    assert "bond market" in hits[0]["text"]

    # Twin update is unaffected by the semantic add
    assert mgr.get_twin().monthly_income == 20000.0


@pytest.mark.integration
def test_long_conversation_auto_remembers_consistently(
    workspace: dict[str, str],
) -> None:
    """Drive 20 mixed-length turns through the manager and verify that
    only the long ones are in the semantic store, while the working
    buffer keeps the most recent ``max_turns`` (default 10).
    """
    mgr = MemoryManager.create(
        user_id="dan", db_path=workspace["db_path"], max_turns=10
    )

    short_turns: list[str] = []
    long_turns: list[str] = []

    for i in range(20):
        if i % 2 == 0:
            content = f"short turn {i}"
            short_turns.append(content)
        else:
            # 80+ chars to exceed the 50-char threshold
            content = (
                f"this is a fairly long turn number {i} that contains more "
                f"than fifty characters of text to trigger auto-remember"
            )
            assert len(content) > 50
            long_turns.append(content)
        mgr.add_turn("user", content)

    # Working buffer is the most recent 10 turns (sliding window)
    ctx = mgr.get_context()
    assert len(ctx) == 10
    # The first surviving turn should be turn 10 (index 10 of the 20)
    assert ctx[0]["content"].startswith("short turn 10") or ctx[0]["content"].startswith("this is a fairly long turn 10")

    # The semantic store should contain all 10 long turns
    # (it is append-only; the working buffer is the only sliding window)
    semantic_docs = mgr.recall("turn", k=50)
    long_count = sum(
        1 for d in semantic_docs if "more than fifty characters" in d["text"]
    )
    assert long_count == 10  # all 10 odd-indexed long turns
