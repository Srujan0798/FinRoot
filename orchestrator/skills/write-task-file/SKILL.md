---
name: write-task-file
description: Use when turning a planned wave task into a self-contained worker task file. Produces a disjoint-write, acceptance-gated brief a stateless worker can execute alone.
allowed-tools: Read Write Glob Grep
invocation: claude
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Write Task File

When to use: dispatching a task and you need a brief a worker can run with zero extra context.

Process:
1. Start from `work/TASK_TEMPLATE.md`.
2. Fill: Objective · Why-it-matters (link to scoring/PRD) · Writes (exact paths) · Forbid ·
   Contracts to honor · ordered Steps · Acceptance (exact commands + expected output) · Report path.
3. Verify the `Writes` set is disjoint from every other pending task (FM-13).
4. Add the domain-rules reminder (numbers cited, fail loud, confidence labels).
5. Keep it ≤ ~1.5K tokens (context-budget). Self-contained, no "see other file" gaps.

Output: a file at `work/<wave>/0X-<slug>.md`. Never include implementation code — describe intent,
contracts, and acceptance; the worker writes the code.
