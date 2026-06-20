# FinRoot — developer entry points. Mock mode needs zero keys.
.DEFAULT_GOAL := help
PY ?= python

.PHONY: help install smoke lint test cli ui evals validate docker clean

help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## install deps (editable)
	pip install -r requirements.txt && pip install -e .

smoke:  ## run the foundation smoke test
	$(PY) scripts/smoke_test.py

lint:  ## ruff check
	ruff check src/ tests/ scripts/

test:  ## run pytest
	pytest

cli:  ## run the CLI (ARGS="--mock 'your question'")
	$(PY) -m interface.cli $(ARGS)

ui:  ## run the Streamlit UI
	streamlit run src/interface/ui/app.py

evals:  ## run the FRB reasoning benchmark -> results/metrics.json
	$(PY) scripts/run_evals.py --all

validate:  ## structural + execution-drift checks
	bash orchestrator/scripts/validate.sh && bash orchestrator/scripts/validate_execution.sh

docker:  ## build + run the full stack
	docker compose up --build

clean:  ## remove caches + generated artifacts (keeps source)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + ; rm -rf .pytest_cache .ruff_cache
