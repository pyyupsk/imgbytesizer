"""
Script to sort requirements*-dev.txt files alphabetically.
Usage: python scripts/sort_requirements.py [directory]
If no directory is specified, it will search in the current directory.
"""

import glob
import os
import sys


def sort_requirements_file(filepath):
  """Sort a requirements file alphabetically, preserving comments and blank lines."""
  try:
    with open(filepath, 'r') as f:
      lines = f.readlines()

    # Separate comments, blank lines, and actual requirements
    comments_and_blanks = []
    requirements = []

    for line in lines:
      line = line.strip()
      if not line or line.startswith('#'):
        comments_and_blanks.append(line)
      else:
        # Handle lines with inline comments
        if '#' in line:
          req_part, comment_part = line.split('#', 1)
          requirements.append((req_part.strip(), f"#{comment_part}"))
        else:
          requirements.append((line, ""))

    # Sort requirements, ignoring case
    requirements.sort(key=lambda x: x[0].lower())

    # Write sorted content back to file
    with open(filepath, 'w') as f:
      # First write all comments and blank lines
      for line in comments_and_blanks:
        f.write(f"{line}\n")

      # Then write sorted requirements
      if comments_and_blanks and requirements:
        f.write("\n")  # Add separation between comments and requirements

      for req, comment in requirements:
        if comment:
          f.write(f"{req} {comment}\n")
        else:
          f.write(f"{req}\n")

    print(f"✓ Sorted {filepath}")
    return True
  except Exception as e:
    print(f"Error processing {filepath}: {e}")
    return False


def main():
  """Find and sort all requirements*.txt files."""
  # Get directory from command line argument, or use current directory
  directory = sys.argv[1] if len(sys.argv) > 1 else "."

  # Find all requirements*.txt files
  pattern = os.path.join(directory, "requirements*.txt")
  requirement_files = glob.glob(pattern)

  if not requirement_files:
    print(f"No files matching '{pattern}' found.")
    return

  print(f"Found {len(requirement_files)} requirements file(s) to sort:")

  success_count = 0
  for filepath in requirement_files:
    if sort_requirements_file(filepath):
      success_count += 1

  print(f"\nSorted {success_count} out of {len(requirement_files)} files.")


if __name__ == "__main__":
  main()
