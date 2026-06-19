"""FinRoot memory layer.

Public surface (re-exported as the wave-2 tasks land):

* :class:`WorkingMemory` — sliding-window conversation buffer (task 01).
* :class:`SemanticMemory` — ChromaDB-backed vector store (task 02).
* :class:`DigitalTwin` / :class:`DigitalTwinStore` / :class:`RiskTolerance` /
  :class:`InvestmentHorizon` — user-profile persistence (task 03).
* :class:`MemoryManager` — unified facade over all three (task 04).

Task 01 (this wave) only ships the working-memory module. The later tasks
own their own modules and will append re-exports here as they merge; the
file map in ``.specify/specs/wave-2/contracts/memory.contract.md`` confirms
this file is part of task 01's write-set.
"""

from __future__ import annotations

from finroot.memory.working import Role, WorkingMemory

__all__ = ["Role", "WorkingMemory"]
