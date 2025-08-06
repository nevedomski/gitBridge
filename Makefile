.PHONY: help install install-dev install-all format lint type-check test clean run

help:
	@echo "Available commands:"
	@echo "  make install      Install the package (core dependencies only)"
	@echo "  make install-dev  Install with development dependencies"
	@echo "  make install-all  Install all dependencies (dev + docs + windows if on Windows)"
	@echo "  make format       Format code with ruff"
	@echo "  make lint         Lint code with ruff"
	@echo "  make type-check   Type check with mypy"
	@echo "  make test         Run tests with pytest"
	@echo "  make clean        Clean build artifacts"
	@echo "  make run ARGS=... Run gitbridge CLI with arguments"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

install-all:
	uv pip install -e ".[all]"

format:
	uv run ruff format .

lint:
	uv run ruff check . --fix

type-check:
	uv run mypy gitbridge

test:
	uv run pytest

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Usage: make run ARGS="sync --config config.yaml"
run:
	uv run gitbridge $(ARGS)