"""
Terminal formatting utilities for imgbytesizer.
"""

from typing import Optional


def format_filesize(size_bytes: Optional[int], precision: int = 2) -> str:
  """Format file size in a human-readable format."""
  if size_bytes is None:
    return "N/A"

  if size_bytes < 1024:
    return f"{size_bytes} B"
  elif size_bytes < 1024 * 1024:
    return f"{size_bytes / 1024:.{precision}f} KB"
  else:
    return f"{size_bytes / (1024 * 1024):.{precision}f} MB"
