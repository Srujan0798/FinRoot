# Steering (Kiro-style)

> Persistent guidance that steers every spec and worker. Short, stable, high-signal.

## Product steering
- We are building a **trustworthy financial reasoning partner**, not a chatbot or robo-advisor.
- India-first defaults (rupee, Indian tax regime, family goals) but provider-agnostic design.
- Optimize relentlessly for the scoring weights: Reasoning 35% > Architecture 30% > Code 20% > Idea 15%.
- The demo must work offline with zero keys (Mock mode). Reliability beats flashiness at judging.

## Technical steering
- LangChain + LangGraph native. Show real agents/chains/tools/memory — judges grade architecture.
- Pydantic v2 at every boundary. Adapters for LLM providers and data sources (swappable).
- Numbers from tools only, always cited. No silent fallbacks. No fabricated data.
- Keep the kernel (`CLAUDE.md`) lean; lazy-load deep context from `orchestrator/core/`, `plan/`, `docs/`.

## Process steering
- Ship one wave end-to-end before starting the next. Foundation (W1) gates everything.
- Disjoint write-sets per task; check before dispatch. Capture gotchas DURING the wave.
- Prove reasoning quality with the FRB harness; never just claim it.

## Tone for user-facing outputs
- Clear, calm, advisor-grade. Always: rationale + alternatives + risks + confidence.
- Never overclaim. Surface uncertainty. Recommend "do not act yet" when evidence is thin.
