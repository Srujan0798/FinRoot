# ADR-0004 — 4-tier memory + Digital Twin

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Orchestrator (with Srujan)

## Context
The 35% Reasoning Quality weapon requires personalization and consistency across sessions. We need:

1. **Working memory:** Short-term context for the current query (in-memory)
2. **Semantic memory:** Long-term knowledge base (ChromaDB vector store)
3. **Structured memory:** Persistent user profile and preferences (SQLite)
4. **Audit memory:** Tamper-evident event log (hash-chained JSONL)

The Digital Twin is the personalization moat (Idea 15%) — it captures the user's unique financial profile, risk tolerance, and behavior patterns to provide tailored advice.

## Decision
We implemented **4-tier memory** in `src/finroot/memory/`:

- **Working:** `src/finroot/memory/working.py` — in-memory AgentState snapshots
- **Semantic:** `src/finroot/memory/semantic.py` — ChromaDB for embeddings and similarity search
- **Structured:** `src/finroot/memory/manager.py` — SQLite for user profiles, preferences, and financial data
- **Audit:** `src/finroot/audit/trail.py` — hash-chained JSONL for tamper evidence (FM-07)

The **Digital Twin** lives in `src/finroot/memory/digital_twin.py` and includes:
- User profile (risk tolerance, goals, constraints)
- Historical interactions and preferences
- Portfolio patterns and behavior
- Personalized reasoning context

The Digital Twin is updated after each interaction and used as context for future queries, creating a personalized moat that's hard for competitors to replicate.

## Consequences
- **Positive:** Creates a strong personalization moat (Idea 15%); users get tailored advice
- **Positive:** Enables consistent reasoning across sessions; users see progress
- **Positive:** Audit trail ensures memory integrity (FM-07)
- **Negative:** Increased storage and compute overhead
- **Negative:** More complex state management across 4 layers
- **Neutral:** Requires careful data synchronization between layers

## Alternatives considered
- **Single vector store:** Would lose structured data integrity and auditability
- **No Digital Twin:** Would reduce personalization and moat strength
- **3-tier memory (working + semantic + audit):** Would lose structured user profile data

The 4-tier approach is the minimal design that delivers the personalization moat while maintaining auditability and structured data integrity.