import os

import pytest
from PIL import Image

from imgbytesizer.resizer import (
    _adjust_final_size, _adjust_to_exact_size, _apply_min_dimension_constraint,
    _binary_search_scale, _final_quality_adjustment, _find_best_quality, _handle_format_conversion,
    _try_combined_approach, _try_minimum_size, _try_quality_adjustment, _try_resizing,
    _try_scale_with_quality, resize_to_target_filesize, _setup_image
)


@pytest.fixture
def sample_image():
  # Create a test image
  img = Image.new("RGB", (800, 600), color="red")
  img_path = "test_image.jpg"
  img.save(img_path, "JPEG", quality=95)
  yield img_path
  # Cleanup
  if os.path.exists(img_path):
    os.remove(img_path)


@pytest.fixture
def sample_png():
  # Create a test PNG image
  img = Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))
  img_path = "test_image.png"
  img.save(img_path, "PNG")
  yield img_path
  # Cleanup
  if os.path.exists(img_path):
    os.remove(img_path)


def test_resize_to_target_filesize_basic(sample_image):
  # Test basic resizing functionality
  target_size = 50 * 1024  # 50KB
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.jpg",
      format_name="JPEG",
      quiet=True,
  )

  assert os.path.exists(output_path)
  assert os.path.getsize(output_path) <= target_size
  os.remove(output_path)


def test_resize_to_target_filesize_format_conversion(sample_image):
  # Test format conversion
  target_size = 50 * 1024  # 50KB
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.webp",
      format_name="WEBP",
      quiet=True,
  )

  assert os.path.exists(output_path)
  assert output_path.endswith(".webp")
  os.remove(output_path)


def test_resize_to_target_filesize_min_dimension(sample_image):
  # Test minimum dimension constraint
  target_size = 50 * 1024  # 50KB
  min_dim = 400
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.jpg",
      format_name="JPEG",
      min_dimension=min_dim,
      quiet=True,
  )

  img = Image.open(output_path)
  width, height = img.size
  assert min(width, height) >= min_dim
  os.remove(output_path)


def test_resize_to_target_filesize_no_exact(sample_image):
  # Test without exact size matching
  target_size = 50 * 1024  # 50KB
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.jpg",
      format_name="JPEG",
      exact_size=False,
      quiet=True,
  )

  assert os.path.exists(output_path)
  assert os.path.getsize(output_path) <= target_size
  os.remove(output_path)


def test_try_quality_adjustment(sample_image):
  # Test quality adjustment function
  img = Image.open(sample_image)
  target_size = 50 * 1024  # 50KB
  result = _try_quality_adjustment(img, "JPEG", target_size, "test_output.jpg", quiet=True)

  assert result is not None
  assert os.path.exists(result)
  assert os.path.getsize(result) <= target_size
  os.remove(result)


def test_try_resizing(sample_image):
  # Test resizing function
  img = Image.open(sample_image)
  target_size = 50 * 1024  # 50KB
  result = _try_resizing(
      img,
      "JPEG",
      target_size,
      "test_output.jpg",
      800,  # original width
      600,  # original height
      None,  # no min dimension
      quiet=True,
  )

  assert result is not None
  assert os.path.exists(result)
  assert os.path.getsize(result) <= target_size
  os.remove(result)


def test_find_best_quality(sample_image):
  # Test quality finding function
  img = Image.open(sample_image)
  target_size = 50 * 1024  # 50KB
  result = _find_best_quality(img, "JPEG", target_size, quiet=True)

  assert result is not None
  size, _buffer = result
  assert size <= target_size


def test_adjust_to_exact_size(sample_image):
  # Test exact size adjustment
  img = Image.open(sample_image)
  target_size = 50 * 1024  # 50KB
  output_path = "test_output.jpg"
  img.save(output_path, "JPEG", quality=95)

  _adjust_to_exact_size(output_path, target_size, quiet=True)

  assert os.path.exists(output_path)
  assert abs(os.path.getsize(output_path) - target_size) <= 100
  os.remove(output_path)


def test_png_format(sample_png):
  # Test PNG format handling
  target_size = 50 * 1024  # 50KB
  output_path = resize_to_target_filesize(
      sample_png,
      target_size,
      output_path="test_output.png",
      format_name="PNG",
      quiet=True,
  )

  assert os.path.exists(output_path)
  assert output_path.endswith(".png")
  os.remove(output_path)


def test_invalid_input():
  # Test invalid input handling
  with pytest.raises(Exception):
    resize_to_target_filesize("nonexistent.jpg", 50 * 1024, quiet=True)


def test_small_target_size(sample_image):
  # Test with very small target size
  target_size = 1 * 1024  # 1KB
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.jpg",
      format_name="JPEG",
      quiet=True,
  )

  assert os.path.exists(output_path)
  assert os.path.getsize(output_path) <= target_size
  os.remove(output_path)


def test_large_target_size(sample_image):
  # Test with target size larger than original
  original_size = os.path.getsize(sample_image)
  target_size = original_size * 2  # Double the original size
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.jpg",
      format_name="JPEG",
      quiet=True,
  )

  assert os.path.exists(output_path)
  assert os.path.getsize(output_path) == original_size  # Should not increase size
  os.remove(output_path)


def test_try_combined_approach(sample_image):
  # Test combined scaling and quality approach
  img = Image.open(sample_image)
  target_size = 100 * 1024  # 100KB
  result = _try_combined_approach(
      img,
      "JPEG",
      target_size,
      "test_output.jpg",
      800,  # original width
      600,  # original height
      None,  # no min dimension
      quiet=True,
  )

  assert result is not None
  assert os.path.exists(result)
  assert os.path.getsize(result) <= target_size
  os.remove(result)


def test_final_quality_adjustment(sample_image):
  # Test final quality adjustment when overshooting
  img = Image.open(sample_image)
  target_size = 50 * 1024  # 50KB
  output_path = "test_output.jpg"
  img.save(output_path, "JPEG", quality=95)  # Save with high quality to ensure overshooting

  _final_quality_adjustment(output_path, "JPEG", target_size, quiet=True)

  assert os.path.exists(output_path)
  assert os.path.getsize(output_path) <= target_size
  os.remove(output_path)


def test_resize_to_target_filesize_error_handling():
  # Test various error conditions
  with pytest.raises(Exception):
    # Test with invalid image path
    resize_to_target_filesize("nonexistent.jpg", 50 * 1024, quiet=True)

  with pytest.raises(Exception):
    # Test with invalid format
    resize_to_target_filesize("test.jpg", 50 * 1024, format_name="INVALID", quiet=True)

  with pytest.raises(Exception):
    # Test with negative target size
    resize_to_target_filesize("test.jpg", -1, quiet=True)


def test_format_conversion_edge_cases(sample_image):
  # Test format conversion edge cases
  target_size = 50 * 1024  # 50KB

  # Test JPEG to PNG conversion
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.png",
      format_name="PNG",
      quiet=True,
  )
  assert output_path.endswith(".png")
  os.remove(output_path)

  # Test JPEG to WEBP conversion
  output_path = resize_to_target_filesize(
      sample_image,
      target_size,
      output_path="test_output.webp",
      format_name="WEBP",
      quiet=True,
  )
  assert output_path.endswith(".webp")
  os.remove(output_path)


def test_setup_image_quiet(sample_image):
  # Test _setup_image with quiet=True
  img, width, height, size = _setup_image(sample_image, quiet=True)
  assert img is not None
  assert width == 800
  assert height == 600
  assert size > 0


def test_handle_format_conversion_no_change(sample_image):
  # Test format conversion when no change needed
  img = Image.open(sample_image)
  output_path = "test_output.jpg"
  result = _handle_format_conversion(img, sample_image, output_path, None, quiet=True)
  assert result == output_path
  assert os.path.exists(output_path)
  os.remove(output_path)


def test_adjust_final_size_overshooting(sample_image):
  # Test final size adjustment when overshooting
  img = Image.open(sample_image)
  target_size = 10 * 1024  # 10KB
  output_path = "test_output.jpg"
  img.save(output_path, "JPEG", quality=95)

  _adjust_final_size(output_path, target_size, "JPEG", True, quiet=True)
  assert os.path.exists(output_path)
  assert os.path.getsize(output_path) <= target_size
  os.remove(output_path)


def test_try_scale_with_quality_min_dimension(sample_image):
  # Test scale with quality and minimum dimension
  img = Image.open(sample_image)
  target_size = 50 * 1024  # 50KB
  min_dim = 400
  scale = 0.3  # This would make image smaller than min_dim

  size, buffer, final_scale = _try_scale_with_quality(
      img, "JPEG", target_size, scale, 800, 600, min_dim, quiet=True
  )

  assert size is not None
  assert buffer is not None
  assert final_scale is not None
  assert final_scale > scale  # Scale should be adjusted up to meet min_dim


def test_try_combined_approach_fallback(sample_image):
  # Test combined approach falling back to minimum size
  img = Image.open(sample_image)
  target_size = 1 * 1024  # 1KB - very small to force fallback
  output_path = "test_output.jpg"

  result = _try_combined_approach(img, "JPEG", target_size, output_path, 800, 600, None, quiet=True)

  assert result == output_path
  assert os.path.exists(output_path)
  os.remove(output_path)


def test_apply_min_dimension_constraint(sample_image):
  # Test minimum dimension constraint application
  new_width, new_height, scale = _apply_min_dimension_constraint(100, 100, 200)
  assert new_width >= 200
  assert new_height >= 200
  assert scale > 1.0


def test_binary_search_scale_overshooting(sample_image):
  # Test binary search scale when overshooting
  img = Image.open(sample_image)
  target_size = 10 * 1024  # 10KB
  result = _binary_search_scale(img, "JPEG", target_size, 800, 600, None, quiet=True)

  size, buffer, scale = result
  assert size is not None
  assert buffer is not None
  assert scale is not None
  assert size <= target_size


def test_try_minimum_size(sample_image):
  # Test minimum size fallback
  img = Image.open(sample_image)
  output_path = "test_output.jpg"
  result = _try_minimum_size(img, "JPEG", output_path, None, quiet=True)

  assert result == output_path
  assert os.path.exists(output_path)
  os.remove(output_path)


def test_final_quality_adjustment_failure(sample_image):
  # Test final quality adjustment failure handling
  with open("test_output.jpg", "w") as f:
    f.write("invalid image data")

  _final_quality_adjustment("test_output.jpg", "JPEG", 50 * 1024, quiet=True)
  os.remove("test_output.jpg")


def test_adjust_to_exact_size_padding(sample_image):
  # Test exact size adjustment with padding
  img = Image.open(sample_image)
  output_path = "test_output.jpg"
  img.save(output_path, "JPEG", quality=95)

  current_size = os.path.getsize(output_path)
  target_size = current_size + 1000  # Add 1KB padding

  _adjust_to_exact_size(output_path, target_size, quiet=True)
  assert os.path.getsize(output_path) == target_size
  os.remove(output_path)
