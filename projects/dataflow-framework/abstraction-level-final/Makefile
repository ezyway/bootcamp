# Makefile for Real-Time Processing Project using UV (Astral) runner

# Variables
PYTHON=python3
UV=uv

.PHONY: help run run-watch test lint clean build publish

help:
	@echo "Available commands:"
	@echo "  run         Run the app in single file mode. Usage: make run INPUT=<file>"
	@echo "  run-watch   Run the app in watch mode (monitoring watch_dir)"
	@echo "  test        Run tests (add as needed)"
	@echo "  lint        Run linting (add as needed)"
	@echo "  clean       Remove build and temporary files"
	@echo "  build       Build the Python package"
	@echo "  publish     Publish package to PyPI (or TestPyPI if configured)"

# Run in single file mode
run:
ifndef INPUT
	$(error INPUT variable is not set. Usage: make run INPUT=<file>)
endif
	$(UV) run cli.py --input $(INPUT) --trace --dashboard

# Run in watch mode (monitor folder)
run-watch:
	$(UV) run cli.py --watch --trace --dashboard

# Placeholder for running tests
test:
	@echo "No tests configured"

# Placeholder for linting
lint:
	@echo "No linting configured"

# Clean build artifacts and virtual env files
clean:
	rm -rf build dist *.egg-info .uv

# Build package (assumes pyproject.toml and build system configured)
build:
	$(PYTHON) -m build