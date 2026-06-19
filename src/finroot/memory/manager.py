"""MemoryManager — unified facade over working, semantic, and twin stores.

This module is the Tier-2 wave-2 task 04 deliverable. It owns *one* concern:
compose the three lower-level memory tiers into a single object that wave-4
agents can use without ever touching the underlying stores directly.

Contract reference
------------------
``.specify/specs/wave-2/contracts/memory.contract.md`` § MemoryManager.

Design notes
------------
* No state of its own beyond references to the three injected stores and the
  ``user_id``. ``MemoryManager`` is a thin coordinator — it does not cache,
  pre-load, or duplicate anything the stores already own.
* Failures from the underlying stores are propagated unchanged (no bare
  ``except:``, no silent recovery, no fabrication). The contract requires
  ``get_twin`` to raise :class:`KeyError` when no twin exists; we re-raise
  whatever ``DigitalTwinStore.load`` raises.
* ``update_twin`` performs a *partial* update by calling
  :meth:`DigitalTwin.model_copy` with ``update=kwargs``. Because
  :class:`DigitalTwin` is configured with ``extra="forbid"``, Pydantic will
  raise :class:`pydantic.ValidationError` on unknown fields — also propagated
  unchanged. Changing ``user_id`` is *rejected* explicitly to prevent the
  caller from silently orphaning the persisted row.
* ``add_turn`` auto-remembers content longer than 50 characters into the
  semantic store so a downstream agent can recall the *gist* of a long
  exchange without us deciding *which* 50 characters matter. The threshold
  is contract-defined and not configurable from the outside; the
  :class:`MemoryManager` is a thin facade, not a policy engine.
* ``create`` is a *convenience factory*, not a public constructor: tests and
  orchestrators that want fine-grained control (e.g. sharing one
  :class:`SemanticMemory` across many managers) should build the three
  stores themselves and call ``__init__`` directly.
"""

from __future__ import annotations

from typing import Any

from finroot.memory.digital_twin import DigitalTwin, DigitalTwinStore
from finroot.memory.semantic import SemanticMemory
from finroot.memory.working import WorkingMemory

_AUTO_REMEMBER_MIN_CHARS: int = 50
"""Minimum ``len(content)`` for a turn to be auto-remembered into semantic memory.

Contract: ``add_turn`` calls ``semantic.add`` only when ``content > 50 chars``.
The threshold is strictly greater-than — a 50-character turn is *not*
auto-remembered, but a 51-character one is.
"""

_RESERVED_TWIN_FIELDS: frozenset[str] = frozenset({"user_id"})
"""Fields that :meth:`MemoryManager.update_twin` refuses to change.

Changing ``user_id`` on an existing twin would orphan the persisted row
(because ``DigitalTwinStore.save`` is keyed on ``user_id``); we fail loud
rather than silently re-key.
"""


class MemoryManager:
    """Unified facade: working + semantic + twin read/write.

    Wave-4 agents use *only* this class to talk to memory. The underlying
    ``WorkingMemory`` / ``SemanticMemory`` / ``DigitalTwinStore`` are
    implementation details that may be swapped without touching callers.

    Parameters
    ----------
    working:
        Sliding-window conversation buffer. Ownership is *not* taken;
        callers may keep their own reference for direct access if needed.
    semantic:
        Vector store (ChromaDB or stdlib TF-IDF fallback). Auto-remembered
        long turns are appended here on :meth:`add_turn`.
    twin_store:
        SQLite (or JSON-fallback) persistence for the user's :class:`DigitalTwin`.
    user_id:
        Stable identifier for the user. Used by :meth:`get_twin` and
        :meth:`update_twin` to locate the persisted twin; must match the
        ``user_id`` of the twin stored in ``twin_store``.

    Raises
    ------
    TypeError
        If any of the three stores is of the wrong type.
    ValueError
        If ``user_id`` is empty.
    """

    def __init__(
        self,
        working: WorkingMemory,
        semantic: SemanticMemory,
        twin_store: DigitalTwinStore,
        user_id: str,
    ) -> None:
        if not isinstance(working, WorkingMemory):
            raise TypeError(
                f"working must be WorkingMemory, got {type(working).__name__}"
            )
        if not isinstance(semantic, SemanticMemory):
            raise TypeError(
                f"semantic must be SemanticMemory, got {type(semantic).__name__}"
            )
        if not isinstance(twin_store, DigitalTwinStore):
            raise TypeError(
                f"twin_store must be DigitalTwinStore, got {type(twin_store).__name__}"
            )
        if not isinstance(user_id, str):
            raise TypeError(
                f"user_id must be str, got {type(user_id).__name__}"
            )
        if not user_id:
            raise ValueError("user_id must be a non-empty string")
        self._working: WorkingMemory = working
        self._semantic: SemanticMemory = semantic
        self._twin_store: DigitalTwinStore = twin_store
        self._user_id: str = user_id

    @property
    def user_id(self) -> str:
        """The user this facade is bound to (read-only)."""
        return self._user_id

    @property
    def working(self) -> WorkingMemory:
        """The underlying :class:`WorkingMemory` (read-only access for tests)."""
        return self._working

    @property
    def semantic(self) -> SemanticMemory:
        """The underlying :class:`SemanticMemory` (read-only access for tests)."""
        return self._semantic

    @property
    def twin_store(self) -> DigitalTwinStore:
        """The underlying :class:`DigitalTwinStore` (read-only access for tests)."""
        return self._twin_store

    # ------------------------------------------------------------------ #
    # Working memory
    # ------------------------------------------------------------------ #

    def add_turn(self, role: str, content: str) -> None:
        """Append one turn to the working buffer and, if long, the semantic store.

        Auto-remember policy: if ``len(content) > 50`` characters, the *same*
        content is also appended to the semantic store with metadata
        ``{"user_id": ..., "role": ..., "source": "auto_remember"}`` so a
        future :meth:`recall` can surface it.

        Parameters
        ----------
        role:
            ``"user"``, ``"assistant"``, or ``"tool"``. Invalid roles raise
            :class:`ValueError` from :meth:`WorkingMemory.add` (FM-11).
        content:
            Free-form text. Empty strings are allowed; they are *not*
            auto-remembered (length-0 fails the threshold).

        Raises
        ------
        ValueError
            If ``role`` is not one of the allowed values.
        TypeError
            If ``content`` is not a ``str``.
        """
        self._working.add(role, content)
        if len(content) > _AUTO_REMEMBER_MIN_CHARS:
            self._semantic.add(
                content,
                {
                    "user_id": self._user_id,
                    "role": role,
                    "source": "auto_remember",
                },
            )

    def get_context(self) -> list[dict[str, str]]:
        """Return the current working-memory window in insertion order.

        The returned list is a fresh copy — callers may mutate it freely
        without affecting the buffer.
        """
        return self._working.get_messages()

    # ------------------------------------------------------------------ #
    # Semantic memory
    # ------------------------------------------------------------------ #

    def remember(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        """Explicitly store a piece of text in semantic memory.

        Unlike :meth:`add_turn`, this is a *direct* write to the semantic
        store — no length threshold, no automatic metadata. Use this when
        the agent decides (e.g. from a tool result) that a fact is worth
        remembering.

        Parameters
        ----------
        text:
            The text to store. Must be a non-empty ``str``.
        metadata:
            Free-form metadata dict attached to the document. ``None`` is
            treated as an empty dict; keys must be serialisable (ChromaDB
            requires str/int/float/bool/None; the JSON fallback accepts any
            JSON-compatible value).

        Returns
        -------
        str
            The document id assigned by the underlying store.

        Raises
        ------
        TypeError
            If ``text`` is not a ``str``.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        payload: dict[str, Any] = dict(metadata) if metadata else {}
        payload.setdefault("user_id", self._user_id)
        return self._semantic.add(text, payload)

    def recall(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search semantic memory for the top-``k`` documents matching ``query``.

        Empty store or no match returns ``[]`` (never raises on miss, per
        the :class:`SemanticMemory` contract).

        Parameters
        ----------
        query:
            The natural-language query.
        k:
            Maximum number of results to return. Must be a positive ``int``.

        Returns
        -------
        list[dict[str, Any]]
            ``[{"text": ..., "metadata": {...}, "score": float}, ...]``
            ordered by descending relevance.

        Raises
        ------
        TypeError
            If ``query`` is not a ``str`` or ``k`` is not an ``int``.
        ValueError
            If ``k < 1``.
        """
        if not isinstance(query, str):
            raise TypeError(f"query must be str, got {type(query).__name__}")
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError(f"k must be int, got {type(k).__name__}")
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        return self._semantic.search(query, k)

    # ------------------------------------------------------------------ #
    # Digital twin
    # ------------------------------------------------------------------ #

    def get_twin(self) -> DigitalTwin:
        """Load the bound user's :class:`DigitalTwin` from the store.

        Returns
        -------
        DigitalTwin
            The persisted twin for ``self._user_id``.

        Raises
        ------
        KeyError
            If no twin exists for ``self._user_id`` (propagated from
            :meth:`DigitalTwinStore.load`). FM-11: fail loud, never invent.
        """
        return self._twin_store.load(self._user_id)

    def update_twin(self, **kwargs: Any) -> DigitalTwin:
        """Apply a partial update to the bound user's twin and persist it.

        Loads the current twin, merges ``kwargs`` into it, validates the
        merged result (so unknown / type-wrong fields raise
        :class:`pydantic.ValidationError`), saves it, and returns the
        updated twin.

        Parameters
        ----------
        **kwargs:
            Fields to change on the twin. The keys must be valid
            :class:`DigitalTwin` fields; ``user_id`` is rejected explicitly
            to prevent silent re-keying of the persisted row.

        Returns
        -------
        DigitalTwin
            The updated, freshly-saved twin.

        Raises
        ------
        KeyError
            If no twin exists for ``self._user_id``.
        ValueError
            If ``user_id`` appears in ``kwargs``.
        pydantic.ValidationError
            If ``kwargs`` contains an unknown field or a value that fails
            the twin's field constraints.

        Notes
        -----
        Pydantic v2's :meth:`BaseModel.model_copy` does not re-run field
        validation, so to enforce ``extra="forbid"`` and the per-field
        constraints we rebuild the model via :meth:`DigitalTwin.model_validate`
        against a merged dict. ``model_dump(mode="python")`` is used so
        datetimes stay as :class:`datetime` objects (not ISO strings),
        avoiding a needless round-trip.
        """
        forbidden = _RESERVED_TWIN_FIELDS & kwargs.keys()
        if forbidden:
            raise ValueError(
                f"update_twin does not allow changing reserved fields: "
                f"{sorted(forbidden)!r}"
            )
        current = self._twin_store.load(self._user_id)
        merged: dict[str, Any] = current.model_dump(mode="python")
        merged.update(kwargs)
        updated = DigitalTwin.model_validate(merged)
        self._twin_store.save(updated)
        return updated

    # ------------------------------------------------------------------ #
    # Factory
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        user_id: str,
        chroma_dir: str = "data/chroma",
        db_path: str = "data/digital_twin.db",
        max_turns: int = 10,
    ) -> MemoryManager:
        """Convenience factory: build all three stores and the facade in one call.

        Use this when you don't need to share stores across managers; for
        fine-grained control, build the three stores and call
        :meth:`__init__` directly.

        Parameters
        ----------
        user_id:
            Stable user identifier. Must be a non-empty ``str``.
        chroma_dir:
            Persist directory for ChromaDB (ignored if chromadb is
            unavailable — the JSON fallback is in-process).
        db_path:
            SQLite file path for :class:`DigitalTwinStore` (the store will
            use a JSON fallback at ``{db_path}.json`` if SQLite is
            unavailable).
        max_turns:
            Sliding-window capacity for :class:`WorkingMemory`.

        Returns
        -------
        MemoryManager
            A facade bound to ``user_id`` with fresh, independent stores.
        """
        working = WorkingMemory(max_turns=max_turns)
        semantic = SemanticMemory(persist_dir=chroma_dir)
        twin_store = DigitalTwinStore(db_path=db_path)
        return cls(
            working=working,
            semantic=semantic,
            twin_store=twin_store,
            user_id=user_id,
        )


__all__ = ["MemoryManager"]
