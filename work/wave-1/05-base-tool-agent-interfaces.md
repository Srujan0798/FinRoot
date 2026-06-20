# Task wave-1/05 — Base Tool & Agent Interfaces

> Self-contained worker brief. Read `work/WORKER_PROMPT.md` + the contract, then build.

## Objective
The `BaseTool` and `BaseAgent` abstractions every wave-3 tool and wave-4 agent will extend. `BaseTool`
bakes in TTL cache, token-bucket rate limit, retry+backoff, **loud failure (no synthetic data)**, and
an audit-emit hook. `BaseAgent` defines the ReAct/sub-agent contract over the LLM + tools.

## Why it matters
Architecture (30%) + Code (20%): consistent, robust tool/agent contracts are what make 12 tools and 6
agents uniform and reviewable. The loud-fail + audit-emit defaults enforce FM-11 everywhere by construction.

## Writes (ONLY these)
- `src/finroot/tools/__init__.py`
- `src/finroot/tools/base.py`
- `src/finroot/agents/__init__.py`
- `src/finroot/agents/base.py`
- `tests/unit/test_base_interfaces.py`

## Forbid
Concrete tools (wave-3) or concrete agents (wave-4). Only the base classes here. Import schemas +
audit + llm from their packages; don't reimplement them.

## Contracts to honor
- `schemas.contract.md`, the `AuditTrail` interface (task 03), the `LLMProvider` interface (task 01).
- Interface:
  ```python
  class BaseTool(ABC, Generic[In, Out]):
      name: str; ttl_seconds: int = 300; rate_per_sec: float = 5.0
      def __call__(self, inp: In) -> Out: ...        # cache→rate-limit→_run→audit-emit
      @abstractmethod
      def _run(self, inp: In) -> Out: ...            # subclass implements; raises on bad input (loud)
  class BaseAgent(ABC):
      name: str; tools: list[BaseTool]
      def __init__(self, llm: LLMProvider, tools: list[BaseTool], audit: AuditTrail): ...
      @abstractmethod
      def act(self, state: AgentState) -> AgentState: ...
  ```

## Steps
1. `tools/base.py`: implement the cache (TTL), token-bucket rate limiter, retry+backoff wrapper, and
   audit-emit on every call; `_run` is abstract. A failing `_run` raises loud (no fallback data).
2. `agents/base.py`: `BaseAgent` holding llm+tools+audit; `act(state)->state` abstract; helper to call
   a tool and record the citation.
3. Tests with a tiny dummy tool/agent: cache returns same result within TTL; rate limit enforced;
   `_run` raising propagates loud (not swallowed); audit event emitted per call.

## Acceptance (paste real output)
```bash
ruff check src/finroot/tools/base.py src/finroot/agents/base.py
pytest tests/unit/test_base_interfaces.py -v
```

## Domain rules
No silent fallback to cache on error; expired/failed → loud or clearly-low-confidence (FM-11). Every
tool call emits an audit event.

## Report
`work/reports/wave-1/05-base-tool-agent-interfaces.report.md`.
