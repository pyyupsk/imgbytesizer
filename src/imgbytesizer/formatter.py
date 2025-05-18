"""
Terminal formatting utilities for imgbytesizer.
"""

from typing import Union


def format_filesize(size_bytes: Union[int, float, None]) -> str:
  """Format file size in bytes to human-readable string."""
  if size_bytes is None:
    return "N/A"
  size: float = float(size_bytes)
  for unit in ["B", "KB", "MB", "GB"]:
    if size < 1024:
      return f"{size:.1f}{unit}"
    size /= 1024
  return f"{size:.1f}TB"
