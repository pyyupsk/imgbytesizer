from imgbytesizer.formatter import format_filesize


def test_format_filesize():
  # Test various file sizes
  assert format_filesize(500) == "500.0B"
  assert format_filesize(1024) == "1.0KB"
  assert format_filesize(1024 * 1024) == "1.0MB"
  assert format_filesize(1024 * 1024 * 1.5) == "1.5MB"

  # Test with None
  assert format_filesize(None) == "N/A"
