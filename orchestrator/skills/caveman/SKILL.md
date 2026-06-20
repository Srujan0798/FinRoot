---
name: caveman
description: Use when a task brief or spec is getting bloated — strip it to the dumbest, shortest form a worker can still execute correctly.
allowed-tools: Read Write
invocation: both
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Caveman

When to use: a brief is wordy, clever, or ambiguous. Simplicity beats cleverness.

Process:
1. Reduce to: what to build · what files · how we know it works (acceptance). Delete the rest.
2. Replace abstractions with concrete examples (one filled example beats a paragraph of theory).
3. Short sentences. No jargon a stateless worker wouldn't share.
4. If it still doesn't fit on one screen, the task is too big — split it.

"Make task small. Make words few. Make test clear." Then dispatch.
