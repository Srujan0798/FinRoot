# Task wave-1/01 — LLM Provider Layer

> Self-contained worker brief. Read `work/WORKER_PROMPT.md` + the contract below, then build.

## Objective
Build a single `LLMProvider` abstraction with four interchangeable adapters: **Mock** (deterministic,
offline), **Ollama** (local sovereign default), **Groq**, **OpenAI**. A factory `get_provider(name)`
returns the right one. Every completion supports extracting `<reasoning>` and `<confidence>` tags.

## Why it matters
Sovereignty (PRD O4) + Architecture (30%): the agent must run offline (Mock) and locally (Ollama)
with zero keys. Every later wave calls this layer; the Mock adapter makes all tests + judging deterministic.

## Writes (ONLY these)
- `src/finroot/llm/__init__.py`
- `src/finroot/llm/base.py`
- `src/finroot/llm/mock.py`
- `src/finroot/llm/ollama.py`
- `src/finroot/llm/groq.py`
- `src/finroot/llm/openai.py`
- `src/finroot/llm/factory.py`
- `tests/unit/test_llm_provider.py`

## Forbid
Anything outside `src/finroot/llm/**` and that one test file. Do NOT edit `schemas/` (task 02 owns it)
— import from it.

## Contracts to honor
- `.specify/specs/wave-1/contracts/schemas.contract.md` → use `Provider` enum + types.
- Interface:
  ```python
  class LLMProvider(Protocol):
      name: str
      def complete(self, prompt: str, *, system: str | None = None,
                   temperature: float = 0.2, max_tokens: int = 1024) -> LLMResult: ...
  class LLMResult(BaseModel):
      text: str; reasoning: str | None; confidence: str | None
      provider: str; model: str; tokens: int | None = None
  def get_provider(name: str | Provider | None = None) -> LLMProvider  # default from settings/env
  ```

## Steps
1. Define `LLMProvider` protocol + `LLMResult` in `base.py`, plus `parse_reasoning_confidence(text)`.
2. `mock.py`: deterministic canned responses keyed by prompt hash; **no network**; always parses
   reasoning/confidence so downstream code is exercised. Reports `model="mock"`.
3. `ollama.py` / `groq.py` / `openai.py`: thin adapters; **lazy-import** the SDK so Mock needs none.
   Missing key/SDK → raise a clear typed error (FM-11), never silently fall back.
4. `factory.get_provider`: resolve from arg → `FINROOT_LLM_PROVIDER` env → default `mock` (tests).
5. Tests: mock completes offline; factory resolves each name; reasoning/confidence parsed; missing-key
   provider raises (not silent).

## Acceptance (paste real output into report)
```bash
ruff check src/finroot/llm/
python -c "from finroot.llm import get_provider; r=get_provider('mock').complete('hi'); print(r.provider, r.text[:20])"
pytest tests/unit/test_llm_provider.py -v
```

## Domain rules
Fail loud on missing keys; never fabricate completions in real providers; Mock is clearly labeled `mock`.

## Report
`work/reports/wave-1/01-llm-provider-layer.report.md` (use `work/REPORT_TEMPLATE.md`).
