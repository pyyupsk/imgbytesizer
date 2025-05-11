import sys
import logging
from typing import Dict, ClassVar


# ANSI Color Codes for beautiful terminal output
class Colors:
    BLUE: ClassVar[str] = "\033[94m"
    CYAN: ClassVar[str] = "\033[96m"
    GREEN: ClassVar[str] = "\033[92m"
    YELLOW: ClassVar[str] = "\033[93m"
    RED: ClassVar[str] = "\033[91m"
    ENDC: ClassVar[str] = "\033[0m"
    BOLD: ClassVar[str] = "\033[1m"
    UNDERLINE: ClassVar[str] = "\033[4m"

    @staticmethod
    def supports_color() -> bool:
        """Check if the terminal supports color output."""
        # Add proper color support detection for different platforms
        return sys.stdout.isatty()


class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored console output."""

    FORMATS: ClassVar[Dict[int, str]] = {
        logging.DEBUG: Colors.BLUE + "%(message)s" + Colors.ENDC,
        logging.INFO: "%(message)s",
        logging.WARNING: Colors.YELLOW + "%(message)s" + Colors.ENDC,
        logging.ERROR: Colors.RED + Colors.BOLD + "%(message)s" + Colors.ENDC,
        logging.CRITICAL: Colors.RED + Colors.BOLD + "%(message)s" + Colors.ENDC,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger() -> logging.Logger:
    """Setup and return the application logger."""
    logger = logging.getLogger("imgbytesizer")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        if Colors.supports_color():
            handler.setFormatter(ColoredFormatter())
        else:
            handler.setFormatter(logging.Formatter("%(message)s"))

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
