"""
Core image resizing functionality.
"""

import os
import io
import time
import logging
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
    image_path,
    target_size_bytes,
    output_path=None,
    format_name=None,
    min_dimension=None,
    exact_size=True,
    quiet=False,
):
    """Resize an image to match a target file size in bytes."""
    start_time = time.time()

    # Load the image and get original info
    print_processing_step(
        0, f"Opening {Colors.YELLOW}{os.path.basename(image_path)}{Colors.ENDC}"
    )

    try:
        img = Image.open(image_path)
        img.load()  # Ensure image is fully loaded
    except Exception as e:
        logger.error(f"Could not open image: {e}")
        raise

    orig_width, orig_height = img.size
    aspect_ratio = orig_width / orig_height

    # Normalize format names and determine output path
    pil_format = get_output_format(img.format, format_name)
    output_path = get_output_path(image_path, output_path, pil_format)

    # Print image information if not in quiet mode
    if not quiet:
        print_result("File", os.path.basename(image_path))
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
            aspect_ratio,
            quiet,
        )

    # Fine-tuning to match exact target size if needed
    if exact_size and os.path.getsize(output_path) < target_size_bytes:
        _adjust_to_exact_size(output_path, pil_format, target_size_bytes, quiet)

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
    img, pil_format, target_size_bytes, output_path, quiet=False
):
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

    if best_size is not None:
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
    img,
    pil_format,
    target_size_bytes,
    output_path,
    orig_width,
    orig_height,
    min_dimension,
    aspect_ratio,
    quiet=False,
):
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
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        # For quality-supporting formats, do a nested binary search for quality
        if pil_format in ["JPEG", "WEBP"]:
            quality_result = _find_best_quality(
                resized_img, pil_format, target_size_bytes, quiet
            )

            if quality_result:
                size, buffer = quality_result
            else:
                size, buffer = get_file_size_bytes(resized_img, pil_format, 1)
        else:
            size, buffer = get_file_size_bytes(resized_img, pil_format)

        if not quiet:
            result_status = "✓" if size <= target_size_bytes else "✗"
            result_color = Colors.GREEN if size <= target_size_bytes else Colors.RED
            print(
                f"  {result_color}{result_status} Result: {format_filesize(size)}{Colors.ENDC}"
            )

        if size <= target_size_bytes and (best_size is None or size > best_size):
            best_size = size
            best_buffer = buffer

        if size > target_size_bytes:
            high_scale = mid_scale
        else:
            low_scale = mid_scale

    # If no suitable size was found, create smallest possible image
    if best_buffer is None:
        if not quiet:
            print(
                f"\n{Colors.YELLOW}⚠ Could not find optimal size. "
                f"Creating smallest possible image...{Colors.ENDC}"
            )

        if min_dimension:
            if orig_width > orig_height:
                new_width = int(min_dimension * aspect_ratio)
                new_height = min_dimension
            else:
                new_width = min_dimension
                new_height = int(min_dimension / aspect_ratio)
        else:
            new_width = max(1, int(orig_width * 0.01))
            new_height = max(1, int(orig_height * 0.01))

        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        quality = 1 if pil_format in ["JPEG", "WEBP"] else None
        best_size, best_buffer = get_file_size_bytes(resized_img, pil_format, quality)

        if not quiet:
            print(
                f"  Created {new_width}×{new_height} image with size {format_filesize(best_size)}"
            )

    # Save the best result
    with open(output_path, "wb") as f:
        f.write(best_buffer.getvalue())

    return output_path


def _find_best_quality(img, pil_format, target_size_bytes, quiet=False):
    """Find the best quality for the given image to match the target size."""
    quality_low, quality_high = 1, 95
    best_q = None
    best_q_size = None
    best_q_buffer = None
    q_iterations = 0

    if not quiet:
        print(f"  {Colors.CYAN}Finding optimal quality...{Colors.ENDC}")

    while quality_low <= quality_high and q_iterations < 8:  # Limit search
        q_iterations += 1
        q_mid = (quality_low + quality_high) // 2
        q_size, q_buffer = get_file_size_bytes(img, pil_format, q_mid)

        if not quiet:
            result_indicator = " "
            if q_size <= target_size_bytes:
                result_indicator = f"{Colors.GREEN}✓{Colors.ENDC}"
            else:
                result_indicator = f"{Colors.RED}✗{Colors.ENDC}"

            print(
                f"    {result_indicator} Quality {q_mid:2d}: {format_filesize(q_size)}"
            )

        if q_size <= target_size_bytes:
            if best_q_size is None or q_size > best_q_size:
                best_q = q_mid
                best_q_size = q_size
                best_q_buffer = q_buffer
            quality_low = q_mid + 1
        else:
            quality_high = q_mid - 1

        # Small delay for visual effect
        if not quiet:
            time.sleep(0.01)

    if best_q_size is not None:
        if not quiet:
            print(f"    {Colors.GREEN}→ Best quality: {best_q}{Colors.ENDC}")
        return best_q_size, best_q_buffer
    else:
        if not quiet:
            print(f"    {Colors.YELLOW}→ Using minimum quality: 1{Colors.ENDC}")
        return None


def _adjust_to_exact_size(output_path, pil_format, target_size_bytes, quiet=False):
    """Adjust file to exactly match the target size."""
    final_img = Image.open(output_path)
    final_size = os.path.getsize(output_path)

    if not quiet:
        print("Adjusting to exact target size...")

    # For JPEG/WEBP, try to find a better quality setting first
    if pil_format in ["JPEG", "WEBP"] and abs(final_size - target_size_bytes) > 100:
        if not quiet:
            print("Optimizing quality for exact size match...")

        best_quality = None
        best_size_diff = abs(final_size - target_size_bytes)

        # Test fewer qualities for speed
        quality_range = range(1, 101, 5)

        for i, quality in enumerate(quality_range):
            if not quiet:
                print_progress_bar(
                    i + 1,
                    len(quality_range),
                    prefix=f"Testing quality {quality:3d}",
                    suffix="",
                )

            test_buffer = io.BytesIO()
            final_img.save(test_buffer, format=pil_format, quality=quality)
            test_size = test_buffer.tell()
            size_diff = abs(test_size - target_size_bytes)

            if size_diff < best_size_diff:
                best_quality = quality
                best_size_diff = size_diff

            if not quiet:
                time.sleep(0.01)  # Visual delay

        if best_quality is not None:
            final_img.save(output_path, format=pil_format, quality=best_quality)
            final_size = os.path.getsize(output_path)

            if not quiet:
                print(
                    f"\n{Colors.GREEN}✓ Quality adjusted to {best_quality}: "
                    f"{format_filesize(final_size)}{Colors.ENDC}"
                )

    # If we still need to pad the file
    if final_size < target_size_bytes:
        bytes_needed = target_size_bytes - final_size

        if not quiet:
            print(f"Adding {format_filesize(bytes_needed)} padding...")

        # Different padding strategies based on format
        if pil_format == "JPEG":
            comment = b"X" * bytes_needed
            temp_buffer = io.BytesIO()

            # Using a more controlled approach to adding comments
            try:
                # Try with a smaller comment first to avoid excessive bloat
                safe_comment_size = min(
                    bytes_needed, 65000
                )  # JPEG comments have size limits
                comment = b"X" * safe_comment_size

                final_img.save(
                    temp_buffer,
                    format="JPEG",
                    quality=95,
                    comment=comment.decode("latin1", errors="replace"),
                )

                # Check if we need multiple passes to reach the target size
                padded_size = temp_buffer.tell()

                if padded_size > target_size_bytes:
                    # If we overshot with the comment,
                    # try binary search to find optimal comment size
                    low, high = 0, safe_comment_size
                    while low < high:
                        mid = (low + high) // 2
                        comment = b"X" * mid
                        temp_buffer = io.BytesIO()
                        final_img.save(
                            temp_buffer,
                            format="JPEG",
                            quality=95,
                            comment=comment.decode("latin1", errors="replace"),
                        )
                        current_size = temp_buffer.tell()

                        if current_size > target_size_bytes:
                            high = mid
                        elif current_size < target_size_bytes:
                            low = mid + 1
                        else:
                            break  # Perfect size found

                    # Use the best approximation
                    comment = b"X" * low
                    temp_buffer = io.BytesIO()
                    final_img.save(
                        temp_buffer,
                        format="JPEG",
                        quality=95,
                        comment=comment.decode("latin1", errors="replace"),
                    )

                # Write the buffer to the file
                with open(output_path, "wb") as f:
                    f.write(temp_buffer.getvalue())

                # If we're still under the target size, pad with zeros
                final_size = os.path.getsize(output_path)
                if final_size < target_size_bytes:
                    with open(output_path, "ab") as f:
                        remaining_bytes = target_size_bytes - final_size
                        f.write(b"\0" * remaining_bytes)

            except Exception:
                # Fallback to simple padding if comment approach fails
                with open(output_path, "ab") as f:
                    f.write(b"\0" * bytes_needed)
        else:
            # For non-JPEG formats, append bytes to the end of the file
            with open(output_path, "ab") as f:
                f.write(b"\0" * bytes_needed)

        final_size = os.path.getsize(output_path)
        if not quiet:
            print(f"{Colors.GREEN}✓ File padded to exact size{Colors.ENDC}")

    elif final_size > target_size_bytes:
        # Handle the case where the file is too large
        if not quiet:
            print(
                f"Warning: File is {format_filesize(final_size - target_size_bytes)} "
                f"larger than target size."
            )

        # For JPEG/WEBP, try to find a better quality setting using binary search
        if pil_format in ["JPEG", "WEBP"]:
            low, high = 1, 95  # Start with quality range
            best_quality = None

            while low <= high:
                mid = (low + high) // 2
                temp_buffer = io.BytesIO()
                final_img.save(temp_buffer, format=pil_format, quality=mid)
                current_size = temp_buffer.tell()

                if current_size > target_size_bytes:
                    high = mid - 1
                else:
                    best_quality = mid
                    low = mid + 1

            if best_quality:
                final_img.save(output_path, format=pil_format, quality=best_quality)
                final_size = os.path.getsize(output_path)

                # If we're still under target, pad with zeros
                if final_size < target_size_bytes:
                    with open(output_path, "ab") as f:
                        remaining_bytes = target_size_bytes - final_size
                        f.write(b"\0" * remaining_bytes)

                if not quiet:
                    print(
                        f"{Colors.GREEN}✓ Quality adjusted to {best_quality}, size: "
                        f"{format_filesize(os.path.getsize(output_path))}{Colors.ENDC}"
                    )

    # Verify final size
    final_size = os.path.getsize(output_path)
    if abs(final_size - target_size_bytes) > 50:  # Allow small margin of error
        if not quiet:
            print(
                f"{Colors.YELLOW}Warning: Final size {format_filesize(final_size)} differs from "
                f"target {format_filesize(target_size_bytes)}{Colors.ENDC}"
            )

    return output_path
