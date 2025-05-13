from imgbytesizer.formatter import format_filesize


def test_format_filesize():
  # Test various file sizes
  assert format_filesize(500) == "500 B"
  assert format_filesize(1024) == "1.00 KB"
  assert format_filesize(1024 * 1024) == "1.00 MB"
  assert format_filesize(1024 * 1024 * 1.5) == "1.50 MB"

  # Test with different precision
  assert format_filesize(1024, precision=0) == "1 KB"
  assert format_filesize(1024 * 1024 * 1.234, precision=3) == "1.234 MB"

  # Test with None
  assert format_filesize(None) == "N/A"
