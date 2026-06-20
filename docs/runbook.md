# Runbook — operating FinRoot

> Day-to-day commands once waves ship. Build-process runbook is `HOW_TO_RUN.md`.

## Setup
```bash
make install            # pip install -r requirements.txt (or pip install -e .)
cp .env.example .env    # optional — Mock + Ollama need no keys
```

## Run
```bash
make cli ARGS="--mock 'analyze my portfolio'"      # offline, deterministic
make ui                                            # streamlit dark UI (Mock default)
FINROOT_LLM_PROVIDER=ollama make ui                # sovereign local mode
```

## Evaluate (the 35% proof)
```bash
make evals                          # FRB across systems → results/metrics.json + evals/reports/
python scripts/run_evals.py --mock --task 001
```

## Quality gates
```bash
make lint      # ruff check
make test      # pytest
make smoke     # python scripts/smoke_test.py → FOUNDATION OK
```

## Containers
```bash
docker compose up                                   # full stack
docker compose -f docker-compose.yml -f docker-compose.dev.yml up   # hot reload
```

## Troubleshooting
- No keys / offline → use `--mock` or `FINROOT_LLM_PROVIDER=mock` (default).
- Ollama not responding → `ollama serve`; check `FINROOT_OLLAMA_BASE_URL`.
- Chroma missing → semantic memory falls back to JSON automatically.
- Audit verify fails → see INCIDENT_RESPONSE_PLAYBOOK (don't auto-repair).
