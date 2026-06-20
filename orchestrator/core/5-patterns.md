# The 5 Canonical Agent Patterns (and how FinRoot uses each)

Anthropic's "Building effective agents" workflow/agent patterns, mapped to FinRoot.

1. **Prompt chaining** — the reasoning pipeline (classify → context → plan → execute → synthesize
   → critique → verify) is a chain with gates between steps.
2. **Routing** — the Reasoning Orchestrator routes each query to the right sub-agent(s) by intent.
3. **Parallelization** — independent sub-agents (e.g., Market + News + Risk) run concurrently;
   self-consistency runs N candidates in parallel then votes.
4. **Orchestrator–workers** — Plan-and-Execute supervisor decomposes and delegates to ReAct
   sub-agents (mirrors our build-time Tier-1/Tier-2 split — fractal design).
5. **Evaluator–optimizer** — the Self-Critic scores and the pipeline refines until the answer
   clears the bar; this is the heart of the 35% reasoning-quality strategy.

Rule of thumb: use the **simplest** pattern that meets the need. Add complexity only when a
capability eval demands it.
