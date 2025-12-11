"""
Utility Functions
Path sanitization, file operations, and other helper functions
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status


class PathSecurityError(HTTPException):
    """Custom path security error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path security violation: {detail}"
        )


def sanitize_path(filepath: str) -> str:
    """
    Remove path traversal attempts from filepath

    Args:
        filepath: Path to sanitize

    Returns:
        Sanitized path

    Raises:
        PathSecurityError: If path contains traversal attempts
    """
    if not filepath:
        raise PathSecurityError("Empty filepath")

    # Reject absolute paths
    if filepath.startswith('/') or filepath.startswith('\\'):
        raise PathSecurityError("Absolute paths not allowed")

    # Reject Windows drive letters
    if len(filepath) >= 2 and filepath[1] == ':':
        raise PathSecurityError("Drive letters not allowed")

    # Check for parent directory references
    if '..' in filepath:
        raise PathSecurityError("Parent directory references (..) not allowed")

    # Normalize path
    normalized = os.path.normpath(filepath)

    # Double-check after normalization
    if '..' in normalized or normalized.startswith('/') or normalized.startswith('\\'):
        raise PathSecurityError("Path traversal detected after normalization")

    # Check for null bytes
    if '\x00' in normalized:
        raise PathSecurityError("Null bytes not allowed in paths")

    return normalized


def safe_join(base_dir: str, *paths: str) -> str:
    """
    Safely join paths and verify result is within base directory

    Args:
        base_dir: Base directory path
        *paths: Path components to join

    Returns:
        Absolute path within base directory

    Raises:
        PathSecurityError: If result would be outside base directory
    """
    # Resolve base directory to absolute path
    base = Path(base_dir).resolve()

    # Join paths
    target = base.joinpath(*paths).resolve()

    # Verify target is within base directory
    try:
        target.relative_to(base)
    except ValueError:
        raise PathSecurityError(
            f"Path traversal attempt: {target} is not within {base}"
        )

    return str(target)


def generate_job_id() -> str:
    """
    Generate cryptographically secure job ID

    Returns:
        Full UUID4 string (36 characters including hyphens)
    """
    return str(uuid.uuid4())


def generate_safe_filename(extension: str, prefix: str = "") -> str:
    """
    Generate safe filename with UUID

    Args:
        extension: File extension (with or without leading dot)
        prefix: Optional prefix for filename

    Returns:
        Safe filename like "prefix_uuid.ext" or "uuid.ext"

    Raises:
        ValueError: If extension is not allowed
    """
    # Normalize extension
    if not extension.startswith('.'):
        extension = f'.{extension}'

    extension = extension.lower()

    # Validate extension against allowed list
    allowed_extensions = {
        '.jpg', '.jpeg', '.png', '.webp',  # Images
        '.mp4', '.webm', '.avi', '.mov'     # Videos
    }

    if extension not in allowed_extensions:
        raise ValueError(
            f"Invalid extension: {extension}. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate UUID
    file_uuid = uuid.uuid4()

    # Build filename
    if prefix:
        # Sanitize prefix (only allow alphanumeric, dash, underscore)
        safe_prefix = ''.join(c for c in prefix if c.isalnum() or c in '-_')
        if not safe_prefix:
            safe_prefix = "file"
        filename = f"{safe_prefix}_{file_uuid}{extension}"
    else:
        filename = f"{file_uuid}{extension}"

    return filename


def ensure_directory_exists(directory: str) -> str:
    """
    Ensure directory exists, create if it doesn't

    Args:
        directory: Directory path

    Returns:
        Absolute path to directory

    Raises:
        OSError: If directory cannot be created
    """
    path = Path(directory)

    try:
        path.mkdir(parents=True, exist_ok=True)
        return str(path.resolve())
    except Exception as e:
        raise OSError(f"Failed to create directory {directory}: {e}")


def safe_delete_file(filepath: str, base_dir: Optional[str] = None) -> bool:
    """
    Safely delete a file with path validation

    Args:
        filepath: Path to file to delete
        base_dir: Optional base directory to restrict deletions to

    Returns:
        True if file was deleted, False if file didn't exist

    Raises:
        PathSecurityError: If path validation fails
    """
    # If base_dir specified, validate path is within it
    if base_dir:
        filepath = safe_join(base_dir, os.path.basename(filepath))

    path = Path(filepath)

    # Check if file exists
    if not path.exists():
        return False

    # Must be a file (not directory)
    if not path.is_file():
        raise PathSecurityError(f"Not a file: {filepath}")

    # Delete file
    try:
        path.unlink()
        return True
    except Exception as e:
        raise OSError(f"Failed to delete file {filepath}: {e}")


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in megabytes

    Args:
        filepath: Path to file

    Returns:
        Size in MB
    """
    size_bytes = Path(filepath).stat().st_size
    return size_bytes / (1024 * 1024)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "1m 23s" or "45s"
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.0f}s"

    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"


def sanitize_error_message(error: Exception, include_type: bool = True) -> str:
    """
    Sanitize error message to prevent information leakage

    Args:
        error: Exception object
        include_type: Whether to include exception type

    Returns:
        Sanitized error message safe to return to users
    """
    # Get base error message
    error_msg = str(error)

    # Remove file paths
    import re
    error_msg = re.sub(r'(/[\w/\-\.]+)', '[PATH]', error_msg)
    error_msg = re.sub(r'([A-Z]:\\[\w\\\-\.]+)', '[PATH]', error_msg)

    # Remove line numbers
    error_msg = re.sub(r'line \d+', 'line [N]', error_msg)

    # Remove memory addresses
    error_msg = re.sub(r'0x[0-9a-fA-F]+', '0x[ADDR]', error_msg)

    # Truncate if too long
    error_msg = truncate_string(error_msg, max_length=200)

    # Add type if requested
    if include_type:
        return f"{type(error).__name__}: {error_msg}"

    return error_msg


def validate_job_id_format(job_id: str) -> bool:
    """
    Validate job ID format (UUID4)

    Args:
        job_id: Job ID to validate

    Returns:
        True if valid UUID4 format
    """
    try:
        uuid_obj = uuid.UUID(job_id, version=4)
        return str(uuid_obj) == job_id
    except (ValueError, AttributeError):
        return False


# File type detection helpers
def get_image_format(filepath: str) -> Optional[str]:
    """
    Detect image format from file header

    Args:
        filepath: Path to image file

    Returns:
        Format string ('jpeg', 'png', 'webp') or None
    """
    try:
        with open(filepath, 'rb') as f:
            header = f.read(12)

        # JPEG
        if header[:3] == b'\xff\xd8\xff':
            return 'jpeg'

        # PNG
        if header[:8] == b'\x89PNG\r\n\x1a\n':
            return 'png'

        # WebP
        if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
            return 'webp'

        return None
    except Exception:
        return None


def is_valid_image(filepath: str) -> bool:
    """
    Check if file is a valid image

    Args:
        filepath: Path to file

    Returns:
        True if valid image
    """
    return get_image_format(filepath) is not None


# Async file operations for FastAPI
async def save_upload_file(upload_file, destination: str) -> int:
    """
    Save uploaded file to destination with chunked reading

    Args:
        upload_file: FastAPI UploadFile object
        destination: Destination file path

    Returns:
        Number of bytes written
    """
    chunk_size = 1024 * 1024  # 1MB chunks
    total_bytes = 0

    # Ensure destination directory exists
    ensure_directory_exists(os.path.dirname(destination))

    try:
        with open(destination, 'wb') as f:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                total_bytes += len(chunk)

        return total_bytes
    except Exception as e:
        # Clean up partial file on error
        if os.path.exists(destination):
            os.remove(destination)
        raise OSError(f"Failed to save upload: {e}")


if __name__ == "__main__":
    # Test utilities
    print("Testing utilities...")

    # Generate job ID
    job_id = generate_job_id()
    print(f"Job ID: {job_id}")
    print(f"Valid: {validate_job_id_format(job_id)}")

    # Generate filenames
    print(f"\nImage filename: {generate_safe_filename('.jpg', 'input')}")
    print(f"Video filename: {generate_safe_filename('.mp4', 'output')}")

    # Test path sanitization
    print("\nPath sanitization tests:")
    try:
        sanitize_path("../etc/passwd")
    except PathSecurityError as e:
        print(f"✓ Blocked: {e.detail}")

    print(f"✓ Allowed: {sanitize_path('uploads/image.jpg')}")
