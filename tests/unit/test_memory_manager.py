"""Tests for :mod:`finroot.memory.manager` (wave-2, task 04).

Covers
------
* Construction validation (types, empty ``user_id``).
* Working-memory delegation (``add_turn`` / ``get_context``).
* Auto-remember threshold (> 50 chars → semantic; ≤ 50 → not).
* Explicit ``remember`` / ``recall`` delegation and validation.
* Twin read/write (``get_twin`` raises ``KeyError`` when missing).
* ``update_twin`` partial update, persistence, reserved-field rejection.
* ``create`` factory end-to-end.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from finroot.memory.digital_twin import (
    DigitalTwin,
    DigitalTwinStore,
    InvestmentHorizon,
    RiskTolerance,
)
from finroot.memory.manager import (
    _AUTO_REMEMBER_MIN_CHARS,
    MemoryManager,
)
from finroot.memory.semantic import SemanticMemory
from finroot.memory.working import WorkingMemory

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fallback_semantic(monkeypatch: pytest.MonkeyPatch) -> SemanticMemory:
    """Force the JSON-fallback semantic store (no chromadb)."""
    monkeypatch.setitem(sys.modules, "chromadb", None)
    return SemanticMemory()


@pytest.fixture()
def twin_store() -> DigitalTwinStore:
    """Fresh SQLite store in a temp file; cleaned up automatically."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = DigitalTwinStore(db_path=path)
    yield store
    Path(path).unlink(missing_ok=True)
    Path(path + ".json").unlink(missing_ok=True)


@pytest.fixture()
def fake_working() -> WorkingMemory:
    return WorkingMemory(max_turns=10)


def _make_twin(**kwargs: object) -> DigitalTwin:
    fields: dict[str, object] = {
        "user_id": "user-1",
        "name": "Test User",
        "age": 30,
        "risk_tolerance": RiskTolerance.MODERATE,
        "investment_horizon": InvestmentHorizon.MEDIUM,
        "monthly_income": 10000.0,
        "monthly_expenses": 5000.0,
        "tax_bracket_pct": 20.0,
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }
    fields.update(kwargs)
    return DigitalTwin(**fields)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_basic_construction(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            working=fake_working,
            semantic=fallback_semantic,
            twin_store=twin_store,
            user_id="u-1",
        )
        assert mgr.user_id == "u-1"
        assert mgr.working is fake_working
        assert mgr.semantic is fallback_semantic
        assert mgr.twin_store is twin_store

    def test_rejects_non_working(
        self,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        with pytest.raises(TypeError, match="working must be WorkingMemory"):
            MemoryManager(
                working="not a working",  # type: ignore[arg-type]
                semantic=fallback_semantic,
                twin_store=twin_store,
                user_id="u",
            )

    def test_rejects_non_semantic(
        self,
        fake_working: WorkingMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        with pytest.raises(TypeError, match="semantic must be SemanticMemory"):
            MemoryManager(
                working=fake_working,
                semantic=42,  # type: ignore[arg-type]
                twin_store=twin_store,
                user_id="u",
            )

    def test_rejects_non_twin_store(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
    ) -> None:
        with pytest.raises(TypeError, match="twin_store must be DigitalTwinStore"):
            MemoryManager(
                working=fake_working,
                semantic=fallback_semantic,
                twin_store=[],  # type: ignore[arg-type]
                user_id="u",
            )

    def test_rejects_empty_user_id(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        with pytest.raises(ValueError, match="user_id must be a non-empty string"):
            MemoryManager(
                working=fake_working,
                semantic=fallback_semantic,
                twin_store=twin_store,
                user_id="",
            )

    def test_rejects_non_string_user_id(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        with pytest.raises(TypeError, match="user_id must be str"):
            MemoryManager(
                working=fake_working,
                semantic=fallback_semantic,
                twin_store=twin_store,
                user_id=123,  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# Working-memory delegation + auto-remember
# ---------------------------------------------------------------------------


class TestAddTurnAndAutoRemember:
    def test_add_turn_delegates_to_working(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.add_turn("user", "hi")
        mgr.add_turn("assistant", "hello there")
        assert mgr.get_context() == [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello there"},
        ]

    def test_short_turn_not_auto_remembered(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.add_turn("user", "hi")
        # 2 chars — well below threshold; semantic store must be empty
        assert fallback_semantic.search("hi", k=10) == []

    def test_empty_turn_not_auto_remembered(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.add_turn("user", "")
        assert fallback_semantic.search("", k=10) == []

    def test_exactly_50_chars_not_auto_remembered(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        """Threshold is strictly greater-than 50, so 50 chars must NOT be remembered."""
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        content = "x" * 50
        assert len(content) == _AUTO_REMEMBER_MIN_CHARS  # 50
        mgr.add_turn("user", content)
        # The working buffer has it
        assert mgr.get_context() == [{"role": "user", "content": content}]
        # …but the semantic store does not
        assert fallback_semantic.search(content, k=10) == []

    def test_51_chars_is_auto_remembered(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        content = "x" * 51
        mgr.add_turn("user", content)
        results = fallback_semantic.search(content, k=5)
        assert len(results) == 1
        assert results[0]["text"] == content
        assert results[0]["metadata"]["user_id"] == "u-1"
        assert results[0]["metadata"]["role"] == "user"
        assert results[0]["metadata"]["source"] == "auto_remember"

    def test_long_turn_auto_remember_metadata_includes_role(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.add_turn(
            "assistant",
            "Here is a long, detailed explanation that should be remembered.",
        )
        results = fallback_semantic.search("detailed explanation", k=5)
        assert len(results) == 1
        assert results[0]["metadata"]["role"] == "assistant"

    def test_add_turn_validates_role(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        with pytest.raises(ValueError, match="role must be one of"):
            mgr.add_turn("system", "hello")
        # the failed add must not have polluted either store
        assert mgr.get_context() == []

    def test_add_turn_validates_content_type(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        with pytest.raises(TypeError, match="content must be str"):
            mgr.add_turn("user", 123)  # type: ignore[arg-type]

    def test_get_context_returns_fresh_list(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.add_turn("user", "hi")
        ctx = mgr.get_context()
        ctx.clear()
        ctx.append({"role": "tool", "content": "tampered"})
        # manager's view is unaffected
        assert mgr.get_context() == [{"role": "user", "content": "hi"}]


# ---------------------------------------------------------------------------
# remember / recall
# ---------------------------------------------------------------------------


class TestRememberAndRecall:
    def test_remember_returns_doc_id(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        doc_id = mgr.remember("market outlook is bullish this quarter")
        assert isinstance(doc_id, str)
        assert len(doc_id) == 36  # UUID

    def test_remember_metadata_none_treated_as_empty(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.remember("just the text", metadata=None)
        results = fallback_semantic.search("just the text", k=1)
        assert len(results) == 1
        assert results[0]["text"] == "just the text"
        # user_id is always injected by the manager, even when caller omits metadata
        assert results[0]["metadata"]["user_id"] == "u-1"

    def test_remember_caller_metadata_is_preserved(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.remember("rupee depreciation risk", metadata={"source": "news", "year": 2026})
        results = fallback_semantic.search("rupee", k=1)
        assert results[0]["metadata"]["source"] == "news"
        assert results[0]["metadata"]["year"] == 2026
        assert results[0]["metadata"]["user_id"] == "u-1"

    def test_remember_rejects_non_string_text(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        with pytest.raises(TypeError, match="text must be str"):
            mgr.remember(123)  # type: ignore[arg-type]

    def test_recall_delegates(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        mgr.remember("equity markets are volatile right now")
        mgr.remember("bond yields are rising globally")
        results = mgr.recall("volatile equity", k=2)
        assert len(results) == 2
        assert results[0]["text"] == "equity markets are volatile right now"

    def test_recall_default_k_is_5(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        for i in range(8):
            mgr.remember(f"document {i} about finance topic number {i}")
        results = mgr.recall("document finance")
        assert len(results) == 5  # default k=5

    def test_recall_empty_store_returns_empty_list(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        assert mgr.recall("anything", k=3) == []

    def test_recall_validates_k(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        with pytest.raises(ValueError, match="k must be >= 1"):
            mgr.recall("q", k=0)
        with pytest.raises(TypeError, match="k must be int"):
            mgr.recall("q", k=2.5)  # type: ignore[arg-type]

    def test_recall_validates_query_type(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        with pytest.raises(TypeError, match="query must be str"):
            mgr.recall(123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Digital twin
# ---------------------------------------------------------------------------


class TestGetAndUpdateTwin:
    def test_get_twin_loads(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        twin_store.save(_make_twin(user_id="u-1", name="Aarav"))
        twin = mgr.get_twin()
        assert twin.user_id == "u-1"
        assert twin.name == "Aarav"

    def test_get_twin_missing_raises_key_error(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "ghost"
        )
        with pytest.raises(KeyError, match="not found"):
            mgr.get_twin()

    def test_update_twin_partial_update(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        twin_store.save(_make_twin(user_id="u-1", name="Aarav", age=30))
        updated = mgr.update_twin(age=31, monthly_income=15000.0)
        assert updated.age == 31
        assert updated.monthly_income == 15000.0
        # other fields unchanged
        assert updated.name == "Aarav"
        assert updated.user_id == "u-1"
        assert updated.risk_tolerance is RiskTolerance.MODERATE

    def test_update_twin_persists_across_reload(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        twin_store.save(_make_twin(user_id="u-1"))
        mgr.update_twin(
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            goals=["retire by 50", "buy beach house"],
        )
        # new manager bound to the same store must see the change
        mgr2 = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        reloaded = mgr2.get_twin()
        assert reloaded.risk_tolerance is RiskTolerance.AGGRESSIVE
        assert reloaded.goals == ["retire by 50", "buy beach house"]

    def test_update_twin_missing_raises_key_error(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "ghost"
        )
        with pytest.raises(KeyError, match="not found"):
            mgr.update_twin(age=40)

    def test_update_twin_rejects_user_id_change(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        """Changing ``user_id`` would orphan the persisted row — fail loud."""
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        twin_store.save(_make_twin(user_id="u-1"))
        with pytest.raises(ValueError, match="reserved fields"):
            mgr.update_twin(user_id="u-2")
        # the original twin must still be at u-1, untouched
        assert mgr.get_twin().user_id == "u-1"

    def test_update_twin_rejects_unknown_field(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        twin_store.save(_make_twin(user_id="u-1"))
        with pytest.raises(ValidationError):
            mgr.update_twin(unknown_field="nope")

    def test_update_twin_rejects_out_of_range_age(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        twin_store.save(_make_twin(user_id="u-1", age=30))
        with pytest.raises(ValidationError):
            mgr.update_twin(age=200)

    def test_update_twin_refreshes_updated_at(
        self,
        fake_working: WorkingMemory,
        fallback_semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
    ) -> None:
        mgr = MemoryManager(
            fake_working, fallback_semantic, twin_store, "u-1"
        )
        original = _make_twin(user_id="u-1", age=30)
        twin_store.save(original)
        before = mgr.get_twin().updated_at
        # force a measurable gap on systems with low-resolution clocks
        import time

        time.sleep(0.01)
        updated = mgr.update_twin(age=31)
        assert updated.updated_at >= before


# ---------------------------------------------------------------------------
# create() factory
# ---------------------------------------------------------------------------


class TestCreateFactory:
    def test_create_returns_manager_with_default_paths(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setitem(sys.modules, "chromadb", None)
        monkeypatch.chdir(tmp_path)  # isolate default relative data paths
        mgr = MemoryManager.create(user_id="u-1")
        assert isinstance(mgr, MemoryManager)
        assert mgr.user_id == "u-1"
        assert isinstance(mgr.working, WorkingMemory)
        assert isinstance(mgr.semantic, SemanticMemory)
        assert isinstance(mgr.twin_store, DigitalTwinStore)

    def test_create_with_custom_paths(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setitem(sys.modules, "chromadb", None)
        chroma_dir = tmp_path / "chroma"
        db_path = str(tmp_path / "twin.db")
        mgr = MemoryManager.create(
            user_id="u-2", chroma_dir=str(chroma_dir), db_path=db_path
        )
        # twin store must point at the custom path
        assert mgr.twin_store._db_path == db_path
        # get_twin on an empty store raises — proves the store is wired
        with pytest.raises(KeyError):
            mgr.get_twin()

    def test_create_max_turns_propagates(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setitem(sys.modules, "chromadb", None)
        monkeypatch.chdir(tmp_path)
        mgr = MemoryManager.create(user_id="u-1", max_turns=3)
        assert mgr.working.max_turns == 3

    def test_create_persists_twin_across_instances(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setitem(sys.modules, "chromadb", None)
        db_path = str(tmp_path / "twin.db")
        mgr1 = MemoryManager.create(user_id="alice", db_path=db_path)
        mgr1.twin_store.save(_make_twin(user_id="alice", name="Alice", age=30))
        mgr1.update_twin(age=42, name="Alice")
        # New instance bound to the same store sees the same twin
        mgr2 = MemoryManager.create(user_id="alice", db_path=db_path)
        twin = mgr2.get_twin()
        assert twin.name == "Alice"
        assert twin.age == 42


# ---------------------------------------------------------------------------
# Mock-based delegation sanity (proves we don't accidentally wrap calls)
# ---------------------------------------------------------------------------


class TestMockDelegation:
    """White-box delegation tests with mocks — catches accidental reimplementation."""

    def test_add_turn_calls_working_add_and_passes_role_content(
        self,
    ) -> None:
        working = MagicMock(spec=WorkingMemory)
        semantic = MagicMock(spec=SemanticMemory)
        twin_store = MagicMock(spec=DigitalTwinStore)
        mgr = MemoryManager(working, semantic, twin_store, "u-1")
        mgr.add_turn("user", "x" * 51)
        working.add.assert_called_once_with("user", "x" * 51)
        semantic.add.assert_called_once()
        # metadata must include user_id and role
        meta = semantic.add.call_args.args[1]
        assert meta["user_id"] == "u-1"
        assert meta["role"] == "user"

    def test_add_turn_short_skips_semantic(self) -> None:
        working = MagicMock(spec=WorkingMemory)
        semantic = MagicMock(spec=SemanticMemory)
        twin_store = MagicMock(spec=DigitalTwinStore)
        mgr = MemoryManager(working, semantic, twin_store, "u-1")
        mgr.add_turn("user", "short")
        working.add.assert_called_once_with("user", "short")
        semantic.add.assert_not_called()

    def test_get_context_calls_working_get_messages(self) -> None:
        working = MagicMock(spec=WorkingMemory)
        working.get_messages.return_value = [{"role": "user", "content": "x"}]
        semantic = MagicMock(spec=SemanticMemory)
        twin_store = MagicMock(spec=DigitalTwinStore)
        mgr = MemoryManager(working, semantic, twin_store, "u-1")
        assert mgr.get_context() == [{"role": "user", "content": "x"}]
        working.get_messages.assert_called_once_with()

    def test_remember_calls_semantic_add_with_user_id(self) -> None:
        working = MagicMock(spec=WorkingMemory)
        semantic = MagicMock(spec=SemanticMemory)
        semantic.add.return_value = "doc-1"
        twin_store = MagicMock(spec=DigitalTwinStore)
        mgr = MemoryManager(working, semantic, twin_store, "u-1")
        doc_id = mgr.remember("hello", metadata={"src": "x"})
        assert doc_id == "doc-1"
        semantic.add.assert_called_once_with("hello", {"src": "x", "user_id": "u-1"})

    def test_recall_calls_semantic_search(self) -> None:
        working = MagicMock(spec=WorkingMemory)
        semantic = MagicMock(spec=SemanticMemory)
        semantic.search.return_value = [{"text": "t", "metadata": {}, "score": 0.5}]
        twin_store = MagicMock(spec=DigitalTwinStore)
        mgr = MemoryManager(working, semantic, twin_store, "u-1")
        results = mgr.recall("q", k=3)
        assert results == [{"text": "t", "metadata": {}, "score": 0.5}]
        semantic.search.assert_called_once_with("q", 3)

    def test_get_twin_calls_twin_store_load_with_user_id(self) -> None:
        working = MagicMock(spec=WorkingMemory)
        semantic = MagicMock(spec=SemanticMemory)
        twin_store = MagicMock(spec=DigitalTwinStore)
        sentinel = _make_twin(user_id="u-1")
        twin_store.load.return_value = sentinel
        mgr = MemoryManager(working, semantic, twin_store, "u-1")
        assert mgr.get_twin() is sentinel
        twin_store.load.assert_called_once_with("u-1")

    def test_update_twin_calls_load_copy_save_in_order(self) -> None:
        working = MagicMock(spec=WorkingMemory)
        semantic = MagicMock(spec=SemanticMemory)
        twin_store = MagicMock(spec=DigitalTwinStore)
        existing = _make_twin(user_id="u-1", age=30)
        twin_store.load.return_value = existing
        mgr = MemoryManager(working, semantic, twin_store, "u-1")
        result = mgr.update_twin(age=31)
        twin_store.load.assert_called_once_with("u-1")
        twin_store.save.assert_called_once()
        saved = twin_store.save.call_args.args[0]
        assert saved.age == 31
        assert result.age == 31
        # returned twin must be the saved one
        assert result is saved


# ---------------------------------------------------------------------------
# Indirect sanity: sqlite schema is created (delegated check)
# ---------------------------------------------------------------------------


def test_create_factory_creates_sqlite_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setitem(sys.modules, "chromadb", None)
    db_path = str(tmp_path / "twin.db")
    mgr = MemoryManager.create(user_id="u-1", db_path=db_path)
    # SQL-level check that the table exists
    conn = sqlite3.connect(mgr.twin_store._db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    finally:
        conn.close()
    table_names = {r[0] for r in rows}
    assert "digital_twins" in table_names
