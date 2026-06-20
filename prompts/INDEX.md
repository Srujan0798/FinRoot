# Prompts Index

> Worker/agent prompts evolve here. `current/` = active, `archive/` = superseded (never deleted),
> `hybrid/` = experimental combinations, `wave-N/` = wave-scoped overrides.

## Standing prompts
| File | Purpose |
|---|---|
| `../work/WORKER_PROMPT.md` | Tier-2 worker preamble (the canonical dispatch prompt) |
| `EXAMPLE_FILLED_TASK.md` | A worked example of a completed task file (reference for workers) |

## current/
*(reasoning + sub-agent system prompts land here in W4/W5, versioned via `config/prompts.py`)*

## Conventions
- Prompts are versioned (name + version) in `config/prompts.py`; this folder holds the prose source.
- Superseded prompt → move to `archive/` with a date suffix; never edit-in-place destructively.
- Reasoning prompts are part of the 35% — keep them inspectable and under review.
