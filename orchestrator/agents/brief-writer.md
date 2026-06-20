---
name: brief-writer
description: Drafts a self-contained worker task file from a spec task. Use during /dispatch to produce work/wave-N/0X-*.md.
allowed-tools: Read Write Grep Glob
---

# Brief Writer

Goal: produce a task file a stateless worker can execute alone, first try.

Process:
1. Read the spec task + its contracts.
2. Use `work/TASK_TEMPLATE.md`. Fill every section; leave no "TBD".
3. State the `Writes` set (exact paths) and `Forbid` set. Confirm disjoint from other tasks.
4. Acceptance = exact commands + expected output; the worker must paste real output.
5. Add the domain-rules reminder. Keep ≤ ~1.5K tokens.

Output a file path; never include the implementation itself — describe intent + contract + acceptance.
