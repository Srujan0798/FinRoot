# ADR-0002 — Stack Selection

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Orchestrator (synthesizing the 12 brainstorm proposals in `resources/brainstorm/`)

## Context
The PS requires LangChain. We need the smallest stack that ships a sovereign, reasoning-first,
auditable financial agent that demos reliably offline and scores on all four axes.

## Decision
| Layer | Choice | Why |
|---|---|---|
| Agent framework | **LangChain + LangGraph** | PS-mandated; LangGraph gives explicit, inspectable Plan-and-Execute control flow (12-factor #8) — judges grade architecture. |
| Types | **Pydantic v2** | typed boundaries; the citation-required validator structurally enforces FM-11. |
| LLM providers | **Mock / Ollama / Groq / OpenAI** behind one interface | sovereignty (local default) + offline Mock for judging; cloud opt-in. |
| Vector memory | **ChromaDB + JSON fallback** | local, no server; degrades gracefully when absent. |
| Structured memory / audit | **SQLite + JSONL (hash-chained)** | zero-ops, local, tamper-evident. |
| Sentiment | **FinBERT (local)** | sovereign, no API. |
| UI / CLI | **Streamlit (dark) + Typer** | fastest finance-grade demo surface; Python-native (no JS). |
| Eval | **custom FRB harness** (Harbor-compatible later) | proves the 35% with pass@k/pass^k. |
| Packaging | **Docker + compose**, ruff, pytest | one-command spin-up; engineering polish (20%). |

## Consequences
- Everything runs with **zero keys** (Mock + Ollama) — judge-safe and sovereign.
- Optional SDKs (groq/openai/chromadb/finbert) are lazy-imported so the base install stays light.
- No closed API is on a critical path; cloud is an accelerator, never a dependency.

## Alternatives rejected
- **CrewAI / AutoGen** as the core — PS favors LangChain; we keep them as edge-only compatibility, not deps.
- **Postgres + pgvector** now — overkill for single-user; deferred to BACKLOG.
- **A JS/TS frontend** — slower to a reliable demo; Streamlit wins for this deadline.
