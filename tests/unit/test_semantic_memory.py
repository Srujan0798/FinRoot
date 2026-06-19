"""Tests for SemanticMemory — ChromaDB path (mocked) and JSON fallback."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from finroot.memory.semantic import (
    SemanticMemory,
    _cosine_similarity,
    _JsonFallbackStore,
    _tokenize,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fallback_only(monkeypatch: pytest.MonkeyPatch) -> SemanticMemory:
    """Force the JSON fallback path by making chromadb unimportable."""
    monkeypatch.setitem(sys.modules, "chromadb", None)
    return SemanticMemory()


@pytest.fixture()
def mock_chroma(monkeypatch: pytest.MonkeyPatch) -> tuple[SemanticMemory, MagicMock]:
    """Provide a SemanticMemory that uses a mocked chromadb."""
    mock_collection = MagicMock()
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient.return_value = mock_client

    monkeypatch.setitem(sys.modules, "chromadb", mock_chromadb)
    mem = SemanticMemory(persist_dir="/tmp/test_chroma", collection="test")
    return mem, mock_collection


# ---------------------------------------------------------------------------
# JSON Fallback Store (direct unit tests)
# ---------------------------------------------------------------------------


class TestJsonFallbackStore:
    def test_add_returns_uuid_string(self) -> None:
        store = _JsonFallbackStore()
        doc_id = store.add("hello world", {"key": "val"})
        assert isinstance(doc_id, str)
        assert len(doc_id) == 36  # UUID format

    def test_search_round_trip(self) -> None:
        store = _JsonFallbackStore()
        store.add("python programming language", {"topic": "tech"})
        store.add("cooking pasta recipe", {"topic": "food"})
        results = store.search("python code", k=2)
        assert len(results) == 2
        assert results[0]["text"] == "python programming language"
        assert results[0]["score"] > 0

    def test_search_empty_store_returns_empty(self) -> None:
        store = _JsonFallbackStore()
        assert store.search("anything", k=5) == []

    def test_delete_removes_doc(self) -> None:
        store = _JsonFallbackStore()
        doc_id = store.add("to be deleted", {"x": 1})
        store.add("keep me", {"x": 2})
        store.delete(doc_id)
        results = store.search("deleted", k=10)
        assert all(r["text"] != "to be deleted" for r in results)

    def test_clear_removes_all(self) -> None:
        store = _JsonFallbackStore()
        store.add("doc one", {})
        store.add("doc two", {})
        store.clear()
        assert store.search("doc", k=10) == []

    def test_k_limits_results(self) -> None:
        store = _JsonFallbackStore()
        for i in range(10):
            store.add(f"document number {i}", {"idx": i})
        results = store.search("document", k=3)
        assert len(results) == 3

    def test_metadata_preserved(self) -> None:
        store = _JsonFallbackStore()
        meta = {"source": "test", "year": 2024, "nested": {"a": 1}}
        store.add("some text", meta)
        results = store.search("some text", k=1)
        assert results[0]["metadata"] == meta


# ---------------------------------------------------------------------------
# Tokenize / Cosine helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_tokenize_lowercases_and_splits(self) -> None:
        assert _tokenize("Hello World") == ["hello", "world"]

    def test_cosine_identical_vectors(self) -> None:
        v = {"a": 1.0, "b": 2.0}
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_cosine_orthogonal_vectors(self) -> None:
        a = {"a": 1.0}
        b = {"b": 1.0}
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_cosine_empty_vectors(self) -> None:
        assert _cosine_similarity({}, {"a": 1.0}) == 0.0
        assert _cosine_similarity({"a": 1.0}, {}) == 0.0


# ---------------------------------------------------------------------------
# SemanticMemory — JSON fallback path (chromadb absent)
# ---------------------------------------------------------------------------


class TestSemanticMemoryFallback:
    def test_uses_fallback_when_chromadb_missing(self, fallback_only: SemanticMemory) -> None:
        assert fallback_only._use_chroma is False

    def test_add_returns_doc_id(self, fallback_only: SemanticMemory) -> None:
        doc_id = fallback_only.add("hello", {"k": "v"})
        assert isinstance(doc_id, str)
        assert len(doc_id) == 36

    def test_search_returns_results(self, fallback_only: SemanticMemory) -> None:
        fallback_only.add("machine learning algorithms", {"domain": "ml"})
        fallback_only.add("stock market analysis", {"domain": "finance"})
        results = fallback_only.search("machine learning", k=2)
        assert len(results) == 2
        assert results[0]["text"] == "machine learning algorithms"
        assert isinstance(results[0]["score"], float)

    def test_search_empty_returns_empty_list(self, fallback_only: SemanticMemory) -> None:
        assert fallback_only.search("no docs", k=5) == []

    def test_delete(self, fallback_only: SemanticMemory) -> None:
        doc_id = fallback_only.add("ephemeral", {})
        fallback_only.add("permanent", {})
        fallback_only.delete(doc_id)
        results = fallback_only.search("ephemeral", k=10)
        assert all(r["text"] != "ephemeral" for r in results)

    def test_clear(self, fallback_only: SemanticMemory) -> None:
        fallback_only.add("a", {})
        fallback_only.add("b", {})
        fallback_only.clear()
        assert fallback_only.search("a", k=10) == []
        assert fallback_only.search("b", k=10) == []


# ---------------------------------------------------------------------------
# SemanticMemory — ChromaDB path (mocked)
# ---------------------------------------------------------------------------


class TestSemanticMemoryChroma:
    def test_uses_chroma_when_available(self, mock_chroma: tuple[SemanticMemory, MagicMock]) -> None:
        mem, _ = mock_chroma
        assert mem._use_chroma is True

    def test_add_calls_chroma(self, mock_chroma: tuple[SemanticMemory, MagicMock]) -> None:
        mem, mock_col = mock_chroma
        doc_id = mem.add("test doc", {"key": "val"})
        assert isinstance(doc_id, str)
        mock_col.add.assert_called_once()
        call_kwargs = mock_col.add.call_args
        assert call_kwargs.kwargs["documents"] == ["test doc"]
        assert call_kwargs.kwargs["metadatas"] == [{"key": "val"}]

    def test_search_calls_chroma(self, mock_chroma: tuple[SemanticMemory, MagicMock]) -> None:
        mem, mock_col = mock_chroma
        mock_col.query.return_value = {
            "documents": [["result doc"]],
            "metadatas": [[{"k": "v"}]],
            "distances": [[0.5]],
        }
        results = mem.search("query", k=3)
        mock_col.query.assert_called_once_with(query_texts=["query"], n_results=3)
        assert len(results) == 1
        assert results[0]["text"] == "result doc"
        assert results[0]["score"] == 0.5

    def test_delete_calls_chroma(self, mock_chroma: tuple[SemanticMemory, MagicMock]) -> None:
        mem, mock_col = mock_chroma
        mem.delete("some-id")
        mock_col.delete.assert_called_once_with(ids=["some-id"])

    def test_clear_calls_chroma(self, mock_chroma: tuple[SemanticMemory, MagicMock]) -> None:
        mem, mock_col = mock_chroma
        mock_col.get.return_value = {"ids": ["a", "b"]}
        mem.clear()
        mock_col.get.assert_called_once()
        mock_col.delete.assert_called_once_with(ids=["a", "b"])
