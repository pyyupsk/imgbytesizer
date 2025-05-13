.PHONY: build test lint typecheck format clean

# Build the package
build:
	python -m build

# Run tests
test:
	pytest tests/ --cov=imgbytesizer --cov-report=xml

# Run linters (Vulture for dead code)
lint:
	vulture imgbytesizer scripts tests .vulture_ignore.py

# Run static type checks
typecheck:
	mypy .

# Auto-format code (YAPF for formatting)
format:
	yapf -ir imgbytesizer scripts tests

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
