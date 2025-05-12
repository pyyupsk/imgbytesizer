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

    # For formats that support quality adjustment, try that first
    if pil_format in ["JPEG", "WEBP"]:
        # First, try quality adjustment with original dimensions
        result = _try_quality_adjustment(
            img, pil_format, target_size_bytes, output_path, quiet
        )

        # If quality adjustment alone doesn't work (image too small),
        # try combined approach with resizing
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

    # Fine-tuning to match exact target size if needed
    if exact_size and os.path.exists(output_path):
        current_size = os.path.getsize(output_path)
        if current_size < target_size_bytes:
            _adjust_to_exact_size(output_path, target_size_bytes, quiet)
        elif current_size > target_size_bytes and pil_format in ["JPEG", "WEBP"]:
            # If we somehow overshot, try one more quality adjustment
            if not quiet:
                print("File is larger than target, adjusting quality once more...")
            _final_quality_adjustment(output_path, pil_format, target_size_bytes, quiet)

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

    # Start with wider quality range (1-100 instead of 1-95)
    low, high = 1, 100
    best_quality = None
    best_size = None
    best_buffer = None
    iteration = 0
    max_iterations = 12  # Increased from 10 for more precision

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

        # Update best if this is closest to target without going over
        if size <= target_size_bytes:
            if best_size is None or size > best_size:
                best_quality = mid
                best_size = size
                best_buffer = buffer
            low = mid + 1  # Try higher quality
        else:
            high = mid - 1  # Try lower quality

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
    """Try a combined approach of slight upscaling and quality adjustment."""
    if not quiet:
        print("Trying combined scaling and quality approach...")

    # Try a series of scale factors, starting from original size and going up
    # This helps when the image is too small to reach the target size with quality alone
    scale_factors = [1.0, 1.25, 1.5, 2.0, 3.0]

    best_size = None
    best_buffer = None
    best_scale = None

    for scale in scale_factors:
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # Apply minimum dimension constraint if specified
        if min_dimension is not None:
            if new_width < min_dimension or new_height < min_dimension:
                scale_w = min_dimension / new_width if new_width < min_dimension else 1
                scale_h = (
                    min_dimension / new_height if new_height < min_dimension else 1
                )
                scale_adj = max(scale_w, scale_h)
                new_width = max(min_dimension, int(new_width * scale_adj))
                new_height = max(min_dimension, int(new_height * scale_adj))

        if not quiet:
            print(f"Trying scale factor {scale:.2f} ({new_width}×{new_height})...")

        # Skip if dimensions are unreasonably large
        if new_width > 10000 or new_height > 10000:
            continue

        # Use LANCZOS for best quality
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Try quality adjustment for this size
        low, high = 1, 100
        best_size_for_scale = None
        best_buffer_for_scale = None

        # Binary search for quality
        for _ in range(10):  # Limit iterations
            mid = (low + high) // 2
            size, buffer = get_file_size_bytes(resized_img, pil_format, mid)

            if not quiet:
                print_progress_bar(
                    _ + 1,
                    10,
                    prefix=f"Quality {mid:2d}",
                    suffix=f"Size: {format_filesize(size)}",
                )

            # Found a valid size
            if size <= target_size_bytes:
                if best_size_for_scale is None or size > best_size_for_scale:
                    best_size_for_scale = size
                    best_buffer_for_scale = buffer
                low = mid + 1
            else:
                high = mid - 1

        # Update overall best if this scale produced a better result
        if best_size_for_scale is not None:
            if best_size is None or abs(best_size_for_scale - target_size_bytes) < abs(
                best_size - target_size_bytes
            ):
                best_size = best_size_for_scale
                best_buffer = best_buffer_for_scale
                best_scale = scale

        # If we're within 95% of the target size, consider it good enough and stop
        if (
            best_size_for_scale is not None
            and best_size_for_scale >= target_size_bytes * 0.95
        ):
            break

    if best_buffer is None:
        # Fall back to resizing if combined approach failed
        return _try_resizing(
            img,
            pil_format,
            target_size_bytes,
            output_path,
            orig_width,
            orig_height,
            min_dimension,
            quiet,
        )

    # Write the best result to file
    with open(output_path, "wb") as f:
        f.write(best_buffer.getvalue())

    if not quiet:
        print(
            f"\n{Colors.GREEN}✓ Combined approach success: scale={best_scale:.2f}, "
            f"size={format_filesize(best_size)}{Colors.ENDC}"
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

    low_scale = 0.01
    high_scale = 1.0
    best_size = None
    best_buffer = None
    best_scale = None
    iterations = 0
    max_iterations = 12  # Limit iterations for binary search

    while high_scale - low_scale > 0.005 and iterations < max_iterations:
        iterations += 1
        mid_scale = (low_scale + high_scale) / 2
        new_width = max(1, int(orig_width * mid_scale))
        new_height = max(1, int(orig_height * mid_scale))

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

        # Update best if this is closest to target without going over
        if size <= target_size_bytes:
            if best_size is None or size > best_size:
                best_size = size
                best_buffer = buffer
                best_scale = mid_scale
            low_scale = mid_scale  # Try larger sizes
        else:
            high_scale = mid_scale  # Try smaller sizes

        # Add small delay for visual effect in progress bar if not in quiet mode
        if not quiet:
            time.sleep(0.01)

    if best_buffer is None:
        # Last resort: use the smallest possible size with lowest quality
        smallest_width = 1 if min_dimension is None else min_dimension
        smallest_height = 1 if min_dimension is None else min_dimension
        tiny_img = img.resize(
            (smallest_width, smallest_height), Image.Resampling.LANCZOS
        )

        min_quality = 1  # Lowest possible quality
        size, buffer = get_file_size_bytes(tiny_img, pil_format, min_quality)

        # Write this as our best attempt
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())

        if not quiet:
            print(
                f"\n{Colors.YELLOW}⚠ Could not reach target size. Using minimum size and quality."
                f"{Colors.ENDC}"
            )

        return output_path

    # Write the best result to file
    with open(output_path, "wb") as f:
        f.write(best_buffer.getvalue())

    if not quiet:
        if best_size is not None:
            found_size = format_filesize(best_size)
        else:
            found_size = "Unknown"

        print(
            f"\n{Colors.GREEN}✓ Found optimal size: {found_size} with scale "
            f"{best_scale:.2f}{Colors.ENDC}"
        )

    return output_path


def _find_best_quality(
    img: Image.Image, pil_format: str, target_size_bytes: int, quiet: bool = False
) -> Tuple[int, io.BytesIO]:
    """Find the best quality setting for a given image size."""
    low, high = 1, 100  # Extended to 100 from 95
    best_size = None
    best_buffer = None
    iteration = 0
    max_iterations = 12  # Increased from 10

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
        img = Image.open(image_path)

        # Get current size
        current_size = os.path.getsize(image_path)

        if current_size <= target_size_bytes:
            return

        # Try to reduce quality to get closer to target
        low, high = 1, 100
        best_buffer = None

        for _ in range(8):  # Limit iterations for speed
            mid = (low + high) // 2
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
        # For JPEG/WebP, add padding in the metadata section or as a comment
        # This is safer than just adding null bytes to the end
        if output_path.lower().endswith((".jpg", ".jpeg", ".webp")):
            # Add a unique marker followed by padding
            f.write(
                b"\xff\xfe"
                + bytes([padding_needed >> 8, padding_needed & 0xFF])
                + b"\x00" * (padding_needed - 4)
            )
        else:
            # For other formats, just add null bytes
            f.write(b"\x00" * padding_needed)

    if not quiet:
        print(
            f"{Colors.GREEN}✓ Adjusted to exact size: "
            f"{format_filesize(target_size_bytes)}{Colors.ENDC}"
        )
