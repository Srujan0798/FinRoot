---
name: plan-wave
description: Use when decomposing a wave into 4-8 parallel-safe tasks with disjoint write-sets, dependencies, and acceptance criteria.
allowed-tools: Read Write Glob Grep
invocation: claude
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Plan Wave

When to use: a new wave becomes active and needs specs + a task breakdown.

Process:
1. Read PRD, ARCHITECTURE, the wave brief in `docs/waves/`, and prior wave gotchas.
2. Define the wave goal + acceptance commands (what proves the wave shipped).
3. List every file the wave touches; partition into 4–8 disjoint `writes` sets (one per task).
4. Identify shared interfaces → freeze them as `contracts/*.md` BEFORE tasks start.
5. Order tasks by dependency; mark which run in parallel.
6. Write `.specify/specs/wave-N/{spec,plan,tasks}.md` and update `EXECUTION.md`.

Guardrails: smallest stack that ships the wave; extras → BACKLOG (FM-08); no shared writes (FM-13).
