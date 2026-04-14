# Changelog

All notable changes to imgbytesizer will be documented in this file.

## [0.2.6] - 2026-04-14

### 🐛 Bug Fixes

- Resolve ty type checker errors in logger and resizer

### 💼 Other

- Migrate from poetry to uv
- Add release automation with git-cliff and release script

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG for v0.2.5 release date change to 2025-05-25
- Pin actions to commit SHAs and bump Python to 3.10
## [0.2.5] - 2025-05-25

### 📚 Documentation

- Add Quality Gate Status badge to README for better visibility of code quality

### 🧪 Testing

- Add and improve tests for image setup, format conversion, and size adjustments

### ⚙️ Miscellaneous Tasks

- Refactor resize_to_target_filesize; add image helpers for setup, format, scaling; improve clarity
## [0.2.4] - 2025-05-19

### ⚙️ Miscellaneous Tasks

- Switch from build to poetry for package building, add poetry.lock, and remove requirements files
- Update poetry.lock; adjust tox.ini for command order and cleanup
- Add CI workflow for automated testing and coverage reporting; update publish workflow for Poetry integration
- Add imgbytesizer script entry point in pyproject.toml
- Tidy up imports in logger, resizer, and test files for better readability
## [0.2.3] - 2025-05-14

### 🐛 Bug Fixes

- Update type checking to use 'ty', adjust file size formatting, and clean up logger setup

### 🚜 Refactor

- Enhance type annotations, improve file size formatting, and streamline logger setup

### 📚 Documentation

- Update README and main.py for consistent example formatting and added version flag

### ⚙️ Miscellaneous Tasks

- Add script to sort requirements files and ensure consistent ordering
- Replace mypy type checker with 'ty' in VSCode extensions
- Add pyfiglet dependency, enhance type annotations in logger and main modules, and tidy up imports
- Add virtual environment setup in GitHub Actions for publish and test workflows
- Activate virtual environment in GitHub Actions for build, test, and lint jobs
- Activate virtual environment in publish workflow before version check
## [0.2.2] - 2025-05-13

### 🚜 Refactor

- Clean up formatter and logger by removing unused functions and consolidating imports

### 🧪 Testing

- Add comprehensive tests for main functionality and resizer edge cases
- Add entrypoint test and improve utility tests for image handling

### ⚙️ Miscellaneous Tasks

- Update Makefile and requirements for linting and formatting improvements
- Add GitHub Actions workflow for testing and linting, update file size formatting function
- Update Makefile to run tests with coverage and add pytest-cov to requirements
- Add requirements.txt installation step to GitHub Actions workflow
- Add editable install step for local development in GitHub Actions workflow
- Update codecov action to v5 and add token and verbose options in GitHub Actions workflow
- Remove isort from formatting and requirements, update code style in imports
- Add Codecov badge to README for better visibility of test coverage
- Update formatting and linting configurations, add YAPF style guide, and adjust flake8 settings
- Add mypy type checker and YAPF formatter to VSCode extensions
- Update Makefile and GitHub Actions for improved linting and type checking
## [0.2.1] - 2025-05-12

### 🚀 Features

- Enhance GitHub Actions workflow to create or update releases based on existence, improving asset handling
- Add testing framework with pytest, update Makefile for test execution, and configure flake8 for code style enforcement
- Update Makefile for improved linting and formatting, add ruff for linting and autofix, enhance type hints across the codebase
- Enhance image resizing logic with combined scaling and quality adjustment, improve error handling, and extend quality range for better results
- Add CI tests to GitHub Actions workflow, including Python setup and dependency installation

### 🐛 Bug Fixes

- Update TAG_NAME assignment in GitHub Actions workflow to prioritize version_tag over github.ref_name for better release tagging
- Adjust _adjust_to_exact_size function to remove unnecessary parameter

### 📚 Documentation

- Update README example output to reflect new image dimensions, sizes, and processing times for imgbytesizer

### ⚙️ Miscellaneous Tasks

- Bump version to 0.2.1 in pyproject.toml and __init__.py
- Add requirements installation step in GitHub Actions workflow
- Update GitHub Actions workflow to use Makefile for testing and building
- Remove redundant test job from GitHub Actions workflow, simplifying CI process
## [0.2.0] - 2025-05-10

### 🚀 Features

- Add version check script and enhance GitHub Actions workflow for dependency installation and version validation
- Bump version to 0.2.0, add author and description, enhance logging and terminal output features
- Add vulture ignore file, enhance Makefile for linting, and update dev dependencies
- Update CHANGELOG for version 0.2.0, document new features, changes, and fixes
- Improve JPEG handling in _adjust_to_exact_size function

### 📚 Documentation

- Update README with new command-line options and example output for imgbytesizer

### ⚙️ Miscellaneous Tasks

- Add Makefile for build and lint tasks, update development dependencies
## [0.1.0] - 2025-05-09

### 🚀 Features

- Init commit with setup files
- Enhance image resizing tool with progress indicators and detailed output
- Add LICENSE and project metadata for imgbytesizer CLI tool
- Add GitHub Actions workflow for automated release publishing
- Implement core functionality for imgbytesizer CLI tool with image resizing and utility functions
- Enhance GitHub Actions workflow to support manual version tagging and improve release asset handling

### 🐛 Bug Fixes

- Update Python version requirement to 3.9

### 📚 Documentation

- Add README.md with usage instructions, features, and examples for ImgByteSizer
- Add CHANGELOG.md for version 0.1.0 with initial release details

### ⚙️ Miscellaneous Tasks

- Add .gitignore file to exclude unnecessary files from version control
- Add VSCode extensions recommendations for Python development
- Update dependencies to use requirements-dev.txt for development and remove outdated build dependency from requirements.txt
