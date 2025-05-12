.PHONY: build test lint typecheck format clean

# Build the package
build:
	python -m build

# Run tests
test:
	pip install -e .
	pytest

# Run linters (Vulture for dead code)
lint:
	vulture imgbytesizer scripts tests .vulture_ignore.py

# Run static type checks
typecheck:
	mypy .

# Auto-format code (Black for formatting + Isort for imports)
format:
	black .
	isort .

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
