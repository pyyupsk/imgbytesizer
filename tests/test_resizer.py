import os
import pytest
from PIL import Image
from imgbytesizer.resizer import (
    resize_to_target_filesize,
    _try_quality_adjustment,
    _try_resizing,
    _find_best_quality,
    _adjust_to_exact_size,
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
    result = _try_quality_adjustment(
        img, "JPEG", target_size, "test_output.jpg", quiet=True
    )

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
    size, buffer = result
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
