# Karpathy / Boris Rules (CLAUDE.md discipline)

Distilled rules for keeping the agentic setup effective.

- **Keep CLAUDE.md small and high-signal.** It is read every session. Deep detail lazy-loads.
- **`.claude/` minimal.** Don't over-build configuration; start with 10 commands and grow as needed.
- **Acceptance before approval.** The orchestrator runs the acceptance command itself (Boris's #1 rule).
- **/clear between unrelated tasks.** Don't let context bloat carry stale decisions (FM-04).
- **Plan in the open.** Write the plan to a file; review it; then execute. Plans are artifacts.
- **One change, one commit, conventional message.** Small reversible steps.
- **Tighten the loop.** Fast smoke tests + Mock mode mean every change is verifiable in seconds.
- **Write the test/eval first** when defining a capability (eval-driven, §5.5).
- **Prefer boring tech.** The smallest winning stack beats the cleverest one.
