import sys
import logging


# ANSI Color Codes for beautiful terminal output
class Colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def supports_color():
        """Check if the terminal supports color output."""
        # Add proper color support detection for different platforms
        return sys.stdout.isatty()


class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored console output."""

    FORMATS = {
        logging.DEBUG: Colors.BLUE + "%(message)s" + Colors.ENDC,
        logging.INFO: "%(message)s",
        logging.WARNING: Colors.YELLOW + "%(message)s" + Colors.ENDC,
        logging.ERROR: Colors.RED + Colors.BOLD + "%(message)s" + Colors.ENDC,
        logging.CRITICAL: Colors.RED + Colors.BOLD + "%(message)s" + Colors.ENDC,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger():
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
