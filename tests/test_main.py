import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from imgbytesizer.main import main


@pytest.fixture
def mock_logger():
  with patch("imgbytesizer.main.setup_logger") as mock:
    yield mock.return_value


@pytest.fixture
def mock_resize():
  with patch("imgbytesizer.main.resize_to_target_filesize") as mock:
    yield mock


@pytest.fixture
def test_image(tmp_path):
  """Create a temporary test image."""
  image = tmp_path / "test.jpg"
  image.touch()
  return image


def test_main_entrypoint(tmp_path):
  script_path = Path(__file__).parent.parent / "imgbytesizer" / "main.py"
  test_image = tmp_path / "test.jpg"
  test_image.touch()

  result = subprocess.run(
      [sys.executable, str(script_path),
       str(test_image), "1KB", "-q"],
      capture_output=True,
      text=True,
  )

  assert result.returncode in (0, 1)


def test_version_display(capsys):
  """Test version display."""
  with patch.object(sys, "argv", ["imgbytesizer", "-v"]):
    assert main() == 0
    captured = capsys.readouterr()
    assert "imgbytesizer v" in captured.out


def test_help_display(capsys):
  """Test help display."""
  with patch.object(sys, "argv", ["imgbytesizer"]):
    assert main() == 0
    captured = capsys.readouterr()
    assert "Resize an image to match a target file size" in captured.out


def test_missing_arguments(capsys):
  """Test missing required arguments."""
  with patch.object(sys, "argv", ["imgbytesizer", "image.jpg"]):
    assert main() == 0
    captured = capsys.readouterr()
    assert "Resize an image to match a target file size" in captured.out


def test_nonexistent_file(mock_logger):
  """Test handling of nonexistent input file."""
  with patch.object(sys, "argv", ["imgbytesizer", "nonexistent.jpg", "1MB"]):
    assert main() == 1
    mock_logger.error.assert_called_once()


def test_invalid_filesize(mock_logger, test_image):
  """Test handling of invalid filesize."""
  with patch.object(sys, "argv", ["imgbytesizer", str(test_image), "invalid"]):
    assert main() == 1
    mock_logger.error.assert_called_once()


def test_successful_resize(mock_logger, mock_resize, test_image):
  """Test successful image resize."""
  mock_resize.return_value = Path("output.jpg")

  with patch.object(sys, "argv", ["imgbytesizer", str(test_image), "1MB"]):
    assert main() == 0
    mock_resize.assert_called_once()
    mock_logger.debug.assert_called_once()


def test_keyboard_interrupt(mock_logger, mock_resize, test_image):
  """Test handling of keyboard interrupt."""
  mock_resize.side_effect = KeyboardInterrupt()

  with patch.object(sys, "argv", ["imgbytesizer", str(test_image), "1MB"]):
    assert main() == 130
    mock_logger.warning.assert_called_once_with("Process interrupted by user.")


def test_general_exception(mock_logger, mock_resize, test_image):
  """Test handling of general exceptions."""
  mock_resize.side_effect = Exception("Test error")

  with patch.object(sys, "argv", ["imgbytesizer", str(test_image), "1MB"]):
    assert main() == 1
    mock_logger.error.assert_called_once_with("Error: Test error")


def test_debug_mode(mock_logger, mock_resize, test_image):
  """Test debug mode logging."""
  mock_resize.side_effect = Exception("Test error")

  with patch.object(sys, "argv", ["imgbytesizer", str(test_image), "1MB", "--debug"]):
    assert main() == 1
    mock_logger.setLevel.assert_called_once()
    mock_logger.exception.assert_called_once_with("Detailed error information:")


def test_quiet_mode(mock_logger, mock_resize, test_image):
  """Test quiet mode."""
  mock_resize.return_value = Path("output.jpg")

  with patch.object(sys, "argv", ["imgbytesizer", str(test_image), "1MB", "-q"]):
    assert main() == 0
    mock_logger.setLevel.assert_called_once()
