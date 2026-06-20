# .claude/ — Orchestrator Settings Guide

> The OS-Setup methodology wants a `.claude/settings.local.json` that pre-approves a safe
> **read + local-repo (r0/r1)** tool surface so routine orchestration doesn't prompt, while keeping
> r2+ confirmations and blocking destructive/money operations.
>
> **This file was NOT auto-generated as an active settings file on purpose:** writing permission
> *allow* rules is a self-modification of the agent's own capabilities, so it must be **your**
> deliberate choice, not something the setup does for you. Create it yourself with the template below.

## Create `.claude/settings.local.json`
```jsonc
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep",
      "Bash(ruff:*)", "Bash(pytest:*)", "Bash(python:*)", "Bash(python3:*)",
      "Bash(pip:*)", "Bash(make:*)",
      "Bash(git status)", "Bash(git diff:*)", "Bash(git log:*)",
      "Bash(bash orchestrator/scripts/*.sh:*)",
      "Bash(bash orchestrator/hooks/*.sh:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)",
      "Bash(*place_order*)",
      "Bash(*execute_trade*)",
      "Bash(*transfer_funds*)"
    ]
  }
}
```
Quickest path: run `/permissions` in Claude Code, or use the `update-config` skill, to add these
interactively — that records your explicit consent.

## Why these choices
- **Allow = r0/r1 only** — reading, linting, testing, running the project's own scripts. Fast loops.
- **r2+ stays interactive** — DB writes, live API calls, pushes all still prompt (blast-radius govern).
- **Deny = r5 / irreversible** — force-push, recursive delete, and any money/trade verbs are blocked,
  matching FinRoot's hard rule that the product can never move money (`orchestrator/core/blast-radius.md`).

## Hooks
Wire `orchestrator/hooks/*` through your runner's hook config:
| Hook | When | Does |
|---|---|---|
| `session-start.sh` | SessionStart | prints active wave + last events |
| `pre-tool-use.sh` | PreToolUse | classifies blast radius; blocks r5, confirms r3+ |
| `block-secrets.sh` | PreCommit | stops secrets being committed (FM-07) |
| `block-destructive.sh` | PreToolUse | hard-stops irreversible commands |
| `post-merge-format.sh` | PostMerge | ruff format + autofix |
| `stop.sh` | Stop | end-of-session handoff checklist |
