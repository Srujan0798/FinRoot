# FinRoot — developer entry points. Mock mode needs zero keys.
.DEFAULT_GOAL := help
PY ?= python3

.PHONY: help install smoke lint test test-fast test-slow test-cold test-zip cli ui evals validate validate-docs validate-links changelog-suggest session-start coverage metrics-drift test-pyramid dep-audit ship-prep doctor docker clean

help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## install deps (editable)
	pip install -r requirements.txt && pip install -e .

smoke:  ## run the foundation smoke test
	$(PY) scripts/smoke_test.py

lint:  ## ruff check
	ruff check src/ tests/ scripts/

test:  ## run all pytest tests (including @pytest.mark.slow)
	pytest

test-fast:  ## run pytest skipping @pytest.mark.slow tests
	pytest -m 'not slow'

test-slow:  ## run only @pytest.mark.slow tests
	pytest -m slow

test-cold:  ## 3x cold suite, fails on any non-zero rc or any data/ leakage
	@bash scripts/cold_check.sh

cli:  ## run the CLI (ARGS="--mock 'your question'")
	$(PY) -m interface.cli $(ARGS)

ui:  ## run the Streamlit UI
	streamlit run src/interface/ui/app.py

evals:  ## run the FRB reasoning benchmark -> results/metrics.json
	$(PY) scripts/run_evals.py --all

validate:  ## structural + execution-drift + doc-drift checks
	bash orchestrator/scripts/validate.sh && bash orchestrator/scripts/validate_execution.sh && bash orchestrator/scripts/validate_docs.sh

validate-docs:  ## scan .md files for stale SHA / metric references
	bash orchestrator/scripts/validate_docs.sh

validate-links:  ## check that internal .md cross-references resolve
	bash orchestrator/scripts/validate_doc_links.sh

# One-command "I'm about to ship" target. Refreshes the metric, regenerates
# docs if they cite a stale SHA, and rebuilds the zip. Run before tagging
# a release.
ship-prep:  ## regenerate metric + rebuild zip + check consistency
	make evals
	bash scripts/make_submission.sh
	bash orchestrator/scripts/validate_docs.sh
	bash orchestrator/scripts/validate_doc_links.sh
	@echo
	@echo "=== ship-prep complete. Verify:"
	@echo "  unzip -p finroot-submission.zip results/metrics.json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d[\"as_of_sha\"],d[\"systems\"][\"finroot\"][\"mean_score\"])'"
	@echo "  make session-start"

doctor:  ## smoke-check all integrations (Python, CLI, validators, zip, data)
	bash scripts/doctor.sh

test-failures:  ## show a summary of the most recent test failures
	bash scripts/test_failures.sh

# "CI" — full quality gate, what you'd run before a release. Includes
# everything: lint, fast tests, coverage, validators, doctor. Excludes
# slow + stress tests (those are run separately on a longer schedule).
ci:  ## full quality gate (lint + test-fast + coverage + validate + doctor)
	ruff check src/ tests/ scripts/ config/
	$(MAKE) test-fast
	$(MAKE) coverage
	$(MAKE) validate
	$(MAKE) doctor

changelog-suggest:  ## print a draft CHANGELOG entry from the last 10 commits
	bash scripts/changelog_suggest.sh

session-start:  ## print a one-page context summary (HEAD, metric, tests, dirty tree)
	bash scripts/session_start.sh

coverage:  ## run pytest with coverage and fail if below threshold (default 80%)
	bash scripts/coverage_check.sh

metrics-drift:  ## compare two metrics.json files; exit 1 if regression > threshold
	bash scripts/metrics_drift.sh HEAD:results/metrics.json results/metrics.json

test-pyramid:  ## print test counts by category (unit/integration/e2e/...) and time budget
	bash scripts/test_pyramid.sh

dep-audit:  ## check for outdated / vulnerable dependencies
	bash scripts/dep_audit.sh

docker:  ## build + run the full stack
	docker compose up --build

clean:  ## remove caches + generated artifacts (keeps source)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + ; rm -rf .pytest_cache .ruff_cache
