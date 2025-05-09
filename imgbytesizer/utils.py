"""
Utility functions for imgbytesizer.
"""
import io


def parse_filesize(size_str):
    """Parse a file size string like '1MB' to bytes."""
    size_str = size_str.strip().upper()
    if size_str.endswith('KB'):
        return int(float(size_str[:-2]) * 1024)
    elif size_str.endswith('MB'):
        return int(float(size_str[:-2]) * 1024 * 1024)
    elif size_str.endswith('GB'):
        return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
    elif size_str.endswith('B'):
        return int(size_str[:-1])
    else:
        try:
            return int(size_str)
        except ValueError:
            raise ValueError("Invalid file size format. Use B, KB, MB, or GB suffix.")


def get_file_size_bytes(img, format, quality=None):
    """Get the file size in bytes for an image with the specified format and quality."""
    out_buffer = io.BytesIO()
    save_args = {'format': format}
    if quality is not None:
        if format == 'JPEG':
            save_args['quality'] = quality
        elif format == 'PNG':
            save_args['optimize'] = True
            save_args['compress_level'] = quality
        elif format == 'WEBP':
            save_args['quality'] = quality

    img.save(out_buffer, **save_args)
    return out_buffer.tell(), out_buffer
