# ADR-0001 — Project Tier and Archetype

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Orchestrator (with Srujan)

## Context
FinRoot is a competition submission (SCALE PS-1) judged on Reasoning 35% · Architecture 30% ·
Code 20% · Idea 15%, and explicitly meant to be production-grade, not a toy. We must pick an
OS-Setup tier (T0–T4) and an archetype (§14) to shape the scaffold.

## Decision
- **Tier: T2 (Production).** T2 adds exactly what the rubric rewards: `evals/` (35% proof),
  observability + audits + tests taxonomy + CI (20% engineering), and the full orchestrator
  apparatus (30% architecture). T3/T4 (compliance, multi-tenant, GTM) are out of scope for a
  single-user judged demo and would add overhead without scoring return.
- **Archetype: hackathon/competition (primary) + research-ml (emphasis).** Judges, deadline, "win"
  → hackathon discipline (one reliable end-to-end demo path, Mock fallback). Reasoning-heavy,
  eval-driven, reproducible metrics → research-ml emphasis (FRB harness, one-source metrics, honest
  limitations). Top failure modes to guard first: FM-09 (false status), FM-11 (silent/fabricated
  data), FM-05 (metric inconsistency), FM-07 (embarrassing artifacts).

## Consequences
- We build the T1 base + T2 additions; we pull a few T4 *docs* (demo script, slides) in wave-8 only,
  as additive deliverables — not a full T4 bump.
- Effort is allocated by weight: Self-Critic + FRB (W5/W6) get the most rigor.

## Alternatives rejected
- **T1** — too thin to showcase engineering (loses Code 20% signal) and lacks first-class evals.
- **T3/T4** — compliance/SaaS scaffolding the judges don't score; slows the deadline.
