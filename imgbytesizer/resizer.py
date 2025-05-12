"""
Core image resizing functionality.
"""

import os
import io
import time
import logging
from typing import Optional, Tuple, Union
from pathlib import Path
from PIL import Image, ImageFile

from .formatter import (
    print_progress_bar,
    print_result,
    print_processing_step,
    print_comparison_table,
    format_filesize,
)
from .logger import Colors
from .utils import get_file_size_bytes, get_output_format, get_output_path

# Allow loading truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Get logger
logger = logging.getLogger("imgbytesizer")


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
    start_time = time.time()

    # Load the image and get original info
    print_processing_step(
        0, f"Opening {Colors.YELLOW}{os.path.basename(str(image_path))}{Colors.ENDC}"
    )

    try:
        img = Image.open(image_path)
        img.load()  # Ensure image is fully loaded
    except Exception as e:
        logger.error(f"Could not open image: {e}")
        raise

    orig_width, orig_height = img.size

    # Normalize format names and determine output path
    pil_format = get_output_format(img.format or "JPEG", format_name)
    output_path = get_output_path(image_path, output_path, pil_format)

    # Print image information if not in quiet mode
    if not quiet:
        print_result("File", os.path.basename(str(image_path)))
        print_result("Format", pil_format)
        print_result("Dimensions", f"{orig_width} × {orig_height} pixels")

        orig_size = os.path.getsize(image_path)
        print_result("Size", format_filesize(orig_size))
        print_result("Target size", format_filesize(target_size_bytes))
    else:
        # Even in quiet mode, we need the original size
        orig_size = os.path.getsize(image_path)

    # Check if resizing is needed
    if orig_size <= target_size_bytes:
        if not quiet:
            print(
                f"{Colors.GREEN}✓ Original image is already smaller than target size{Colors.ENDC}"
            )

        # If format conversion is needed
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

    # Try quality adjustment first for formats that support it
    result = None

    if pil_format in ["JPEG", "WEBP"]:
        result = _try_quality_adjustment(
            img, pil_format, target_size_bytes, output_path, quiet
        )

    # If quality adjustment didn't work, try resizing
    if result is None:
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

    # Fine-tuning to match exact target size if needed
    if exact_size and os.path.getsize(output_path) < target_size_bytes:
        _adjust_to_exact_size(output_path, target_size_bytes, quiet)

    # Final report if not in quiet mode
    if not quiet:
        final_img = Image.open(output_path)
        final_width, final_height = final_img.size
        final_size = os.path.getsize(output_path)

        print_comparison_table(
            orig_size,
            (orig_width, orig_height),
            final_size,
            (final_width, final_height),
            target_size_bytes,
        )

        elapsed = time.time() - start_time
        print_result("Time taken", f"{elapsed:.2f} seconds")
        print_result(
            "Output file",
            f"{Colors.UNDERLINE}{os.path.basename(output_path)}{Colors.ENDC}",
        )

    return output_path


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

    low, high = 1, 95
    best_quality = None
    best_size = None
    best_buffer = None
    iteration = 0
    max_iterations = 10  # Limit iterations for binary search

    # Binary search for best quality
    while low <= high and iteration < max_iterations:
        iteration += 1
        mid = (low + high) // 2
        size, buffer = get_file_size_bytes(img, pil_format, mid)

        if not quiet:
            print_progress_bar(
                iteration,
                max_iterations,
                prefix=f"Testing quality {mid:2d}",
                suffix=f"Size: {format_filesize(size)}",
            )

        if size <= target_size_bytes and (best_size is None or size > best_size):
            best_quality = mid
            best_size = size
            best_buffer = buffer

        if size > target_size_bytes:
            high = mid - 1
        else:
            low = mid + 1

        # Add small delay for visual effect in progress bar if not in quiet mode
        if not quiet:
            time.sleep(0.01)

    if best_size is not None and best_buffer is not None:
        if not quiet:
            print(
                f"\n{Colors.GREEN}✓ Found optimal quality: {best_quality} "
                f"(size: {format_filesize(best_size)}){Colors.ENDC}"
            )

        # Write the buffer to file
        with open(output_path, "wb") as f:
            f.write(best_buffer.getvalue())

        return output_path

    return None


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

    low_scale = 0.01
    high_scale = 1.0
    best_size = None
    best_buffer = None
    iterations = 0
    max_iterations = 10  # Limit iterations for binary search

    while high_scale - low_scale > 0.01 and iterations < max_iterations:
        iterations += 1
        mid_scale = (low_scale + high_scale) / 2
        new_width = int(orig_width * mid_scale)
        new_height = int(orig_height * mid_scale)

        # Apply minimum dimension constraint if specified
        if min_dimension is not None:
            if new_width < min_dimension or new_height < min_dimension:
                scale_w = min_dimension / new_width if new_width < min_dimension else 1
                scale_h = (
                    min_dimension / new_height if new_height < min_dimension else 1
                )
                scale = max(scale_w, scale_h)
                new_width = max(min_dimension, int(new_width * scale))
                new_height = max(min_dimension, int(new_height * scale))

        if not quiet:
            print_processing_step(
                iterations, f"Trying scale {mid_scale:.2f} ({new_width}×{new_height})"
            )

        # Use LANCZOS for best quality
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Try to find best quality for this size
        size, buffer = _find_best_quality(
            resized_img, pil_format, target_size_bytes, quiet
        )

        if size <= target_size_bytes and (best_size is None or size > best_size):
            best_size = size
            best_buffer = buffer

        if size > target_size_bytes:
            high_scale = mid_scale
        else:
            low_scale = mid_scale

        # Add small delay for visual effect in progress bar if not in quiet mode
        if not quiet:
            time.sleep(0.01)

    if best_buffer is None:
        raise ValueError("Could not find suitable size and quality combination")

    # Write the best result to file
    with open(output_path, "wb") as f:
        f.write(best_buffer.getvalue())

    if not quiet:
        if best_size is not None:
            found_size = format_filesize(best_size)
        else:
            found_size = "Unknown"

        print(f"\n{Colors.GREEN}✓ Found optimal size: {found_size}{Colors.ENDC}")

    return output_path


def _find_best_quality(
    img: Image.Image, pil_format: str, target_size_bytes: int, quiet: bool = False
) -> Tuple[int, io.BytesIO]:
    """Find the best quality setting for a given image size."""
    low, high = 1, 95
    best_size = None
    best_buffer = None
    iteration = 0
    max_iterations = 10  # Limit iterations for binary search

    while low <= high and iteration < max_iterations:
        iteration += 1
        mid = (low + high) // 2
        size, buffer = get_file_size_bytes(img, pil_format, mid)

        if not quiet:
            print_progress_bar(
                iteration,
                max_iterations,
                prefix=f"Testing quality {mid:2d}",
                suffix=f"Size: {format_filesize(size)}",
            )

        if size <= target_size_bytes and (best_size is None or size > best_size):
            best_size = size
            best_buffer = buffer

        if size > target_size_bytes:
            high = mid - 1
        else:
            low = mid + 1

        # Add small delay for visual effect in progress bar if not in quiet mode
        if not quiet:
            time.sleep(0.01)

    if best_buffer is None or best_size is None:
        raise ValueError("Could not find suitable quality setting")

    return best_size, best_buffer


def _adjust_to_exact_size(
    output_path: str, target_size_bytes: int, quiet: bool = False
) -> None:
    """Adjust the image to match the exact target size by adding padding bytes to the file."""
    if not quiet:
        print("Adjusting to exact target size...")

    # Read the current image
    current_size = os.path.getsize(output_path)

    # Calculate padding needed
    padding_needed = max(0, target_size_bytes - current_size)
    if padding_needed <= 0:
        return

    # Add padding by appending to the file
    with open(output_path, "ab") as f:
        f.write(b"\x00" * padding_needed)

    if not quiet:
        print(
            f"{Colors.GREEN}✓ Adjusted to exact size: "
            f"{format_filesize(target_size_bytes)}{Colors.ENDC}"
        )
