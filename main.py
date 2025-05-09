import os
import sys
import argparse
import time
import io
import shutil

from PIL import Image
from tabulate import tabulate


# ANSI Color Codes for beautiful terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_terminal_width():
    """Get the width of the terminal."""
    try:
        columns = shutil.get_terminal_size().columns
        return max(80, columns)
    except Exception:
        return 80


def format_filesize(size_bytes):
    """Format file size in a human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024} KB"
    else:
        return f"{size_bytes/(1024*1024)} MB"


def print_progress_bar(progress, total, prefix='', suffix='', length=30):
    """Print a progress bar with percentage."""
    percent = min(100, int(100.0 * progress / total))
    filled_length = int(length * progress // total)
    bar = '█' * filled_length + '░' * (length - filled_length)
    print(f"\r{prefix} |{Colors.GREEN}{bar}{Colors.ENDC}| {percent}% {suffix}", end='\r')
    if progress == total:
        print()


def print_result(name, value, status=None):
    """Print a name-value pair with optional status color."""
    value_color = Colors.ENDC
    if status == 'good':
        value_color = Colors.GREEN
    elif status == 'warning':
        value_color = Colors.YELLOW
    elif status == 'bad':
        value_color = Colors.RED

    print(f"  {Colors.BOLD}{name}:{Colors.ENDC} {value_color}{value}{Colors.ENDC}")


def print_processing_step(step, description):
    """Print a processing step with a spinner."""
    spinner = ["◐", "◓", "◑", "◒"]
    print(f"{Colors.BLUE}{spinner[step % len(spinner)]}{Colors.ENDC} {description}")


def print_comparison_table(original_size, original_dimensions,
                           final_size, final_dimensions, target_size):

    orig_dim = f"{original_dimensions[0]}×{original_dimensions[1]}"
    new_dim = f"{final_dimensions[0]}×{final_dimensions[1]}"
    orig_size = format_filesize(original_size)
    new_size = format_filesize(final_size)
    target = format_filesize(target_size)
    diff = abs(final_size - target_size)
    diff_pct = (diff / target_size) * 100
    reduction = ((original_size - final_size) / original_size) * \
        100 if original_size > final_size else 0

    # Determine color based on how close to target
    if diff_pct < 1:
        diff_color = Colors.GREEN
    elif diff_pct < 5:
        diff_color = Colors.YELLOW
    else:
        diff_color = Colors.RED

    table = [
        [f"{Colors.BOLD}Dimensions{Colors.ENDC}", f"{Colors.CYAN}{orig_dim}{Colors.ENDC}",
            f"{Colors.GREEN}{new_dim}{Colors.ENDC}"],
        [f"{Colors.BOLD}Size{Colors.ENDC}", f"{Colors.CYAN}{orig_size}{Colors.ENDC}",
            f"{Colors.GREEN}{new_size}{Colors.ENDC}"],
        [f"{Colors.BOLD}Target Size{Colors.ENDC}", "", f"{Colors.BLUE}{target}{Colors.ENDC}"],
        [f"{Colors.BOLD}Difference{Colors.ENDC}", "",
            f"{diff_color}{format_filesize(diff)} ({diff_pct:.1f}%){Colors.ENDC}"],
        [f"{Colors.BOLD}Reduction{Colors.ENDC}", "",
            f"{Colors.CYAN}{reduction:.1f}% smaller{Colors.ENDC}"
            if reduction else f"{Colors.YELLOW}N/A{Colors.ENDC}"]
    ]

    print()
    print(
        tabulate(table, headers=[
            f"{Colors.UNDERLINE}Metric{Colors.ENDC}",
            f"{Colors.UNDERLINE}Original{Colors.ENDC}",
            f"{Colors.UNDERLINE}Processed{Colors.ENDC}"
        ], tablefmt="rounded_grid")
    )


def get_file_size_bytes(img, format, quality=None):
    """Get the file size in bytes for an image with the specified format and quality."""
    out_buffer = io.BytesIO()
    save_args = {'format': format}
    if quality is not None:
        if format == 'JPEG':
            save_args['quality'] = quality
        elif format == 'PNG':
            save_args['optimize'] = True
            save_args['compress_level'] = quality
        elif format == 'WEBP':
            save_args['quality'] = quality

    img.save(out_buffer, **save_args)
    return out_buffer.tell(), out_buffer


def resize_to_target_filesize(
    image_path, target_size_bytes, output_path=None,
    format=None, min_dimension=None, exact_size=True
):
    """Resize an image to match a target file size in bytes."""
    start_time = time.time()

    # Load the image and get original info
    print_processing_step(0, f"Opening {Colors.YELLOW}{os.path.basename(image_path)}{Colors.ENDC}")

    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}ERROR: Could not open image: {e}{Colors.ENDC}")
        return None

    orig_width, orig_height = img.size
    aspect_ratio = orig_width / orig_height

    # Determine format
    if format is None:
        format = img.format

    pil_format = format.upper() if format else img.format
    if pil_format == 'JPG':
        pil_format = 'JPEG'

    # Determine output path
    if output_path is None:
        base_name, _ = os.path.splitext(image_path)
        output_path = f"{base_name}_resized.{pil_format.lower()}"

    # Print image information
    print_result("File", os.path.basename(image_path))
    print_result("Format", pil_format)
    print_result("Dimensions", f"{orig_width} × {orig_height} pixels")

    orig_size, _ = get_file_size_bytes(img, pil_format)
    print_result("Size", format_filesize(orig_size))
    print_result("Target size", format_filesize(target_size_bytes))

    # Check if resizing is needed
    if orig_size <= target_size_bytes:

        print(f"{Colors.GREEN}✓ Original image is already smaller than target size{Colors.ENDC}")
        img.save(output_path)

        print_result("Status", "No resizing needed", "good")
        print_result("Output", os.path.basename(output_path))
        return output_path

    # Try quality adjustment first for formats that support it
    if pil_format in ['JPEG', 'WEBP']:

        print("Trying quality adjustment without resizing...")

        low, high = 1, 95
        best_quality = None
        best_size = None
        best_buffer = None
        iteration = 0
        total_iterations = min(10, high - low)  # Estimate iterations for progress bar

        while low <= high:
            iteration += 1
            mid = (low + high) // 2
            size, buffer = get_file_size_bytes(img, pil_format, mid)

            print_progress_bar(iteration, total_iterations,
                               prefix=f"Testing quality {mid:2d}",
                               suffix=f"Size: {format_filesize(size)}")

            if size <= target_size_bytes and (best_size is None or size > best_size):
                best_quality = mid
                best_size = size
                best_buffer = buffer

            if size > target_size_bytes:
                high = mid - 1
            else:
                low = mid + 1

            # Add small delay for visual effect in progress bar
            time.sleep(0.01)

        if best_size is not None:
            print(
                f"\n{Colors.GREEN}✓ Found optimal quality: {best_quality} "
                f"(size: {format_filesize(best_size)}){Colors.ENDC}"
            )
            with open(output_path, 'wb') as f:
                f.write(best_buffer.getvalue())

            # Final report
            final_img = Image.open(output_path)
            final_width, final_height = final_img.size
            final_size = os.path.getsize(output_path)

            print_comparison_table(orig_size, (orig_width, orig_height),
                                   final_size, (final_width, final_height),
                                   target_size_bytes)

            elapsed = time.time() - start_time
            print_result("Time taken", f"{elapsed:.2f} seconds")
            print_result(
                "Output file", f"{Colors.UNDERLINE}{os.path.basename(output_path)}{Colors.ENDC}")

            return output_path

    # If quality adjustment didn't work, try resizing
    print("Performing size-based optimization...")

    low_scale = 0.01
    high_scale = 1.0
    best_size = None
    best_buffer = None
    iterations = 0
    max_iterations = 10  # Limit iterations for binary search visualization

    while high_scale - low_scale > 0.01 and iterations < max_iterations:
        iterations += 1
        mid_scale = (low_scale + high_scale) / 2
        new_width = int(orig_width * mid_scale)
        new_height = int(orig_height * mid_scale)

        if min_dimension is not None:
            if new_width < min_dimension or new_height < min_dimension:
                scale_w = min_dimension / new_width if new_width < min_dimension else 1
                scale_h = min_dimension / new_height if new_height < min_dimension else 1
                scale = max(scale_w, scale_h)
                new_width = max(min_dimension, int(new_width * scale))
                new_height = max(min_dimension, int(new_height * scale))

        print_processing_step(
            iterations, f"Trying scale {mid_scale:.2f} ({new_width}×{new_height})")
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        if pil_format in ['JPEG', 'WEBP']:
            # For quality-supporting formats, do a nested binary search for quality
            quality_low, quality_high = 1, 95
            best_q = None
            best_q_size = None
            best_q_buffer = None
            q_iterations = 0

            print(f"  {Colors.CYAN}Finding optimal quality...{Colors.ENDC}")

            while quality_low <= quality_high and q_iterations < 8:  # Limit inner search as well
                q_iterations += 1
                q_mid = (quality_low + quality_high) // 2
                q_size, q_buffer = get_file_size_bytes(resized_img, pil_format, q_mid)

                result_indicator = " "
                if q_size <= target_size_bytes:
                    result_indicator = f"{Colors.GREEN}✓{Colors.ENDC}"
                    if best_q_size is None or q_size > best_q_size:
                        best_q = q_mid
                        best_q_size = q_size
                        best_q_buffer = q_buffer
                else:
                    result_indicator = f"{Colors.RED}✗{Colors.ENDC}"

                print(f"    {result_indicator} Quality {q_mid:2d}: {format_filesize(q_size)}")

                if q_size > target_size_bytes:
                    quality_high = q_mid - 1
                else:
                    quality_low = q_mid + 1

                time.sleep(0.01)  # Small delay for visual effect

            if best_q_size is not None:
                size, buffer = best_q_size, best_q_buffer
                print(f"    {Colors.GREEN}→ Best quality: {best_q}{Colors.ENDC}")
            else:
                size, buffer = get_file_size_bytes(resized_img, pil_format, 1)
                print(f"    {Colors.YELLOW}→ Using minimum quality: 1{Colors.ENDC}")
        else:
            size, buffer = get_file_size_bytes(resized_img, pil_format)

        result_status = "✓" if size <= target_size_bytes else "✗"
        result_color = Colors.GREEN if size <= target_size_bytes else Colors.RED
        print(f"  {result_color}{result_status} Result: {format_filesize(size)}{Colors.ENDC}")

        if size <= target_size_bytes and (best_size is None or size > best_size):
            best_size = size
            best_buffer = buffer

        if size > target_size_bytes:
            high_scale = mid_scale
        else:
            low_scale = mid_scale

    # If no suitable size was found
    if best_buffer is None:
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
        quality = 1 if pil_format in ['JPEG', 'WEBP'] else None
        best_size, best_buffer = get_file_size_bytes(resized_img, pil_format, quality)

        print(f"  Created {new_width}×{new_height} image with size {format_filesize(best_size)}")

    # Save the best result
    with open(output_path, 'wb') as f:
        f.write(best_buffer.getvalue())

    final_img = Image.open(output_path)
    final_width, final_height = final_img.size
    final_size = os.path.getsize(output_path)

    # Fine-tuning to match exact target size if needed
    if exact_size and final_size < target_size_bytes:

        print("Adjusting to exact target size...")

        if pil_format in ['JPEG', 'WEBP'] and abs(final_size - target_size_bytes) > 100:
            print("Optimizing quality for exact size match...")
            best_quality = None
            best_size_diff = abs(final_size - target_size_bytes)

            quality_range = range(1, 101, 5)  # Test fewer qualities for speed
            for i, quality in enumerate(quality_range):
                print_progress_bar(
                    i+1, len(quality_range),
                    prefix=f"Testing quality {quality:3d}",
                    suffix=""
                )

                test_buffer = io.BytesIO()
                final_img.save(test_buffer, format=pil_format, quality=quality)
                test_size = test_buffer.tell()
                size_diff = abs(test_size - target_size_bytes)

                if size_diff < best_size_diff:
                    best_quality = quality
                    best_size_diff = size_diff

                time.sleep(0.01)  # Visual delay

            if best_quality is not None:
                final_img.save(output_path, format=pil_format, quality=best_quality)
                final_size = os.path.getsize(output_path)
                print(
                    f"\n{Colors.GREEN}✓ Quality adjusted to {best_quality}: "
                    f"{format_filesize(final_size)}{Colors.ENDC}"
                )

        # If we still need to pad the file
        if final_size < target_size_bytes:
            bytes_needed = target_size_bytes - final_size
            print(f"Adding {format_filesize(bytes_needed)} padding...")

            if pil_format == 'JPEG':
                comment = b'X' * bytes_needed
                temp_buffer = io.BytesIO()
                final_img.save(temp_buffer, format='JPEG', quality=95,
                               comment=comment.decode('latin1', errors='replace'))
                with open(output_path, 'wb') as f:
                    f.write(temp_buffer.getvalue())
            else:
                with open(output_path, 'ab') as f:
                    f.write(b'P' * bytes_needed)

            final_size = os.path.getsize(output_path)
            print(f"{Colors.GREEN}✓ File padded to exact size{Colors.ENDC}")

    # Final report
    print_comparison_table(orig_size, (orig_width, orig_height),
                           final_size, (final_width, final_height),
                           target_size_bytes)

    elapsed = time.time() - start_time
    print_result("Time taken", f"{elapsed:.2f} seconds")
    print_result("Output file", f"{Colors.UNDERLINE}{os.path.basename(output_path)}{Colors.ENDC}")

    return output_path


def parse_filesize(size_str):
    """Parse a file size string like '1MB' to bytes."""
    size_str = size_str.strip().upper()
    if size_str.endswith('KB'):
        return int(float(size_str[:-2]) * 1024)
    elif size_str.endswith('MB'):
        return int(float(size_str[:-2]) * 1024 * 1024)
    elif size_str.endswith('GB'):
        return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
    elif size_str.endswith('B'):
        return int(size_str[:-1])
    else:
        try:
            return int(size_str)
        except ValueError:
            raise ValueError("Invalid file size format. Use B, KB, MB, or GB suffix.")


def main():
    parser = argparse.ArgumentParser(
        description='Resize an image to match a target file size',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.jpg 500KB                   # Resize to 500 KB
  %(prog)s photo.png 2MB -o small_photo.png  # Resize to 2 MB with custom output
  %(prog)s image.jpg 100KB -f webp           # Resize and convert to WebP
  %(prog)s large.jpg 50KB --min-dimension 200  # Ensure min dimension is 200px
    """
    )

    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('target_size', help='Target file size (e.g., "1MB", "500KB")')
    parser.add_argument('-o', '--output', help='Output path (default: input_resized.ext)')
    parser.add_argument('-f', '--format', help='Output format (jpg, png, webp)')
    parser.add_argument('--min-dimension', type=int, help='Minimum width/height in pixels')
    parser.add_argument('--no-exact', action='store_true',
                        help='Do not pad file to get exact target size')

    # Handle no arguments case with nice help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    try:
        target_bytes = parse_filesize(args.target_size)
    except ValueError as e:
        print(f"{Colors.RED}{Colors.BOLD}Error: {e}{Colors.ENDC}")
        return 1

    try:
        resize_to_target_filesize(
            args.image_path,
            target_bytes,
            args.output,
            args.format,
            args.min_dimension,
            exact_size=not args.no_exact
        )
        return 0
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Process interrupted by user.{Colors.ENDC}")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}Error: {e}{Colors.ENDC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
