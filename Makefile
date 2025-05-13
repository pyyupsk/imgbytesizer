.PHONY: build test lint format typecheck clean

# Build the package
build:
	python -m build

# Run tests
test:
	pytest tests/ --cov=imgbytesizer --cov-report=xml

# Run linters (Flake8 for PEP8, Vulture for dead code)
lint:
	flake8 imgbytesizer scripts tests
	vulture imgbytesizer scripts tests .vulture_ignore.py

# Auto-format code (YAPF for formatting)
format:
	yapf -ir imgbytesizer scripts tests

# Run static type checks
typecheck:
	mypy imgbytesizer scripts tests

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
