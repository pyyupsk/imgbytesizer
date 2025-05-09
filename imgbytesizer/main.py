"""
Command-line interface for imgbytesizer.
"""
import sys
import argparse

from .formatter import Colors
from .resizer import resize_to_target_filesize
from .utils import parse_filesize


def main():
    """Main entry point for the CLI."""
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
