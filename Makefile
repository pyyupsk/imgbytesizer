.PHONY: build test lint typecheck format clean

# Build the package
build:
	python -m build

# Run tests
test:
	pytest

# Run linters (Ruff for fast linting + Vulture for dead code)
lint:
	ruff check .
	vulture imgbytesizer scripts tests .vulture_ignore.py

# Run static type checks
typecheck:
	mypy .

# Auto-format code (Black for formatting + Ruff for autofixable linting)
format:
	ruff check . --fix
	black .

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
