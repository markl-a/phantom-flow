.PHONY: help build up down restart logs test clean install lint format docker-build docker-push init docs examples

# Default target
help:
	@echo "Data Analysis with Chatbots - Makefile Commands"
	@echo "======================================================="
	@echo "🚀 Quick Start:"
	@echo "  make quickstart    - Complete setup (install + init)"
	@echo "  make run           - Run Streamlit dashboard"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs"
	@echo "  make shell         - Open shell in app container"
	@echo ""
	@echo "💻 Development Commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make init          - Initialize project structure"
	@echo "  make test          - Run all tests"
	@echo "  make test-fast     - Run tests without coverage"
	@echo "  make test-watch    - Run tests in watch mode"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean temporary files"
	@echo ""
	@echo "📊 Analysis Commands:"
	@echo "  make cluster       - Run clustering comparison"
	@echo "  make examples      - Run all example scripts"
	@echo "  make download-data - Download all datasets"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  make docs          - Generate Sphinx documentation"
	@echo "  make docs-serve    - Serve documentation locally"
	@echo ""
	@echo "🔬 CI/CD Commands:"
	@echo "  make ci            - Run full CI pipeline locally"
	@echo "  make coverage      - Generate coverage report"
	@echo "  make benchmark     - Run performance benchmarks"

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

shell:
	docker-compose exec app /bin/bash

# Development commands
install:
	@echo "📦 Installing dependencies..."
	pip install -e ".[dev]"
	pre-commit install
	@echo "✅ Installation complete!"

init:
	@echo "⚡ Initializing project structure..."
	python -m data_analysis_chatbots.init --with-examples
	@echo "✅ Project initialized!"

test:
	@echo "🧪 Running tests with coverage..."
	pytest -v --cov=src/data_analysis_chatbots --cov-report=term-missing

test-fast:
	@echo "⚡ Running fast tests..."
	pytest -v -x

test-watch:
	@echo "👀 Running tests in watch mode..."
	pytest-watch

coverage:
	@echo "📊 Generating coverage report..."
	pytest --cov=src/data_analysis_chatbots --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated in htmlcov/index.html"

lint:
	@echo "🔍 Running linters..."
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports
	bandit -r src/ -ll
	@echo "✅ Linting complete!"

format:
	@echo "🎨 Formatting code..."
	black src/ tests/
	isort src/ tests/
	@echo "✅ Code formatted!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/

# CI pipeline
ci: format lint test
	@echo "CI pipeline completed successfully!"

# Docker registry
docker-build:
	docker build -t data-analysis-chatbots:latest .

docker-push:
	docker tag data-analysis-chatbots:latest yourusername/data-analysis-chatbots:latest
	docker push yourusername/data-analysis-chatbots:latest

# Run Streamlit locally
run:
	streamlit run app.py

# Analysis commands
cluster:
	@echo "📊 Running clustering comparison..."
	python examples/clustering_comparison.py

examples:
	@echo "🚀 Running all example scripts..."
	python examples/complete_analysis_workflow.py
	python examples/clustering_comparison.py

download-data:
	@echo "⬇️  Downloading datasets..."
	python -m data_analysis_chatbots.data_downloader --all

# Documentation
docs:
	@echo "📚 Generating Sphinx documentation..."
	cd docs/sphinx && make html
	@echo "✅ Documentation built in docs/sphinx/_build/html/"

docs-serve:
	@echo "🌐 Serving documentation on http://localhost:8000..."
	cd docs/sphinx/_build/html && python -m http.server 8000

# Benchmark
benchmark:
	@echo "⏱️  Running performance benchmarks..."
	pytest tests/test_advanced_clustering.py -v --benchmark-only 2>/dev/null || \
	python -m pytest tests/ -k "benchmark" -v

# Quick start
quickstart: install init
	@echo ""
	@echo "✅ Setup complete!"
	@echo "=================="
	@echo "Next steps:"
	@echo "  1. Download data: make download-data"
	@echo "  2. Run examples:  make examples"
	@echo "  3. Start app:     make run"
	@echo ""
