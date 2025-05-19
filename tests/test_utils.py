import io

import pytest
from PIL import Image

from imgbytesizer.utils import (
    IMG_FORMATS, get_file_size_bytes, get_output_format, get_output_path, parse_filesize
)


def test_parse_filesize():
  # Test various file size formats
  assert parse_filesize("1KB") == 1024
  assert parse_filesize("1MB") == 1024 * 1024
  assert parse_filesize("1GB") == 1024 * 1024 * 1024
  assert parse_filesize("500B") == 500
  assert parse_filesize("1.5KB") == int(1.5 * 1024)
  assert parse_filesize("2.5MB") == int(2.5 * 1024 * 1024)


def test_parse_filesize_invalid():
  # Test invalid file size formats
  with pytest.raises(ValueError):
    parse_filesize("")
  with pytest.raises(ValueError):
    parse_filesize("invalid")
  with pytest.raises(ValueError):
    parse_filesize("1TB")  # Unsupported unit


def test_get_output_format():
  # Test format determination
  assert get_output_format("JPEG") == "JPEG"
  assert get_output_format("JPG") == "JPEG"
  assert get_output_format("PNG") == "PNG"
  assert get_output_format("WEBP") == "WEBP"

  # Test with requested format
  assert get_output_format("JPEG", "PNG") == "PNG"
  assert get_output_format("PNG", "WEBP") == "WEBP"
  assert get_output_format("JPG", "JPEG") == "JPEG"


def test_get_output_path():
  # Test output path generation
  assert get_output_path("image.jpg") == "image_resized.jpg"
  assert get_output_path("image.png") == "image_resized.png"
  assert get_output_path("image.jpg", "custom.jpg") == "custom.jpg"
  assert get_output_path("image.jpg", format_name="PNG") == "image_resized.png"
  assert get_output_path("image.jpg", format_name="WEBP") == "image_resized.webp"
  assert get_output_path("image.jpg", "custom.webp", "WEBP") == "custom.webp"


def test_get_file_size_bytes():
  # Create test image
  img = Image.new("RGB", (100, 100), color="red")

  # Test JPEG format
  size, buffer = get_file_size_bytes(img, "JPEG", quality=95)
  assert size > 0
  assert isinstance(buffer, io.BytesIO)

  # Test PNG format
  size, buffer = get_file_size_bytes(img, "PNG")
  assert size > 0
  assert isinstance(buffer, io.BytesIO)

  # Test WEBP format
  size, buffer = get_file_size_bytes(img, "WEBP", quality=95)
  assert size > 0
  assert isinstance(buffer, io.BytesIO)


def test_get_file_size_bytes_invalid():
  # Create test image
  img = Image.new("RGB", (100, 100), color="red")

  # Test invalid format
  with pytest.raises(Exception):
    get_file_size_bytes(img, "INVALID")


def test_img_formats():
  # Test supported formats
  assert "jpg" in IMG_FORMATS
  assert "jpeg" in IMG_FORMATS
  assert "png" in IMG_FORMATS
  assert "webp" in IMG_FORMATS
  assert len(IMG_FORMATS) == 4


def test_get_file_size_bytes_png_with_quality():
  img = Image.new("RGB", (50, 50), color="blue")
  size, buffer = get_file_size_bytes(img, "PNG", quality=80)
  assert size > 0


def test_get_output_path_with_jpeg_extension():
  assert get_output_path("image.jpg", format_name="jpeg") == "image_resized.jpg"
