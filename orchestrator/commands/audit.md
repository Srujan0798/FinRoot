---
name: audit
description: Produce a date-stamped audit (final / docs-sync / tech-debt / security) in docs/audits/.
allowed-tools: Read Write Bash(ruff:*) Bash(pytest:*) Bash(pip-audit:*) Grep Glob
invocation: both
---

# /audit [--type=final|docs-sync|tech-debt|security]

Default `final` (run at end of each wave). Writes `docs/audits/<YYYY-MM-DD>-<type>.md`.

Steps:
1. **final** — verify acceptance criteria, run tests + ruff, check security + docs sync; classify
   findings CRITICAL/HIGH/MEDIUM/LOW. CRITICAL blocks ship; HIGH → next wave; MEDIUM → BACKLOG.
2. **docs-sync** — run `validate_execution.sh`; check files referenced in CLAUDE.md exist (FM-03);
   flag code/doc drift.
3. **tech-debt** — list `src/` modules not imported, TODOs, stale ADRs.
4. **security** — `pip-audit`, secret scan, MCP whitelist check.
5. Every CRITICAL finding → HALL_OF_SHAME entry + regression test + eval task + prevention rule (§6.7).
6. Sign-off block; set next audit date. Emit `audit.complete`.
