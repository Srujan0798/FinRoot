# Context Budget

Keep the orchestrator's working context lean so it never forgets earlier decisions (FM-04).

## Budget targets
| Layer | Target | Notes |
|---|---|---|
| Kernel (`CLAUDE.md`) | ≤ ~3K tokens | auto-loaded; trim ruthlessly |
| Active-wave spec | ≤ ~2K tokens | read on demand |
| Per task file | ≤ ~1.5K tokens | self-contained but tight |
| Session working set | ≤ ~40% of window | compact beyond this |

## Progressive disclosure
Load only what the current step needs: kernel → active spec → the one task → its contract. Do NOT
preload all of `docs/`. Use grep/replay to fetch specifics.

## Compaction triggers
- Approaching the working-set cap → write decisions to HANDOFF.md / an ADR / events.jsonl, /clear.
- End of a wave → rewrite HANDOFF.md, summarize the wave in EXECUTION.md log.
- Cold resume → `replay_session.sh` reconstructs the minimal context, not the whole history.

## Report: `scripts/context-budget-report.sh` estimates the size of kernel + active spec + tasks.
