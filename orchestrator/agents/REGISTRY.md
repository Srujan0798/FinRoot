# Sub-Agent Registry

Sub-agents the orchestrator invokes for focused, read-heavy, or independent work. These are
ORCHESTRATOR helpers (Tier-1 side), distinct from the FinRoot product agents in `src/finroot/agents/`.

| Agent | Purpose | Invoked during | Context |
|---|---|---|---|
| `codebase-explorer` | Map existing code, trace execution paths, find where something lives | /plan, /diagnose | read-only subagent |
| `verifier` | Independent re-check of a worker's diff against the contract + guardrails | /review | read-only subagent |
| `interviewer` | Ask Srujan ≤4 multiple-choice questions when genuinely blocked | ambiguity, 2nd REVISE | interactive |
| `brief-writer` | Draft a self-contained worker task file from a spec task | /dispatch | subagent |
| `security-reviewer` | Scan for secrets, unsafe advice paths, injection, dependency risk (T2) | /audit --type=security | read-only subagent |

## Rules
- Sub-agents run in their own context window (don't pollute the orchestrator's budget, FM-04).
- They return a summary to the orchestrator; the orchestrator decides and acts.
- None of them write to `src/` — only workers implement.
