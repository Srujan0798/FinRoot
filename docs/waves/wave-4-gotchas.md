# Wave-4 Gotchas

## G-4a: LangGraph cannot resolve Pydantic forward refs from TYPE_CHECKING
- **Date**: 2026-06-19
- **Symptom**: `StateGraph(AgentState)` fails with `NameError: name 'AuditEvent' is not defined`
- **Root cause**: `AgentState` has `audit_events: list[AuditEvent]` where `AuditEvent` is only imported under `TYPE_CHECKING`. LangGraph's `get_type_hints(schema, include_extras=True)` evaluates forward references in a module context where `AuditEvent` is not available.
- **Fix**: Use a `TypedDict` (`GraphState`) as the LangGraph state schema, with `audit_events: list[Any]`. Convert to/from `AgentState` at the orchestrator boundary via `agent_state_to_graph()`/`graph_state_to_agent()`.
- **Lesson**: Never pass Pydantic models with `TYPE_CHECKING`-guarded forward refs directly to LangGraph's `StateGraph`.

## G-4b: LangGraph node names must not collide with state keys
- **Date**: 2026-06-19
- **Symptom**: `ValueError: 'plan' is already being used as a state key`
- **Root cause**: The `GraphState` TypedDict has a `plan` field, and the node was also named `"plan"`.
- **Fix**: Renamed the node to `"select_agents"` while keeping the state field as `plan`.
- **Lesson**: Check state field names before naming LangGraph nodes.

## G-4c: `.specify/specs/wave-4/contracts/` directory does not exist
- **Date**: 2026-06-19
- **Symptom**: Task 06 contract references `.specify/specs/wave-4/contracts/graph.contract.md` but the `.specify/` directory is entirely absent from the repo.
- **Root cause**: The `.specify/` directory tree was never created during earlier waves, or was removed. Contracts referenced in task briefs may not exist as files.
- **Fix**: Implemented `ResultSynthesizer` to match the actual interface used by `src/finroot/workflows/graph.py:195` (`synthesize(AgentState) -> Recommendation`) rather than the type signature in the task brief (`-> AgentState`), because graph.py is the real consumer.
- **Lesson**: Always check the actual consumer code (graph.py) in addition to contracts. The task brief's method signature may be slightly idealized.
