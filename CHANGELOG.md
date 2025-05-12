# Changelog

All notable changes to imgbytesizer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-05-12

### Added

- Implemented a new combined strategy of image upscaling and quality adjustment to better achieve target file sizes, especially when the original image is smaller than the target (`resizer.py`). This includes the `_try_combined_approach` function.
- Integrated `pytest` for automated testing, including a new `test` target in `Makefile` and a test execution step in the CI pipeline (`.github/workflows/publish.yml`, `Makefile`).
- Added `.flake8` configuration file with `max-line-length = 100`.

### Changed

- **Resizing Core Logic:**
  - Quality adjustment algorithm (`_try_quality_adjustment`, `_find_best_quality`) now uses a wider quality range (1-100, up from 1-95) and increased iterations (e.g., 12 from 10) for more precise results (`resizer.py`).
  - Binary search for optimal quality during resizing has been refined for better accuracy, attempting higher qualities if current size is under target and lower if over (`resizer.py`).
  - Resizing algorithm's (`_try_resizing`) binary search for scale factor now uses more iterations and finer step adjustments for scale (e.g., `high_scale - low_scale > 0.005`) (`resizer.py`).
  - Updated image resampling to use `Image.Resampling.LANCZOS` (modern Pillow API) instead of deprecated `Image.LANCZOS` (`resizer.py`).
  - Fallback image format for output path generation is now 'JPEG' if the original image format is undefined (e.g., `img.format or "JPEG"`) (`resizer.py`).
  - Logic for final adjustment to exact size improved, including handling cases where the image is larger than the target after initial processing by attempting a final quality adjustment (`_final_quality_adjustment` implied) (`resizer.py`).
- **Development Environment & CI:**
  - Replaced `flake8` with `ruff` for linting (e.g., `ruff check .`) and added `ruff --fix` to the formatting pipeline in `Makefile`.
  - `mypy` type checking and `black` formatting in `Makefile` now target the entire project (`.`) for broader coverage (e.g., `mypy .`, `black .`).
  - Updated Vulture dead code detection paths in `Makefile` to include `scripts` and `tests` directories.
  - CI pipeline (`.github/workflows/publish.yml`):
    - `check-version` job now depends on the successful completion of the `tests` job.
    - Enhanced GitHub Release step to update existing releases if a tag already exists, preventing errors (`gh release view "$TAG_NAME" ... else ... gh release create`).
    - Modified `TAG_NAME` environment variable logic in the publish workflow (`inputs.version_tag || github.ref_name`).
- **Code Quality & Readability:**
  - Significantly improved type hinting across the codebase for better maintainability and clarity (e.g., `Optional`, `Tuple`, `Union`, `ClassVar`, `Path` in `__init__.py`, `formatter.py`, `logger.py`, `main.py`, `resizer.py`).
  - `format_filesize` utility in `formatter.py` now gracefully handles `None` as input for file size, returning "N/A".
- **Documentation:**
  - Updated example usage (target size `1MB` from `250KB`) and example output in `README.md` to reflect the new resizing strategies, messages ("Trying combined scaling and quality approach...", "Combined approach success: scale=..."), and performance characteristics.

### Fixed

- Improved ability to reach target file sizes for images that are initially smaller than the target, due to the new combined upscaling and quality adjustment strategy.
- Enhanced robustness in determining output image format, particularly when the input image's format is not readily available from its metadata.
- Ensured progress bars and colored output are correctly suppressed when not in a TTY environment (existing but reinforced by type hints and explicit checks).

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
