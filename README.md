# ImgByteSizer

[![PyPI version](https://img.shields.io/pypi/v/imgbytesizer.svg)](https://pypi.org/project/imgbytesizer/)
[![PyPI Downloads](https://static.pepy.tech/badge/imgbytesizer)](https://pepy.tech/projects/imgbytesizer)

ImgByteSizer is a command-line tool that precisely resizes and optimizes images to match a specific file size while maintaining the best possible quality.

## Features

- 🎯 Resize images to an exact target file size
- 🖼️ Maintains aspect ratio during resizing
- 🔍 Intelligent quality optimization with binary search
- 🔄 Format conversion (JPEG, PNG, WebP)
- 📏 Minimum dimension constraints
- 🎨 Beautiful terminal output with progress indicators
- 📊 Detailed comparison of original vs. processed images

## Installation

```bash
pip install imgbytesizer
```

## Usage

```bash
imgbytesizer image.jpg 500KB
```

### Basic Examples

```bash
# Resize an image to 500KB
imgbytesizer large_photo.jpg 500KB

# Resize and convert to WebP format
imgbytesizer image.png 250KB -f webp

# Specify output file path
imgbytesizer photo.jpg 1MB -o compressed_photo.jpg

# Ensure minimum dimension is at least 400px
imgbytesizer large_image.jpg 300KB --min-dimension 400
```

### Command-Line Options

```bash
usage: imgbytesizer [-h] [-o OUTPUT] [-f FORMAT] [--min-dimension MIN_DIMENSION] [--no-exact] image_path target_size

Resize an image to match a target file size

positional arguments:
  image_path            Path to the input image
  target_size           Target file size (e.g., "1MB", "500KB")

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Output path (default: input_resized.ext)
  -f, --format FORMAT   Output format (jpg, png, webp)
  --min-dimension MIN_DIMENSION
                        Minimum width/height in pixels
  --no-exact            Do not pad file to get exact target size
```

## How It Works

ImgByteSizer uses binary search algorithms to efficiently find the optimal combination of image dimensions and compression quality to match your target file size:

1. First attempts to adjust quality without resizing (for formats that support quality settings)
2. If quality adjustment alone isn't sufficient, performs binary search for optimal dimensions
3. Fine-tunes with an additional quality optimization pass
4. Adds minimal padding if necessary to hit the exact target size

The tool prioritizes maintaining the highest possible quality while meeting the target size constraint.

## Example Output

```
◐ Opening photo.jpg
  File: photo.jpg
  Format: JPEG
  Dimensions: 4032 × 3024 pixels
  Size: 2.5 MB
  Target size: 500 KB

Trying quality adjustment without resizing...
Testing quality 48 |██████████████████████████████| 100% Size: 497.3 KB

✓ Found optimal quality: 48 (size: 497.3 KB)

┌────────────┬──────────────┬───────────────┐
│   Metric   │   Original   │   Processed   │
├────────────┼──────────────┼───────────────┤
│ Dimensions │  4032×3024   │ 4032×3024     │
│ Size       │   2.5 MB     │ 497.3 KB      │
│ Target Size│              │ 500 KB        │
│ Difference │              │ 2.7 KB (0.5%) │
│ Reduction  │              │ 80.1% smaller │
└────────────┴──────────────┴───────────────┘
  Time taken: 0.87 seconds
  Output file: photo_resized.jpg
```

## Real Use Cases

### Web Development

```bash
# Create images that won't exceed page weight budget
imgbytesizer hero.jpg 200KB --min-dimension 1200
imgbytesizer background.png 100KB -f webp
```

### Email Attachments

```bash
# Shrink images to fit email attachment limits
imgbytesizer family_photo.jpg 5MB
```

### Social Media Uploads

```bash
# Optimize images for social media platforms with size limits
imgbytesizer profile_pic.jpg 400KB --min-dimension 400
```

## Requirements

- Python 3.9+
- Dependencies:
  - Pillow >= 11.0.0
  - tabulate >= 0.9.0

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
