"""
Command-line interface for imgbytesizer.
"""

import sys
import argparse
import logging
from pathlib import Path

from .logger import setup_logger
from .resizer import resize_to_target_filesize
from .utils import parse_filesize, IMG_FORMATS


def main() -> int:
    """Main entry point for the CLI."""
    # Setup logger
    logger = setup_logger()

    parser = argparse.ArgumentParser(
        description="Resize an image to match a target file size",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.jpg 500KB                   # Resize to 500 KB
  %(prog)s photo.png 2MB -o small_photo.png  # Resize to 2 MB with custom output
  %(prog)s image.jpg 100KB -f webp           # Resize and convert to WebP
  %(prog)s large.jpg 50KB --min-dimension 200  # Ensure min dimension is 200px
  %(prog)s -v                                # Show version information
    """,
    )

    parser.add_argument("image_path", nargs="?", help="Path to the input image")
    parser.add_argument(
        "target_size", nargs="?", help='Target file size (e.g., "1MB", "500KB")'
    )
    parser.add_argument(
        "-o", "--output", help="Output path (default: input_resized.ext)"
    )
    parser.add_argument("-f", "--format", choices=IMG_FORMATS, help="Output format")
    parser.add_argument(
        "--min-dimension", type=int, help="Minimum width/height in pixels"
    )
    parser.add_argument(
        "--no-exact",
        action="store_true",
        help="Do not pad file to get exact target size",
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Show version information"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")

    # Handle version flag before checking required arguments
    args = parser.parse_args()

    # Handle version request
    if args.version:
        from . import __version__

        print(f"imgbytesizer v{__version__}")
        return 0

    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)

    # Handle no arguments case with nice help
    if args.image_path is None or args.target_size is None:
        parser.print_help()
        return 0

    # Validate input file exists
    image_path = Path(args.image_path)
    if not image_path.exists():
        logger.error(f"Input file not found: {args.image_path}")
        return 1

    try:
        target_bytes = parse_filesize(args.target_size)
    except ValueError as e:
        logger.error(f"Error: {e}")
        return 1

    try:
        output_path = resize_to_target_filesize(
            args.image_path,
            target_bytes,
            args.output,
            args.format,
            args.min_dimension,
            exact_size=not args.no_exact,
            quiet=args.quiet,
        )

        logger.debug(f"Successfully processed image: {output_path}")
        return 0
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user.")
        return 130
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.debug:
            logger.exception("Detailed error information:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
