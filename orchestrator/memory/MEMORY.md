# Orchestrator Memory

> Durable, high-signal lessons and decisions the orchestrator should not forget. One line each.
> This is the orchestrator's working memory; product/user memory lives in `src/finroot/memory/`.

## Project facts
- FinRoot = sovereign, reasoning-first AI financial agent. Tier T2. Scoring: Reasoning 35% >
  Architecture 30% > Code 20% > Idea 15%. India-first defaults.
- Demo path must run offline (Mock) with zero keys. Reliability > flash at judging.
- Build is dual-tier: this orchestrator plans/reviews; Srujan's agent swarm implements.

## Decisions (link ADRs)
- 2026-06-19: Tier=T2, archetype=hackathon+research-ml. (ADR-0001)
- 2026-06-19: Stack = LangChain+LangGraph, Pydantic v2, Chroma+SQLite, Streamlit+Typer,
  Ollama/Groq/OpenAI/Mock. (ADR-0002)

## Lessons (append from /reflect and HALL_OF_SHAME)
- (seed) Numbers must be tool-sourced + cited — the single biggest finance-agent failure mode.
- (seed) Self-Critic must be tested against deliberately-bad answers or it rubber-stamps.

## Standing reminders
- Freeze shared contracts before parallel dispatch (FM-13).
- Re-run acceptance yourself before APPROVE (FM-09).
- Rewrite HANDOFF + EXECUTION to truth at session end (FM-01/14).
