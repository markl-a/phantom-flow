# Makefile — Automation_with_Agent
#
# Cross-platform conventions: works on macOS / Linux / Windows-with-make.
# The demo target depends only on Python stdlib so `make demo` works
# without `pip install` first — that's the recruiter-clones-and-runs
# story.
#
#   make demo     30-second proof-of-life (no API keys needed)
#   make install  pip install -e . (developer setup)
#   make test     pytest test_*.py
#   make lint     black + ruff
#   make help     this list

PY ?= python3

.PHONY: help demo install dev-install test lint format clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

demo:  ## 30-second proof-of-life demo (URL → RAG → LLM, mock by default)
	@$(PY) demo.py

demo-llm:  ## Same demo but force a real LLM call (needs API key in env)
	@$(PY) demo.py --use-llm

install:  ## pip install -e . (with all optional deps)
	@$(PY) -m pip install -e ".[all]"

dev-install:  ## pip install -e .[all,dev] (includes pytest, black, ruff, mypy)
	@$(PY) -m pip install -e ".[all,dev]"

test:  ## Run pytest
	@$(PY) -m pytest -q

lint:  ## Static checks (black --check + ruff)
	@$(PY) -m black --check . || true
	@$(PY) -m ruff check . || true

format:  ## Auto-format with black
	@$(PY) -m black .

clean:  ## Remove build artifacts
	@rm -rf build dist *.egg-info .pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
