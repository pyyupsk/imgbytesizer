"""
Terminal formatting utilities for imgbytesizer.
"""
import shutil
from tabulate import tabulate


# ANSI Color Codes for beautiful terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_terminal_width():
    """Get the width of the terminal."""
    try:
        columns = shutil.get_terminal_size().columns
        return max(80, columns)
    except Exception:
        return 80


def format_filesize(size_bytes):
    """Format file size in a human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024} KB"
    else:
        return f"{size_bytes/(1024*1024)} MB"


def print_progress_bar(progress, total, prefix='', suffix='', length=30):
    """Print a progress bar with percentage."""
    percent = min(100, int(100.0 * progress / total))
    filled_length = int(length * progress // total)
    bar = '█' * filled_length + '░' * (length - filled_length)
    print(f"\r{prefix} |{Colors.GREEN}{bar}{Colors.ENDC}| {percent}% {suffix}", end='\r')
    if progress == total:
        print()


def print_result(name, value, status=None):
    """Print a name-value pair with optional status color."""
    value_color = Colors.ENDC
    if status == 'good':
        value_color = Colors.GREEN
    elif status == 'warning':
        value_color = Colors.YELLOW
    elif status == 'bad':
        value_color = Colors.RED

    print(f"  {Colors.BOLD}{name}:{Colors.ENDC} {value_color}{value}{Colors.ENDC}")


def print_processing_step(step, description):
    """Print a processing step with a spinner."""
    spinner = ["◐", "◓", "◑", "◒"]
    print(f"{Colors.BLUE}{spinner[step % len(spinner)]}{Colors.ENDC} {description}")


def print_comparison_table(original_size, original_dimensions,
                           final_size, final_dimensions, target_size):

    orig_dim = f"{original_dimensions[0]}×{original_dimensions[1]}"
    new_dim = f"{final_dimensions[0]}×{final_dimensions[1]}"
    orig_size = format_filesize(original_size)
    new_size = format_filesize(final_size)
    target = format_filesize(target_size)
    diff = abs(final_size - target_size)
    diff_pct = (diff / target_size) * 100
    reduction = ((original_size - final_size) / original_size) * \
        100 if original_size > final_size else 0

    # Determine color based on how close to target
    if diff_pct < 1:
        diff_color = Colors.GREEN
    elif diff_pct < 5:
        diff_color = Colors.YELLOW
    else:
        diff_color = Colors.RED

    table = [
        [f"{Colors.BOLD}Dimensions{Colors.ENDC}", f"{Colors.CYAN}{orig_dim}{Colors.ENDC}",
            f"{Colors.GREEN}{new_dim}{Colors.ENDC}"],
        [f"{Colors.BOLD}Size{Colors.ENDC}", f"{Colors.CYAN}{orig_size}{Colors.ENDC}",
            f"{Colors.GREEN}{new_size}{Colors.ENDC}"],
        [f"{Colors.BOLD}Target Size{Colors.ENDC}", "", f"{Colors.BLUE}{target}{Colors.ENDC}"],
        [f"{Colors.BOLD}Difference{Colors.ENDC}", "",
            f"{diff_color}{format_filesize(diff)} ({diff_pct:.1f}%){Colors.ENDC}"],
        [f"{Colors.BOLD}Reduction{Colors.ENDC}", "",
            f"{Colors.CYAN}{reduction:.1f}% smaller{Colors.ENDC}"
            if reduction else f"{Colors.YELLOW}N/A{Colors.ENDC}"]
    ]

    print()
    print(
        tabulate(table, headers=[
            f"{Colors.UNDERLINE}Metric{Colors.ENDC}",
            f"{Colors.UNDERLINE}Original{Colors.ENDC}",
            f"{Colors.UNDERLINE}Processed{Colors.ENDC}"
        ], tablefmt="rounded_grid")
    )
