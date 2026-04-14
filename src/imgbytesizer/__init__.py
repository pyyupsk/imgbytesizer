"""
imgbytesizer: A CLI tool to resize images to a target file size.
"""

from importlib.metadata import metadata

_meta = metadata("imgbytesizer")

__version__: str = _meta["Version"]
__author__: str = _meta["Author-email"].split(" <")[0]
__description__: str = _meta["Summary"]
