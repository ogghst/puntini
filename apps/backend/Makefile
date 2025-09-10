# Puntini Backend Makefile
# Provides convenient commands for development, testing, and linting

.PHONY: help install install-dev test test-cov lint lint-fix format type-check security-check clean run dev

# Default target
help: ## Show this help message
	@echo "Puntini Backend Development Commands"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies including linting tools
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install

# Testing
test: ## Run all tests
	python -m pytest

test-cov: ## Run tests with coverage report
	python -m pytest --cov=. --cov-report=html --cov-report=term-missing

test-fast: ## Run tests excluding slow tests
	python -m pytest -m "not slow"

# Code Quality
lint: ## Run all linting tools
	@echo "Running Ruff..."
	ruff check .
	@echo "Running Flake8..."
	flake8 .
	@echo "Running Pylint..."
	pylint api/ config/ models/ graphstore/ agent/ --rcfile=pyproject.toml
	@echo "Running MyPy..."
	mypy .
	@echo "Running Bandit security check..."
	bandit -r . -f json -o bandit-report.json || true
	@echo "Linting complete!"

lint-fix: ## Run linting tools and fix auto-fixable issues
	@echo "Running Ruff (with fixes)..."
	ruff check . --fix
	@echo "Running isort..."
	isort .
	@echo "Running Black..."
	black .
	@echo "Linting fixes complete!"

format: ## Format code with Black and isort
	black .
	isort .

type-check: ## Run type checking with MyPy
	mypy .

security-check: ## Run security checks with Bandit
	bandit -r . -f json -o bandit-report.json

# Pre-commit
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

# Development
run: ## Run the development server
	python main.py

dev: ## Run the development server with auto-reload
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Cleanup
clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -f bandit-report.json
	rm -f coverage.xml

# CI/CD helpers
ci-test: ## Run tests for CI/CD
	python -m pytest --cov=. --cov-report=xml --junitxml=test-results.xml

ci-lint: ## Run linting for CI/CD
	ruff check . --output-format=json > ruff-report.json || true
	flake8 . --output-file=flake8-report.txt || true
	mypy . --junit-xml=mypy-report.xml || true
	bandit -r . -f json -o bandit-report.json || true

# Docker helpers (if needed)
docker-build: ## Build Docker image
	docker build -t puntini-backend .

docker-run: ## Run Docker container
	docker run -p 8000:8000 puntini-backend

# Database helpers (if needed)
db-migrate: ## Run database migrations
	@echo "Database migration commands would go here"

db-seed: ## Seed database with test data
	@echo "Database seeding commands would go here"
