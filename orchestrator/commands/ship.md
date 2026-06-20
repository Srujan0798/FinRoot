---
name: ship
description: Ship a completed wave — full gate, tag, EXECUTION commit hash, CHANGELOG, HANDOFF rewrite.
allowed-tools: Read Write Bash(git:*) Bash(ruff:*) Bash(pytest:*) Bash(python:*) Bash(make:*)
invocation: both
---

# /ship wave-N

All tasks merged → finalize the wave.

Steps:
1. Run the wave's full acceptance block from `.specify/specs/wave-N/spec.md`. Capture all output.
2. Run `bash orchestrator/scripts/validate_execution.sh` (no drift) and `validate.sh`.
3. Regenerate derived docs/metrics (FM-12). Numbers come from `results/metrics.json` (FM-05).
4. Tag: `git tag wave-N-complete`.
5. Update `EXECUTION.md`: status → **SHIPPED** ✅ with the commit hash; set the next active wave.
6. Bump `CHANGELOG.md`. Rewrite `HANDOFF.md` to current truth (FM-01/14).
7. Emit `wave.shipped`. Announce next wave is ready to `/plan` or `/dispatch`.

A wave is SHIPPED only when its acceptance commands pass in your hands with output captured.
