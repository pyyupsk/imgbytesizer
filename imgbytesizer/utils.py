"""
Utility functions for imgbytesizer.
"""

import io
import logging
from pathlib import Path
from typing import Tuple, Optional, Union, List, Dict, Any
from PIL import Image


# Supported image formats
IMG_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp"]

# Logger
logger = logging.getLogger("imgbytesizer")


def parse_filesize(size_str: str) -> int:
    """Parse a file size string like '1MB' to bytes."""
    if not size_str:
        raise ValueError("File size cannot be empty")

    size_str = size_str.strip().upper()

    # Handle decimal points in size strings
    try:
        if size_str.endswith("KB"):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith("MB"):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith("GB"):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        elif size_str.endswith("B"):
            return int(size_str[:-1])
        else:
            return int(float(size_str))
    except ValueError:
        raise ValueError("Invalid file size format. Use B, KB, MB, or GB suffix.")


def get_file_size_bytes(
    img: Image.Image, format_name: str, quality: Optional[int] = None
) -> Tuple[int, io.BytesIO]:
    """Get the file size in bytes for an image with the specified format and quality."""
    out_buffer = io.BytesIO()
    save_args: Dict[str, Any] = {"format": format_name}

    # Apply quality settings based on format
    if quality is not None:
        if format_name in ["JPEG", "JPG"]:
            save_args["quality"] = quality
            save_args["optimize"] = True
        elif format_name == "PNG":
            save_args["optimize"] = True
            save_args["compress_level"] = min(
                9, quality // 10
            )  # Map quality to compress_level
        elif format_name == "WEBP":
            save_args["quality"] = quality
            save_args["method"] = 6  # Higher quality compression method

    logger.debug(f"Saving with format {format_name}, params: {save_args}")

    try:
        img.save(out_buffer, **save_args)
        size = out_buffer.tell()
        logger.debug(f"Image size with {format_name}, quality {quality}: {size} bytes")
        return size, out_buffer
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise


def get_output_format(input_format: str, requested_format: Optional[str] = None) -> str:
    """Determine the output format based on input and requested format."""
    if requested_format:
        format_name = requested_format.upper()
    else:
        format_name = input_format

    # Normalize format names
    if format_name == "JPG":
        format_name = "JPEG"

    return format_name


def get_output_path(
    image_path: Union[str, Path],
    output_path: Optional[str] = None,
    format_name: Optional[str] = None,
) -> str:
    """Generate appropriate output path."""
    path = Path(image_path)

    if output_path:
        return output_path

    # Determine extension
    if format_name:
        ext = format_name.lower()
        if ext == "jpeg":
            ext = "jpg"
    else:
        ext = path.suffix[1:] if path.suffix else "jpg"

    return f"{path.stem}_resized.{ext}"
