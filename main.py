import os
import sys
import argparse
from PIL import Image
import io


def get_file_size_bytes(img, format, quality=None):
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

    img = Image.open(image_path)
    orig_width, orig_height = img.size
    aspect_ratio = orig_width / orig_height

    if format is None:
        format = img.format

    pil_format = format.upper() if format else img.format
    print(f"Input format: {pil_format}")
    if pil_format == 'JPG':
        pil_format = 'JPEG'

    if output_path is None:
        base_name, _ = os.path.splitext(image_path)
        output_path = f"{base_name}_resized.{pil_format.lower()}"

    orig_size, _ = get_file_size_bytes(img, pil_format)
    if orig_size <= target_size_bytes:
        print(
            f"Original image is already smaller than target size: "
            f"{orig_size} bytes vs {target_size_bytes} bytes"
        )
        img.save(output_path)
        return output_path

    print(f"Original image size: {orig_size/1024:.2f} KB ({orig_width}x{orig_height})")
    print(f"Target size: {target_size_bytes/1024:.2f} KB")

    if pil_format in ['JPEG', 'WEBP']:
        print("Trying quality adjustment without resizing...")
        low, high = 1, 95
        best_quality = None
        best_size = None
        best_buffer = None

        while low <= high:
            mid = (low + high) // 2
            size, buffer = get_file_size_bytes(img, pil_format, mid)

            print(f"  Quality {mid}: {size/1024:.2f} KB")

            if size <= target_size_bytes and (best_size is None or size > best_size):
                best_quality = mid
                best_size = size
                best_buffer = buffer

            if size > target_size_bytes:
                high = mid - 1
            else:
                low = mid + 1

        if best_size is not None:
            print(f"Found optimal quality: {best_quality} (size: {best_size/1024:.2f} KB)")
            with open(output_path, 'wb') as f:
                f.write(best_buffer.getvalue())
            return output_path

    print("Resizing image...")

    low_scale = 0.01
    high_scale = 1.0
    best_size = None
    best_buffer = None

    while high_scale - low_scale > 0.01:
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

        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        if pil_format in ['JPEG', 'WEBP']:
            quality_low, quality_high = 1, 95
            best_q = None
            best_q_size = None
            best_q_buffer = None

            while quality_low <= quality_high:
                q_mid = (quality_low + quality_high) // 2
                q_size, q_buffer = get_file_size_bytes(resized_img, pil_format, q_mid)

                if q_size <= target_size_bytes and (best_q_size is None or q_size > best_q_size):
                    best_q = q_mid
                    best_q_size = q_size
                    best_q_buffer = q_buffer

                if q_size > target_size_bytes:
                    quality_high = q_mid - 1
                else:
                    quality_low = q_mid + 1

            if best_q_size is not None:
                size, buffer = best_q_size, best_q_buffer
                print(
                    f"  Scale {mid_scale:.2f} ({new_width}x{new_height}) with quality {best_q}: "
                    f"{size/1024:.2f} KB"
                )
            else:
                size, buffer = get_file_size_bytes(resized_img, pil_format, 1)
                print(
                    f"  Scale {mid_scale:.2f} ({new_width}x{new_height}) with quality 1: "
                    f"{size/1024:.2f} KB"
                )
        else:
            size, buffer = get_file_size_bytes(resized_img, pil_format)
            print(f"  Scale {mid_scale:.2f} ({new_width}x{new_height}): {size/1024:.2f} KB")

        if size <= target_size_bytes and (best_size is None or size > best_size):
            best_size = size
            best_buffer = buffer

        if size > target_size_bytes:
            high_scale = mid_scale
        else:
            low_scale = mid_scale

    if best_buffer is None:
        print("Could not find a suitable size. Creating smallest possible image...")
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
        _, best_buffer = get_file_size_bytes(resized_img, pil_format, quality)

    with open(output_path, 'wb') as f:
        f.write(best_buffer.getvalue())

    final_img = Image.open(output_path)
    final_width, final_height = final_img.size
    final_size = os.path.getsize(output_path)

    if exact_size and final_size < target_size_bytes:
        print("Fine-tuning to exact file size...")

        if pil_format in ['JPEG', 'WEBP'] and abs(final_size - target_size_bytes) > 100:
            best_quality = None
            best_size_diff = abs(final_size - target_size_bytes)

            for quality in range(1, 101):
                test_buffer = io.BytesIO()
                final_img.save(test_buffer, format=pil_format, quality=quality)
                test_size = test_buffer.tell()
                size_diff = abs(test_size - target_size_bytes)

                if size_diff < best_size_diff:
                    best_quality = quality
                    best_size_diff = size_diff

            if best_quality is not None:
                final_img.save(output_path, format=pil_format, quality=best_quality)
                final_size = os.path.getsize(output_path)
                print(f"  Adjusted quality to {best_quality}: {final_size/1024:.2f} KB")

        if final_size < target_size_bytes:
            bytes_needed = target_size_bytes - final_size

            if pil_format == 'JPEG':
                comment = b'X' * bytes_needed
                temp_buffer = io.BytesIO(best_buffer.getvalue())
                temp_img = Image.open(temp_buffer)
                temp_img.save(output_path, format='JPEG', quality=95,
                              comment=comment.decode('latin1'))

            elif pil_format == 'PNG':
                final_img.save(output_path, format='PNG', pnginfo=None)

                with open(output_path, 'ab') as f:
                    pad = bytes_needed * b'P'
                    f.write(pad)
            else:
                with open(output_path, 'ab') as f:
                    f.write(b'P' * bytes_needed)

            final_size = os.path.getsize(output_path)
            print(f"  Padded file with {bytes_needed} bytes")

    print(f"\nFinal image: {final_width}x{final_height}, {final_size/1024:.2f} KB")
    print(f"Target size: {target_size_bytes/1024:.2f} KB")
    print(f"Difference: {abs(final_size - target_size_bytes)/1024:.2f} KB")
    print(f"Saved to: {output_path}")

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
    parser = argparse.ArgumentParser(description='Resize an image to match a target file size')

    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('target_size', help='Target file size (e.g., "1MB", "500KB")')
    parser.add_argument('-o', '--output', help='Output path (default: input_resized.ext)')
    parser.add_argument('-f', '--format', help='Output format (jpg, png, webp)')
    parser.add_argument('--min-dimension', type=int, help='Minimum width/height in pixels')
    parser.add_argument('--no-exact', action='store_true',
                        help='Do not pad file to get exact target size')

    args = parser.parse_args()

    try:
        target_bytes = parse_filesize(args.target_size)
    except ValueError as e:
        print(f"Error: {e}")
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
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
