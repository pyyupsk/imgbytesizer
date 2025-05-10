# Changelog

All notable changes to imgbytesizer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-05-10

### Added

- New logging system with proper logger configuration (`logger.py`)
- Added debug mode with `--debug` flag for detailed error information
- Added quiet mode with `-q`/`--quiet` flag for minimal output
- Added version display with `-v`/`--version` flag
- Support for truncated images via `ImageFile.LOAD_TRUNCATED_IMAGES`
- Better non-TTY terminal support (no color, no progress bars)
- Added proper color detection for terminal output
- Improved error handling throughout the application
- Added development tools:
  - vulture for dead code detection
  - flake8 for linting
  - mypy for type checking
  - black for code formatting

### Changed

- Improved CLI interface with better help messages
- Refined image processing algorithms for better quality and speed
- Enhanced terminal output formatting with improved progress bars
- Better filesize formatting with consistent precision
- Optimized quality adjustment algorithm with more efficient binary search
- Improved format handling and normalization
- Code refactoring for better maintainability:
  - Split large functions into smaller, focused ones
  - Better separation of concerns
  - More consistent naming conventions
- Updated dependencies in requirements-dev.txt

### Fixed

- Fixed handling of image formats and extensions
- Fixed potential issues with terminal width detection
- Improved error messages for better user experience
- Fixed image quality optimization for different formats
- Fixed color output detection for various terminal types

## [0.1.0] - Initial Release

- Initial implementation of imgbytesizer
- Basic CLI interface
- Support for resizing images to target file sizes
- Support for JPG, PNG, and WebP formats
- Quality optimization for supported formats
