"""
Terminal formatting utilities for imgbytesizer.
"""

import sys
import logging
from typing import Tuple, Optional
from tabulate import tabulate

from .logger import Colors


def format_filesize(size_bytes: int | None, precision: int = 2) -> str:
    """Format file size in a human-readable format."""
    if size_bytes is None:
        return "N/A"

    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.{precision}f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.{precision}f} MB"


def print_progress_bar(
    progress: int, total: int, prefix: str = "", suffix: str = "", length: int = 30
) -> None:
    """Print a progress bar with percentage."""
    if not sys.stdout.isatty():
        return  # Don't print progress bars if not in a terminal

    percent = min(100, int(100.0 * progress / total))
    filled_length = int(length * progress // total)
    bar = "█" * filled_length + "░" * (length - filled_length)

    if Colors.supports_color():
        print(
            f"\r{prefix} |{Colors.GREEN}{bar}{Colors.ENDC}| {percent}% {suffix}",
            end="\r",
        )
    else:
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end="\r")

    if progress == total:
        print()


def print_result(name: str, value: str, status: Optional[str] = None) -> None:
    """Print a name-value pair with optional status color."""
    value_color = Colors.ENDC
    if status == "good":
        value_color = Colors.GREEN
    elif status == "warning":
        value_color = Colors.YELLOW
    elif status == "bad":
        value_color = Colors.RED

    if Colors.supports_color():
        print(f"  {Colors.BOLD}{name}:{Colors.ENDC} {value_color}{value}{Colors.ENDC}")
    else:
        print(f"  {name}: {value}")


def print_processing_step(step: int, description: str) -> None:
    """Print a processing step with a spinner."""
    if not sys.stdout.isatty():
        logger = logging.getLogger("imgbytesizer")
        logger.info(description)
        return

    spinner = ["◐", "◓", "◑", "◒"]

    if Colors.supports_color():
        print(f"{Colors.BLUE}{spinner[step % len(spinner)]}{Colors.ENDC} {description}")
    else:
        print(f"* {description}")


def print_comparison_table(
    original_size: int,
    original_dimensions: Tuple[int, int],
    final_size: int,
    final_dimensions: Tuple[int, int],
    target_size: int,
) -> None:
    """Print comparison table between original and processed image."""
    if not sys.stdout.isatty():
        # Use simpler output for non-terminal environments
        logger = logging.getLogger("imgbytesizer")
        logger.info(
            f"Original: {original_dimensions[0]}×{original_dimensions[1]}, "
            f"{format_filesize(original_size)}"
        )
        logger.info(
            f"Processed: {final_dimensions[0]}×{final_dimensions[1]}, {format_filesize(final_size)}"
        )
        logger.info(f"Target: {format_filesize(target_size)}")
        return

    orig_dim = f"{original_dimensions[0]}×{original_dimensions[1]}"
    new_dim = f"{final_dimensions[0]}×{final_dimensions[1]}"
    orig_size = format_filesize(original_size)
    new_size = format_filesize(final_size)
    target = format_filesize(target_size)
    diff = abs(final_size - target_size)
    diff_pct = (diff / target_size) * 100
    reduction = (
        ((original_size - final_size) / original_size) * 100
        if original_size > final_size
        else 0
    )

    # Determine color based on how close to target
    if diff_pct < 1:
        diff_color = Colors.GREEN
    elif diff_pct < 5:
        diff_color = Colors.YELLOW
    else:
        diff_color = Colors.RED

    if Colors.supports_color():
        table = [
            [
                f"{Colors.BOLD}Dimensions{Colors.ENDC}",
                f"{Colors.CYAN}{orig_dim}{Colors.ENDC}",
                f"{Colors.GREEN}{new_dim}{Colors.ENDC}",
            ],
            [
                f"{Colors.BOLD}Size{Colors.ENDC}",
                f"{Colors.CYAN}{orig_size}{Colors.ENDC}",
                f"{Colors.GREEN}{new_size}{Colors.ENDC}",
            ],
            [
                f"{Colors.BOLD}Target Size{Colors.ENDC}",
                "",
                f"{Colors.BLUE}{target}{Colors.ENDC}",
            ],
            [
                f"{Colors.BOLD}Difference{Colors.ENDC}",
                "",
                f"{diff_color}{format_filesize(diff)} ({diff_pct:.1f}%){Colors.ENDC}",
            ],
            [
                f"{Colors.BOLD}Reduction{Colors.ENDC}",
                "",
                (
                    f"{Colors.CYAN}{reduction:.1f}% smaller{Colors.ENDC}"
                    if reduction
                    else f"{Colors.YELLOW}N/A{Colors.ENDC}"
                ),
            ],
        ]

        headers = [
            f"{Colors.UNDERLINE}Metric{Colors.ENDC}",
            f"{Colors.UNDERLINE}Original{Colors.ENDC}",
            f"{Colors.UNDERLINE}Processed{Colors.ENDC}",
        ]
    else:
        table = [
            ["Dimensions", orig_dim, new_dim],
            ["Size", orig_size, new_size],
            ["Target Size", "", target],
            ["Difference", "", f"{format_filesize(diff)} ({diff_pct:.1f}%)"],
            ["Reduction", "", f"{reduction:.1f}% smaller" if reduction else "N/A"],
        ]

        headers = ["Metric", "Original", "Processed"]

    print()
    print(tabulate(table, headers=headers, tablefmt="rounded_grid"))
