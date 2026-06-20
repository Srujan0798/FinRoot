# Task wave-8/01 — Dockerfile + Compose + healthcheck

> Read `work/WORKER_PROMPT.md` then build. Depends on W7 (UI). One-command spin-up.

## Objective
Containerize FinRoot so judges run the whole demo with one command, fully offline (Mock mode).

## Writes (ONLY these)
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

## Forbid
All other files. (If a seed `Dockerfile`/`docker-compose.yml` exists, REPLACE with the hardened version and note it in the report.)

## Contract
Read `.specify/specs/wave-8/contracts/submission.contract.md` § Docker.

## Steps
1. `Dockerfile`:
   - `FROM python:3.11-slim`; set workdir; copy `pyproject.toml` + `src/` etc.; `pip install -e .` (and UI extras: streamlit, typer, rich — add an `[ui]` extra in pyproject if missing? NO — do not edit pyproject; instead `pip install streamlit typer rich` explicitly in the image).
   - Create a non-root user, run as it.
   - `ENV FINROOT_LLM_PROVIDER=mock` (offline default).
   - `EXPOSE 8501`; `HEALTHCHECK` curling `http://localhost:8501/_stcore/health`.
   - `CMD ["streamlit", "run", "src/interface/ui/app.py", "--server.address=0.0.0.0", "--server.port=8501"]`.
2. `docker-compose.yml`:
   - service `finroot`, build `.`, ports `8501:8501`, `environment: FINROOT_LLM_PROVIDER=mock`, optional `.env` mount (commented), `restart: unless-stopped`, healthcheck.
3. `.dockerignore`: `.git`, `__pycache__`, `*.pyc`, `.venv`, `venv`, `*.db`, `data/chroma`, `data/watchlists`, `logs`, `.env`, `*.key`, `.pytest_cache`, `.ruff_cache`, `work/`, `attic/`.

## Acceptance
```bash
docker build -t finroot:demo . 2>&1 | tail -5    # builds clean (if docker available)
# If docker unavailable in this env, validate syntax:
python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml')); print('compose YAML valid')"
test -f Dockerfile && test -f .dockerignore && echo "files present"
```
Note in report whether docker build was actually run or only syntax-validated (FM-09).

## Report
`work/reports/wave-8/01-docker.report.md`
