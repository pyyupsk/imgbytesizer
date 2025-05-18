"""
Logging utilities for imgbytesizer.
"""

import logging
from typing import Final, Optional, Tuple, TextIO

from .formatter import format_filesize


# ANSI Color Codes for beautiful terminal output
class Colors:
  RED: Final[str] = "\033[91m"
  GREEN: Final[str] = "\033[92m"
  YELLOW: Final[str] = "\033[93m"
  ENDC: Final[str] = "\033[0m"
  UNDERLINE: Final[str] = "\033[4m"


def setup_logger() -> logging.Logger:
  """Set up and configure the logger."""
  logger: logging.Logger = logging.getLogger("imgbytesizer")
  logger.setLevel(logging.INFO)

  # Create console handler
  handler: logging.StreamHandler[TextIO] = logging.StreamHandler()  # type: ignore
  handler.setLevel(logging.INFO)

  # Create formatter
  formatter: logging.Formatter = logging.Formatter(
      "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  )
  handler.setFormatter(formatter)

  # Add handler to logger
  logger.addHandler(handler)

  return logger


def print_result(label: str, value: str, status: Optional[str] = None) -> None:
  """Print a name-value pair with optional status color."""
  if status == "good":
    value = f"{Colors.GREEN}{value}{Colors.ENDC}"
  elif status == "bad":
    value = f"{Colors.RED}{value}{Colors.ENDC}"
  elif status == "warning":
    value = f"{Colors.YELLOW}{value}{Colors.ENDC}"

  print(f"{label:12} {value}")


def print_comparison_table(
    orig_size: int,
    orig_dimensions: Tuple[int, int],
    final_size: int,
    final_dimensions: Tuple[int, int],
    target_size: int,
) -> None:
  """Print a comparison table of original and final image properties."""
  print("\nComparison:")
  print("-" * 40)

  # Original dimensions
  orig_width, orig_height = orig_dimensions
  print_result("Original", f"{orig_width} × {orig_height} pixels")
  print_result("Size", format_filesize(orig_size))

  # Final dimensions
  final_width, final_height = final_dimensions
  print_result("Final", f"{final_width} × {final_height} pixels")
  print_result("Size", format_filesize(final_size))

  # Target size
  print_result("Target", format_filesize(target_size))

  # Calculate and print differences
  size_diff: int = final_size - orig_size
  size_diff_percent: float = (size_diff / orig_size) * 100
  size_status: str = "good" if size_diff <= 0 else "bad"

  print_result(
      "Size change",
      f"{format_filesize(size_diff)} ({size_diff_percent:+.1f}%)",
      size_status,
  )

  # Dimension changes
  width_diff: int = final_width - orig_width
  height_diff: int = final_height - orig_height
  width_diff_percent: float = (width_diff / orig_width) * 100
  height_diff_percent: float = (height_diff / orig_height) * 100

  print_result(
      "Width change",
      f"{width_diff:+d} pixels ({width_diff_percent:+.1f}%)",
      "good" if width_diff <= 0 else "warning",
  )
  print_result(
      "Height change",
      f"{height_diff:+d} pixels ({height_diff_percent:+.1f}%)",
      "good" if height_diff <= 0 else "warning",
  )

  print("-" * 40)


def print_processing_step(step: int, message: str) -> None:
  """Print a processing step with step number."""
  print(f"\n[{step}] {message}")


def print_progress_bar(
    iteration: int,
    total: int,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 50,
    fill: str = "█",
) -> None:
  """Print a progress bar."""
  percent: str = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
  filled_length: int = int(length * iteration // total)
  bar: str = fill * filled_length + "-" * (length - filled_length)
  print(f"\r{prefix} |{bar}| {percent}% {suffix}", end="\r")
  if iteration == total:
    print()
