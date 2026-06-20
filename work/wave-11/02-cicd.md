# Task wave-11/02 — CI/CD + GitHub Actions

> Read `work/WORKER_PROMPT.md` then build. Shows professional engineering practice.

## Objective
Add GitHub Actions workflows for automated testing, linting, and FRB evaluation on every push.
This shows judges the project has CI/CD discipline.

## Writes (ONLY these)
- `.github/workflows/ci.yml` (update existing)
- `.github/workflows/test.yml` (update existing)
- `.github/workflows/evals.yml` (update existing)

## Forbid
All other files.

## Steps
1. Read existing `.github/workflows/` files.
2. Update `ci.yml`:
   - Run on push to main and PRs
   - Python 3.11 matrix
   - Steps: checkout, setup-python, pip install, ruff check, pytest
   - Cache pip dependencies
3. Update `test.yml`:
   - Run on push to main and PRs
   - Run full test suite: `PYTHONPATH=src python3 -m pytest tests/ -q`
   - Run golden tests: `PYTHONPATH=src python3 -m pytest tests/golden/ -q`
   - Upload test results as artifacts
4. Update `evals.yml`:
   - Run on push to main only
   - Run FRB harness: `PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1`
   - Upload results/metrics.json as artifact
   - Comment on PR with FRB results (if applicable)
5. Ensure all workflows use `FINROOT_LLM_PROVIDER=mock` for offline testing.

## Acceptance
```bash
cat .github/workflows/ci.yml | head -20
cat .github/workflows/test.yml | head -20
cat .github/workflows/evals.yml | head -20
```

## Report
`work/reports/wave-11/02-cicd.report.md`
