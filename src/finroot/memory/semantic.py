"""SemanticMemory — ChromaDB vector store with stdlib TF-IDF fallback."""

from __future__ import annotations

import math
import uuid
from collections import Counter
from typing import Any


class _JsonFallbackStore:
    """In-memory TF-IDF store using stdlib only (no numpy/sklearn)."""

    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []
        self._idf: dict[str, float] = {}
        self._dirty = True

    def add(self, text: str, metadata: dict[str, Any], doc_id: str | None = None) -> str:
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        self._docs.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata,
            "tf_idf": [],
        })
        self._dirty = True
        return doc_id

    def _build_idf(self) -> None:
        if not self._dirty:
            return
        n = len(self._docs)
        if n == 0:
            self._idf = {}
            self._dirty = False
            return
        doc_freq: Counter[str] = Counter()
        for doc in self._docs:
            tokens = _tokenize(doc["text"])
            doc_freq.update(set(tokens))
        self._idf = {term: math.log((n + 1) / (df + 1)) + 1 for term, df in doc_freq.items()}
        for doc in self._docs:
            tokens = _tokenize(doc["text"])
            tf = Counter(tokens)
            total = len(tokens) if tokens else 1
            doc["tf_idf"] = {term: (count / total) * self._idf.get(term, 0.0) for term, count in tf.items()}
        self._dirty = False

    def search(self, query: str, k: int) -> list[dict[str, Any]]:
        self._build_idf()
        if not self._docs:
            return []
        query_tokens = _tokenize(query)
        query_tf = Counter(query_tokens)
        query_total = len(query_tokens) if query_tokens else 1
        query_vec: dict[str, float] = {
            term: (count / query_total) * self._idf.get(term, 0.0)
            for term, count in query_tf.items()
        }
        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self._docs:
            sim = _cosine_similarity(query_vec, doc["tf_idf"])
            scored.append((sim, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[dict[str, Any]] = []
        for score, doc in scored[:k]:
            results.append({
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": round(score, 6),
            })
        return results

    def delete(self, doc_id: str) -> None:
        self._docs = [d for d in self._docs if d["id"] != doc_id]
        self._dirty = True

    def clear(self) -> None:
        self._docs.clear()
        self._idf.clear()
        self._dirty = True


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticMemory:
    """ChromaDB-backed vector store with JSON fallback for offline/Mock mode.

    Lazy-imports ``chromadb`` inside ``__init__`` (G-0b).  If the import fails,
    an in-memory TF-IDF cosine-similarity store is used instead.
    """

    def __init__(self, persist_dir: str = "data/chroma", collection: str = "finroot") -> None:
        self._use_chroma = False
        self._chroma_client: Any = None
        self._collection: Any = None
        self._fallback = _JsonFallbackStore()

        try:
            import chromadb  # type: ignore[import-untyped]

            self._chroma_client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._chroma_client.get_or_create_collection(name=collection)
            self._use_chroma = True
        except ImportError:
            pass

    def add(self, text: str, metadata: dict[str, Any]) -> str:
        doc_id = str(uuid.uuid4())
        if self._use_chroma:
            self._collection.add(ids=[doc_id], documents=[text], metadatas=[metadata])  # type: ignore[union-attr]
        else:
            self._fallback.add(text, metadata, doc_id=doc_id)
        return doc_id

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if self._use_chroma:
            result = self._collection.query(query_texts=[query], n_results=k)  # type: ignore[union-attr]
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            dists = result.get("distances", [[]])[0]
            out: list[dict[str, Any]] = []
            for i, doc in enumerate(docs):
                dist = dists[i] if i < len(dists) else 0.0
                score = 1.0 - dist if dist <= 1.0 else 0.0
                out.append({"text": doc, "metadata": metas[i] if i < len(metas) else {}, "score": round(score, 6)})
            return out
        return self._fallback.search(query, k)

    def delete(self, doc_id: str) -> None:
        if self._use_chroma:
            self._collection.delete(ids=[doc_id])  # type: ignore[union-attr]
        else:
            self._fallback.delete(doc_id)

    def clear(self) -> None:
        if self._use_chroma:
            ids = self._collection.get()["ids"]  # type: ignore[union-attr]
            if ids:
                self._collection.delete(ids=ids)  # type: ignore[union-attr]
        else:
            self._fallback.clear()
