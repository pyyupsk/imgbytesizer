import sys
from io import StringIO

from imgbytesizer.logger import print_result


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
  assert "Test:" in output
  assert "Value" in output

  # Test with 'warning' status
  captured_output = StringIO()
  sys.stdout = captured_output
  print_result("Test", "Value", "warning")
  output = captured_output.getvalue()
  sys.stdout = sys.__stdout__
  assert "Test:" in output
  assert "Value" in output

  # Test with 'bad' status
  captured_output = StringIO()
  sys.stdout = captured_output
  print_result("Test", "Value", "bad")
  output = captured_output.getvalue()
  sys.stdout = sys.__stdout__
  assert "Test:" in output
  assert "Value" in output
