# 12-Factor Agents (applied to FinRoot)

Adapted from the 12-Factor Agents methodology. The ones we enforce hardest are starred.

1. **Natural-language → tool calls** — the agent converts intent into typed tool invocations.
2. ★ **Own your prompts** — prompts are versioned in `prompts/` + `config/prompts.py`, not buried.
3. ★ **Own your context window** — progressive disclosure; lean kernel; compact to HANDOFF/events (FM-04).
4. **Tools are structured outputs** — every tool returns a Pydantic model, not free text.
5. ★ **Unify execution + business state** — `AgentState` is the single carried state; audit log is durable.
6. **Launch / pause / resume** — `wake()` via HANDOFF + events.jsonl + replay_session.sh.
7. **Contact humans via tool calls** — interview the user through the `interviewer` sub-agent.
8. ★ **Own your control flow** — LangGraph state machine, explicit pipeline (not an opaque loop).
9. **Compact errors into context** — failures summarized into the trace, not swallowed (FM-11).
10. **Small, focused agents** — 5 specialized sub-agents, each with a tight tool set.
11. **Trigger from anywhere** — CLI / UI / API entry points share one core.
12. ★ **Stateless reducer** — the reasoning step is a pure function of `AgentState`; reproducible.
