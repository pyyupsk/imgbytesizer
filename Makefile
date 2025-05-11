.PHONY: build test lint typecheck format clean

# Build the package
build:
	python -m build

# Run tests
test:
	pytest

# Run linters
lint:
	flake8 imgbytesizer tests
	vulture imgbytesizer tests .vulture_ignore.py

# Run static type checks
typecheck:
	mypy imgbytesizer tests

# Auto-format code
format:
	black imgbytesizer tests

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
