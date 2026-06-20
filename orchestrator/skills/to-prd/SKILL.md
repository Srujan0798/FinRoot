---
name: to-prd
description: Use when a raw idea or brief must become or update the structured PRD (problem, users, objectives, metrics, scope).
allowed-tools: Read Write Grep Glob
invocation: claude
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# To PRD

When to use: turning a brief/idea into `plan/PRD.md` content, or revising it after a decision.

Process:
1. Extract: problem, target user, objectives, novelty, capabilities, non-goals, success metrics, risks.
2. Keep metrics measurable and tied to a single source (`results/metrics.json` / eval reports).
3. Map every capability to a scoring weight so effort stays aligned (Reasoning 35% first).
4. Record material changes as an ADR; never let PRD drift from EXECUTION (FM-01).
