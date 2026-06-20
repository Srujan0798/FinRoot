# ADR-0003 — LangGraph Plan-and-Execute

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Orchestrator (with Srujan)

## Context
The agent architecture (30% weight) requires a stateful, inspectable reasoning pipeline that judges can trace and validate. The original LangChain Chain pattern was a single linear execution, which made it impossible to:

1. Show the reasoning trace (classify → context → plan → execute → synthesize)
2. Inject self-critic feedback mid-stream
3. Replay decisions for audit
4. Explain why a specific agent was chosen

The PS explicitly rewards LangGraph for its explicit control flow and ability to show work (Code Implementation 20% + Architecture 30%).

## Decision
We adopted **LangGraph Plan-and-Execute**:

- **Plan node:** Generates a structured plan (list of strings) that becomes part of AgentState
- **Execute node:** Invokes the appropriate agents based on intent (see `src/finroot/workflows/graph.py:30-38`)
- **Synthesize node:** Builds the final Recommendation from tool outputs

This maps directly to the 5-axis self-critic (0005) because:
- **Correctness:** Critic can verify each step's output
- **Risk:** Critic can flag unsafe recommendations
- **Actionability:** Plan can be shown to users
- **Explainability:** Full trace is available
- **Evidence:** Each tool output is cited

The graph is built in `src/finroot/agents/orchestrator.py:24` and converts between `AgentState` and `GraphState` for LangGraph compatibility.

## Consequences
- **Positive:** Judges can see the exact reasoning path; the system is auditable and explainable (FM-09, FM-07)
- **Positive:** Enables mid-stream self-critic injection (0005) and replay (0007)
- **Negative:** Slightly higher complexity than a single Chain; requires careful state management
- **Neutral:** Adds one more layer of indirection but improves modularity

## Alternatives considered
- **Single LangChain Chain:** Simpler but opaque; judges can't trace reasoning
- **CrewAI / AutoGen:** More agent orchestration but not PS-mandated; adds complexity without scoring benefit
- **Custom state machine:** Would reinvent LangGraph's features; less battle-tested

The Plan-and-Execute pattern is the minimal correct choice that satisfies both the PS requirements and the 5-axis self-critic architecture.