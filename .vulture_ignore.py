# This file is used by vulture to mark certain symbols as used,
# even if they're not explicitly referenced in the code.

from unittest.mock import Mock

from PIL import ImageFile

# Required to allow PIL to load incomplete/truncated images.
ImageFile.LOAD_TRUNCATED_IMAGES  # imgbytesizer/resizer.py

_mock = Mock()
_mock.side_effect  # tests/test_main.py
