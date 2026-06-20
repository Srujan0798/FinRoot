# Incident Response Playbook

Lightweight (single-user / demo scope). Focus: keep the build green and the demo reliable.

## Severity
- **SEV-1** — demo path broken (Mock mode fails) or fabricated-number leak in output.
- **SEV-2** — a wave's acceptance fails after merge; main is red.
- **SEV-3** — a live provider/tool flaky (Mock unaffected).
- **SEV-4** — cosmetic / docs.

## Response
1. **Stabilize:** if a recent merge broke main → revert, send the task back to REVISE. Demo always
   falls back to Mock mode (no keys) — that's the safe harbor.
2. **Diagnose:** `/diagnose` — reproduce in Mock with seeded RNG; read the audit trail + events.
3. **Fix via the loop:** failing test → fix (worker) → verify (orchestrator) → merge.
4. **Learn:** SEV-1/2 → `HALL_OF_SHAME.md` entry + regression test + eval task + prevention rule (§6.7).

## Common scenarios
- **Fabricated/uncited number in output (SEV-1)** → the citation validator or grader should have
  caught it; add the missing guard; tighten `rules/python.md`; add an FRB negative case.
- **Self-Critic rubber-stamping** → add deliberately-bad answers to the eval set it must catch.
- **Live API down during demo** → switch to Mock mode (default anyway); note in demo script.
- **Audit chain verify=False** → do NOT auto-repair; investigate the tamper/bug; it's working as designed.
- **Context bloat / orchestrator confused** → `/handoff`, `/clear`, replay_session.sh, resume.
