import sys
from io import StringIO
from imgbytesizer.formatter import (
    format_filesize,
    print_result,
)


def test_format_filesize():
    # Test various file sizes
    assert format_filesize(500) == "500 B"
    assert format_filesize(1024) == "1.00 KB"
    assert format_filesize(1024 * 1024) == "1.00 MB"
    assert format_filesize(1024 * 1024 * 1.5) == "1.50 MB"

    # Test with different precision
    assert format_filesize(1024, precision=0) == "1 KB"
    assert format_filesize(1024 * 1024 * 1.234, precision=3) == "1.234 MB"


def test_print_result():
    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    # Test basic result
    print_result("Test", "Value")
    output = captured_output.getvalue()

    # Reset stdout
    sys.stdout = sys.__stdout__

    # Check output
    assert "Test:" in output
    assert "Value" in output

    # Test with status
    captured_output = StringIO()
    sys.stdout = captured_output

    print_result("Test", "Value", "good")
    output = captured_output.getvalue()

    sys.stdout = sys.__stdout__

    # Check output contains status
    assert "Test:" in output
    assert "Value" in output
