# Task wave-1/04 — Config, Settings & Prompt Registry

> Self-contained worker brief. Read `work/WORKER_PROMPT.md` + the contract, then build.

## Objective
A typed settings loader (env + sane defaults) and a versioned prompt registry. Critical params are
asserted at load and printed at startup so a silent revert fails loud (FM-06).

## Why it matters
Own-your-prompts + own-your-config (12-Factor). Single config source prevents drift; the prompt
registry keeps reasoning prompts versioned and inspectable (supports the 35% + reproducibility).

## Writes (ONLY these)
- `config/__init__.py`
- `config/settings.py`
- `config/prompts.py`
- `src/finroot/utils/__init__.py`
- `src/finroot/utils/config.py`
- `tests/unit/test_config.py`

## Forbid
Anything else. Import schema enums (e.g., `Provider`) from `src/finroot/schemas/` — don't redefine.

## Contracts to honor
- `schemas.contract.md` → `Provider` enum.
- Interface:
  ```python
  class Settings(BaseSettings):           # pydantic-settings
      llm_provider: Provider = Provider.MOCK
      ollama_base_url: str = "http://localhost:11434"
      ollama_model: str = "llama3.1:8b"
      groq_api_key: str | None = None
      openai_api_key: str | None = None
      chroma_dir: str = "data/chroma"
      audit_path: str = "logs/audit.jsonl"
      env_prefix = "FINROOT_"
  def get_settings() -> Settings: ...      # cached
  class PromptRegistry:                     # name+version -> template
      def get(self, name: str, version: str = "latest") -> str: ...
  ```

## Steps
1. `settings.py`: `Settings` (pydantic-settings) reading `FINROOT_*` env with defaults; `get_settings()` cached.
2. `config.py`: assert critical params at load; print a one-line startup banner of active config.
3. `prompts.py`: a small registry seeding the system prompts the agent will use (placeholders are fine;
   reasoning prompts get filled in W4/W5) — keyed by name + version.
4. Tests: defaults load with no env; `FINROOT_LLM_PROVIDER=ollama` overrides; registry returns a prompt
   by name+version and errors on unknown name (loud, FM-11).

## Acceptance (paste real output)
```bash
ruff check src/finroot/utils/ config/
FINROOT_LLM_PROVIDER=ollama python -c "from config.settings import get_settings; print(get_settings().llm_provider)"
pytest tests/unit/test_config.py -v
```

## Domain rules
Unknown prompt name → error, not a blank default. Secrets only from env; never commit real keys (FM-07).

## Report
`work/reports/wave-1/04-config-settings.report.md`.
