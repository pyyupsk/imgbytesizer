"""
Core image resizing functionality.
"""

import io
import logging
import os
import time
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image, ImageFile

from .formatter import format_filesize
from .logger import (
    Colors, print_comparison_table, print_processing_step, print_progress_bar, print_result
)
from .utils import get_file_size_bytes, get_output_format, get_output_path

# Allow loading truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Get logger
logger: logging.Logger = logging.getLogger("imgbytesizer")


def _setup_image(image_path: Union[str, Path],
                 quiet: bool = False) -> Tuple[Image.Image, int, int, int]:
  """Load image and get original info."""
  print_processing_step(
      0, f"Opening {Colors.YELLOW}{os.path.basename(str(image_path))}{Colors.ENDC}"
  )

  try:
    img: Image.Image = Image.open(image_path)
    img.load()  # Ensure image is fully loaded
  except Exception as e:
    logger.error(f"Could not open image: {e}")
    raise

  orig_width: int
  orig_height: int
  orig_width, orig_height = img.size
  orig_size: int = os.path.getsize(image_path)

  if not quiet:
    print_result("File", os.path.basename(str(image_path)))
    print_result("Dimensions", f"{orig_width} × {orig_height} pixels")
    print_result("Size", format_filesize(orig_size))

  return img, orig_width, orig_height, orig_size


def _handle_format_conversion(
    img: Image.Image,
    image_path: str,
    output_path: str,
    format_name: Optional[str],
    quiet: bool = False
) -> str:
  """Handle format conversion if needed."""
  if format_name and format_name.upper() != img.format:
    img.save(output_path)
    if not quiet:
      print_result("Status", "Converted format only", "good")
      print_result("Output", os.path.basename(output_path))
  else:
    # No processing needed, just copy
    from shutil import copy2
    copy2(image_path, output_path)
    if not quiet:
      print_result("Status", "No processing needed", "good")
      print_result("Output", os.path.basename(output_path))
  return output_path


def _select_resizing_strategy(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    output_path: str,
    orig_width: int,
    orig_height: int,
    min_dimension: Optional[int],
    quiet: bool = False
) -> str:
  """Select and execute appropriate resizing strategy."""
  if pil_format in ["JPEG", "WEBP"]:
    # First, try quality adjustment with original dimensions
    result: Optional[str] = _try_quality_adjustment(
        img, pil_format, target_size_bytes, output_path, quiet
    )

    # If quality adjustment alone doesn't work, try combined approach
    if result is None or os.path.getsize(result) < target_size_bytes * 0.9:
      result = _try_combined_approach(
          img,
          pil_format,
          target_size_bytes,
          output_path,
          orig_width,
          orig_height,
          min_dimension,
          quiet,
      )
  else:
    # For formats without quality adjustment, just try resizing
    result = _try_resizing(
        img,
        pil_format,
        target_size_bytes,
        output_path,
        orig_width,
        orig_height,
        min_dimension,
        quiet,
    )
  return result


def _adjust_final_size(
    output_path: str,
    target_size_bytes: int,
    pil_format: str,
    exact_size: bool,
    quiet: bool = False
) -> None:
  """Adjust final size to match target if needed."""
  if not exact_size or not os.path.exists(output_path):
    return

  current_size: int = os.path.getsize(output_path)
  if current_size < target_size_bytes:
    _adjust_to_exact_size(output_path, target_size_bytes, quiet)
  elif current_size > target_size_bytes and pil_format in ["JPEG", "WEBP"]:
    if not quiet:
      print("File is larger than target, adjusting quality once more...")
    _final_quality_adjustment(output_path, pil_format, target_size_bytes, quiet)


def resize_to_target_filesize(
    image_path: Union[str, Path],
    target_size_bytes: int,
    output_path: Optional[str] = None,
    format_name: Optional[str] = None,
    min_dimension: Optional[int] = None,
    exact_size: bool = True,
    quiet: bool = False,
) -> str:
  """Resize an image to match a target file size in bytes."""
  start_time: float = time.time()

  # Load image and get original info
  img, orig_width, orig_height, orig_size = _setup_image(image_path, quiet)

  # Normalize format names and determine output path
  pil_format: str = get_output_format(img.format or "JPEG", format_name)
  output_path = get_output_path(image_path, output_path, pil_format)

  if not quiet:
    print_result("Format", pil_format)
    print_result("Target size", format_filesize(target_size_bytes))

  # Check if resizing is needed
  if orig_size <= target_size_bytes:
    if not quiet:
      print(f"{Colors.GREEN}✓ Original image is already smaller than target size{Colors.ENDC}")
    return _handle_format_conversion(img, str(image_path), output_path, format_name, quiet)

  # Select and execute resizing strategy
  result = _select_resizing_strategy(
      img, pil_format, target_size_bytes, output_path, orig_width, orig_height, min_dimension, quiet
  )

  # Adjust final size if needed
  _adjust_final_size(result, target_size_bytes, pil_format, exact_size, quiet)

  # Final report if not in quiet mode
  if not quiet:
    final_img: Image.Image = Image.open(result)
    final_width: int
    final_height: int
    final_width, final_height = final_img.size
    final_size: int = os.path.getsize(result)

    print_comparison_table(
        orig_size,
        (orig_width, orig_height),
        final_size,
        (final_width, final_height),
        target_size_bytes,
    )

    elapsed: float = time.time() - start_time
    print_result("Time taken", f"{elapsed:.2f} seconds")
    print_result(
        "Output file",
        f"{Colors.UNDERLINE}{os.path.basename(result)}{Colors.ENDC}",
    )

  return result


def _binary_search_quality(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    max_iterations: int,
    quiet: bool = False
) -> Tuple[Optional[int], Optional[int], Optional[io.BytesIO]]:
  """Binary search for best quality setting."""
  low: int = 1
  high: int = 100
  best_quality: Optional[int] = None
  best_size: Optional[int] = None
  best_buffer: Optional[io.BytesIO] = None
  iteration: int = 0

  while low <= high and iteration < max_iterations:
    iteration += 1
    mid: int = (low + high) // 2
    size, buffer = get_file_size_bytes(img, pil_format, mid)

    if not quiet:
      print_progress_bar(
          iteration,
          max_iterations,
          prefix=f"Testing quality {mid:2d}",
          suffix=f"Size: {format_filesize(size)}",
      )

    if size <= target_size_bytes:
      if best_size is None or size > best_size:
        best_quality = mid
        best_size = size
        best_buffer = buffer
      low = mid + 1
    else:
      high = mid - 1

    if not quiet:
      time.sleep(0.01)

  return best_quality, best_size, best_buffer


def _try_quality_adjustment(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    output_path: str,
    quiet: bool = False,
) -> Optional[str]:
  """Try to reach target size by adjusting quality only."""
  if not quiet:
    print("Trying quality adjustment without resizing...")

  best_quality, best_size, best_buffer = _binary_search_quality(
      img, pil_format, target_size_bytes, 12, quiet
  )

  if best_size is not None and best_buffer is not None:
    if not quiet:
      print(
          f"\n{Colors.GREEN}✓ Found optimal quality: {best_quality} "
          f"(size: {format_filesize(best_size)}){Colors.ENDC}"
      )

    with open(output_path, "wb") as f:
      f.write(best_buffer.getvalue())

    return output_path

  return None


def _try_scale_with_quality(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    scale: float,
    orig_width: int,
    orig_height: int,
    min_dimension: Optional[int],
    quiet: bool = False
) -> Tuple[Optional[int], Optional[io.BytesIO], Optional[float]]:
  """Try a specific scale factor with quality adjustment."""
  new_width: int = int(orig_width * scale)
  new_height: int = int(orig_height * scale)

  if min_dimension is not None:
    if new_width < min_dimension or new_height < min_dimension:
      scale_w: float = (min_dimension / new_width if new_width < min_dimension else 1)
      scale_h: float = (min_dimension / new_height if new_height < min_dimension else 1)
      scale = max(scale_w, scale_h)
      new_width = int(orig_width * scale)
      new_height = int(orig_height * scale)

  if not quiet:
    print(f"Trying scale factor {scale:.2f} ({new_width}×{new_height})...")

  if new_width > 10000 or new_height > 10000:
    return None, None, None

  resized_img: Image.Image = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
  size, buffer = _find_best_quality(resized_img, pil_format, target_size_bytes, quiet)

  return size, buffer, scale


def _get_scale_factors(target_size_bytes: int) -> list[float]:
  """Get appropriate scale factors based on target size."""
  return [0.1, 0.2, 0.3, 0.4, 0.5] if target_size_bytes < 5 * 1024 else [1.0, 1.25, 1.5, 2.0, 3.0]


def _try_combined_approach(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    output_path: str,
    orig_width: int,
    orig_height: int,
    min_dimension: Optional[int],
    quiet: bool = False,
) -> str:
  """Try combined scaling and quality approach."""
  if not quiet:
    print("Trying combined scaling and quality approach...")

  best_size: Optional[int] = None
  best_buffer: Optional[io.BytesIO] = None
  best_scale: Optional[float] = None

  for scale in _get_scale_factors(target_size_bytes):
    size, buffer, scale = _try_scale_with_quality(
        img, pil_format, target_size_bytes, scale, orig_width, orig_height, min_dimension, quiet
    )

    if size is not None and buffer is not None:
      if best_size is None or abs(size - target_size_bytes) < abs(best_size - target_size_bytes):
        best_size = size
        best_buffer = buffer
        best_scale = scale

      if size >= target_size_bytes * 0.95:
        break

  if best_buffer is None:
    return _try_minimum_size(img, pil_format, output_path, min_dimension, quiet)

  with open(output_path, "wb") as f:
    f.write(best_buffer.getvalue())

  if not quiet:
    print(
        f"\n{Colors.GREEN}✓ Found optimal size: {format_filesize(best_size)} with scale "
        f"{best_scale:.2f}{Colors.ENDC}"
    )

  return output_path


def _apply_min_dimension_constraint(new_width: int, new_height: int,
                                    min_dimension: Optional[int]) -> Tuple[int, int, float]:
  """Apply minimum dimension constraint and return new dimensions and scale."""
  if min_dimension is None:
    return new_width, new_height, 1.0

  if new_width < min_dimension or new_height < min_dimension:
    scale_w: float = (min_dimension / new_width if new_width < min_dimension else 1)
    scale_h: float = (min_dimension / new_height if new_height < min_dimension else 1)
    scale = max(scale_w, scale_h)
    new_width = max(min_dimension, int(new_width * scale))
    new_height = max(min_dimension, int(new_height * scale))
    return new_width, new_height, scale

  return new_width, new_height, 1.0


def _binary_search_scale(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    orig_width: int,
    orig_height: int,
    min_dimension: Optional[int],
    quiet: bool = False
) -> Tuple[Optional[int], Optional[io.BytesIO], Optional[float]]:
  """Binary search for the best scale factor."""
  low_scale: float = 0.01
  high_scale: float = 1.0
  best_size: Optional[int] = None
  best_buffer: Optional[io.BytesIO] = None
  best_scale: Optional[float] = None
  iterations: int = 0
  max_iterations: int = 12

  while high_scale - low_scale > 0.005 and iterations < max_iterations:
    iterations += 1
    mid_scale: float = (low_scale + high_scale) / 2
    new_width: int = max(1, int(orig_width * mid_scale))
    new_height: int = max(1, int(orig_height * mid_scale))

    new_width, new_height, _ = _apply_min_dimension_constraint(new_width, new_height, min_dimension)

    if not quiet:
      print_processing_step(iterations, f"Trying scale {mid_scale:.2f} ({new_width}×{new_height})")

    resized_img: Image.Image = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    size, buffer = _find_best_quality(resized_img, pil_format, target_size_bytes, quiet)

    if size <= target_size_bytes:
      if best_size is None or size > best_size:
        best_size = size
        best_buffer = buffer
        best_scale = mid_scale
      low_scale = mid_scale
    else:
      high_scale = mid_scale

    if not quiet:
      time.sleep(0.01)

  return best_size, best_buffer, best_scale


def _try_minimum_size(
    img: Image.Image,
    pil_format: str,
    output_path: str,
    min_dimension: Optional[int],
    quiet: bool = False
) -> str:
  """Try the smallest possible size with lowest quality as last resort."""
  smallest_width: int = 1 if min_dimension is None else min_dimension
  smallest_height: int = 1 if min_dimension is None else min_dimension
  tiny_img: Image.Image = img.resize((smallest_width, smallest_height), Image.Resampling.LANCZOS)

  _size, buffer = get_file_size_bytes(tiny_img, pil_format, 1)

  with open(output_path, "wb") as f:
    f.write(buffer.getvalue())

  if not quiet:
    print(
        f"\n{Colors.YELLOW}⚠ Could not reach target size. Using minimum size and quality."
        f"{Colors.ENDC}"
    )

  return output_path


def _try_resizing(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    output_path: str,
    orig_width: int,
    orig_height: int,
    min_dimension: Optional[int],
    quiet: bool = False,
) -> str:
  """Try to reach target size by resizing the image."""
  if not quiet:
    print("Performing size-based optimization...")

  best_size, best_buffer, best_scale = _binary_search_scale(
      img, pil_format, target_size_bytes, orig_width, orig_height, min_dimension, quiet
  )

  if best_buffer is None:
    return _try_minimum_size(img, pil_format, output_path, min_dimension, quiet)

  with open(output_path, "wb") as f:
    f.write(best_buffer.getvalue())

  if not quiet:
    found_size: str = format_filesize(best_size) if best_size is not None else "Unknown"
    print(
        f"\n{Colors.GREEN}✓ Found optimal size: {found_size} with scale "
        f"{best_scale:.2f}{Colors.ENDC}"
    )

  return output_path


def _find_best_quality(
    img: Image.Image,
    pil_format: str,
    target_size_bytes: int,
    quiet: bool = False
) -> Tuple[int, io.BytesIO]:
  """Find the best quality setting for a given image size."""
  low: int = 1
  high: int = 100  # Extended to 100 from 95
  best_size: Optional[int] = None
  best_buffer: Optional[io.BytesIO] = None
  iteration: int = 0
  max_iterations: int = 12  # Increased from 10

  while low <= high and iteration < max_iterations:
    iteration += 1
    mid: int = (low + high) // 2
    size: int
    buffer: io.BytesIO
    size, buffer = get_file_size_bytes(img, pil_format, mid)

    if not quiet:
      print_progress_bar(
          iteration,
          max_iterations,
          prefix=f"Testing quality {mid:2d}",
          suffix=f"Size: {format_filesize(size)}",
      )

    # Update best if this is closest to target without going over
    if size <= target_size_bytes:
      if best_size is None or size > best_size:
        best_size = size
        best_buffer = buffer
      low = mid + 1
    else:
      high = mid - 1

    # Add small delay for visual effect in progress bar if not in quiet mode
    if not quiet:
      time.sleep(0.01)

  if best_buffer is None:
    # If all qualities exceed target, use lowest quality
    size: int
    buffer: io.BytesIO
    size, buffer = get_file_size_bytes(img, pil_format, 1)
    return size, buffer

  if best_size is None:
    # Handle the case where best_size is None
    best_size = 0  # or some other default value

  return best_size, best_buffer


def _final_quality_adjustment(
    image_path: str, pil_format: str, target_size_bytes: int, quiet: bool = False
) -> None:
  """Make a final quality adjustment to get closer to target size."""
  try:
    img: Image.Image = Image.open(image_path)

    # Get current size
    current_size: int = os.path.getsize(image_path)

    if current_size <= target_size_bytes:
      return

    # Try to reduce quality to get closer to target
    low: int = 1
    high: int = 100
    best_buffer: Optional[io.BytesIO] = None

    for _ in range(8):  # Limit iterations for speed
      mid: int = (low + high) // 2
      size: int
      buffer: io.BytesIO
      size, buffer = get_file_size_bytes(img, pil_format, mid)

      if size <= target_size_bytes:
        best_buffer = buffer
        low = mid + 1
      else:
        high = mid - 1

    if best_buffer is not None:
      with open(image_path, "wb") as f:
        f.write(best_buffer.getvalue())
  except Exception as e:
    if not quiet:
      print(f"{Colors.YELLOW}⚠ Final quality adjustment failed: {e}{Colors.ENDC}")


def _adjust_to_exact_size(output_path: str, target_size_bytes: int, quiet: bool = False) -> None:
  """Adjust the image to match the exact target size by adding padding bytes to the file."""
  if not quiet:
    print("Adjusting to exact target size...")

  # Read the current image
  current_size: int = os.path.getsize(output_path)

  # Calculate padding needed
  padding_needed: int = max(0, target_size_bytes - current_size)
  if padding_needed <= 0:
    return

  # Add padding by appending to the file
  with open(output_path, "ab") as f:
    # For JPEG/WebP, add padding in the metadata section or as a comment
    # This is safer than just adding null bytes to the end
    if output_path.lower().endswith((".jpg", ".jpeg", ".webp")):
      # Add a unique marker followed by padding
      f.write(
          b"\xff\xfe" + bytes([padding_needed >> 8, padding_needed & 0xFF]) + b"\x00" *
          (padding_needed - 4)
      )
    else:
      # For other formats, just add null bytes
      f.write(b"\x00" * padding_needed)

  if not quiet:
    print(
        f"{Colors.GREEN}✓ Adjusted to exact size: "
        f"{format_filesize(target_size_bytes)}{Colors.ENDC}"
    )
