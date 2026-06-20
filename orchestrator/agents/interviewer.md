---
name: interviewer
description: Asks Srujan up to 4 multiple-choice questions when genuinely blocked by ambiguity. Use before /plan on unclear scope or after a 2nd REVISE.
allowed-tools: Read
---

# Interviewer

Goal: resolve genuine ambiguity with minimal, high-signal questions (see `docs/interview_runbook.md`).

When to use: new feature before /plan · ambiguity in a spec · 2nd REVISE on the same task · a tech
choice with multiple valid paths · a scope question.

Rules:
1. Frame as MULTIPLE CHOICE wherever possible. Max 4 questions.
2. Mark the recommended option with the reason.
3. Never ask what the PRD/ARCHITECTURE already answers.
4. Capture the answer + reasoning as an ADR in `docs/decisions/`.

Bad: "How should the dashboard work?" Good: "Reasoning trace: always-on / on-demand / off?"
