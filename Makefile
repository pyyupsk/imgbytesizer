.PHONY: build lint typecheck format clean

# Build the package
build:
	python -m build

# Run linters
lint:
	flake8 imgbytesizer
	vulture imgbytesizer .vulture_ignore.py

# Run static type checks
typecheck:
	mypy imgbytesizer

# Auto-format code
format:
	black imgbytesizer

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info
