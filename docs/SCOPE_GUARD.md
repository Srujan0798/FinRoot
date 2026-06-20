# Scope Guard — IN / OUT / LATER

> The canonical scope boundary (FM-08). Every task brief lists files it may + must-not touch. Extras
> go to BACKLOG, not into the build. Orchestrator enforces; workers obey.

## IN (build this round — the 8 waves)
- Reasoning-first multi-agent core (LangGraph orchestrator + 5 sub-agents).
- 4-tier memory + Financial Digital Twin.
- 12-tool ecosystem (market, news, fundamentals, sentiment, risk, sim, **Indian tax engine**, macro,
  currency, profile, documents, watchlist) — all keyless/Mock-capable.
- Self-Critic + Rooted Prudence verifier + self-consistency + explainability.
- Hash-chained audit trail.
- FRB evaluation harness with baseline comparison (the 35% proof).
- Streamlit dark UI + Typer CLI + Mock mode.
- Docker, CI, docs, demo script, slides, submission package.

## OUT (do NOT build — declined on purpose)
- **Trade execution / money movement** (r5 — blocked; FinRoot is decision-support only).
- Multi-tenant SaaS, billing, auth portals, user management.
- Mobile apps; real-time HFT / tick signals.
- Removing the "not financial advice" disclaimer.
- A TS/JS frontend (Streamlit is the UI).

## LATER (BACKLOG — revisit only if a wave finishes early)
Brokerage read-only sync · FX/multi-currency reasoning · voice/WhatsApp · PDF statement ingestion ·
Postgres+pgvector · adversarial/red-team eval set · streaming UI tokens. See `BACKLOG.md`.

## When scope is challenged
A "great idea" mid-wave → report it as a Follow-up → orchestrator triages to BACKLOG. Changing IN/OUT
requires an ADR in `docs/decisions/`, never a silent worker decision.
