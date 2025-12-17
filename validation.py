"""
Input Validation Module
Comprehensive validation for all user inputs to prevent security vulnerabilities
Prevents: SSRF, injection attacks, path traversal, malicious file uploads
"""

import re
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
import bleach
from config import settings


class ValidationError(HTTPException):
    """Custom validation error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


# SSRF Prevention: Blocked IP ranges
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),      # Localhost
    ipaddress.ip_network('10.0.0.0/8'),       # Private network
    ipaddress.ip_network('172.16.0.0/12'),    # Private network
    ipaddress.ip_network('192.168.0.0/16'),   # Private network
    ipaddress.ip_network('169.254.0.0/16'),   # Link-local (AWS metadata)
    ipaddress.ip_network('::1/128'),          # IPv6 localhost
    ipaddress.ip_network('fc00::/7'),         # IPv6 private
    ipaddress.ip_network('fe80::/10'),        # IPv6 link-local
]


def is_private_ip(ip_str: str) -> bool:
    """
    Check if IP address is private/internal

    Args:
        ip_str: IP address string

    Returns:
        True if IP is private/internal
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in blocked_range:
                return True
        return False
    except ValueError:
        return False


def validate_image_url(url: str) -> str:
    """
    Validate image URL to prevent SSRF attacks

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        ValidationError: If URL is invalid or potentially malicious
    """
    if not url or not isinstance(url, str):
        raise ValidationError("Image URL is required")

    # Length limit
    if len(url) > 2000:
        raise ValidationError("Image URL too long (max 2000 characters)")

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationError("Invalid URL format")

    # Scheme validation (only http/https)
    if parsed.scheme not in ['http', 'https']:
        raise ValidationError(f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed")

    # Must have a hostname
    if not parsed.hostname:
        raise ValidationError("URL must have a hostname")

    # Check for blocked hostnames
    blocked_hostnames = [
        'localhost',
        '0.0.0.0',
        'metadata.google.internal',  # GCP metadata
        'metadata',
    ]
    hostname_lower = parsed.hostname.lower()
    if hostname_lower in blocked_hostnames:
        raise ValidationError(f"Blocked hostname: {parsed.hostname}")

    # Resolve hostname to IP and check if private
    try:
        ip = socket.gethostbyname(parsed.hostname)
        if is_private_ip(ip):
            raise ValidationError(
                f"Private/internal IP addresses are not allowed: {ip}"
            )
    except socket.gaierror:
        raise ValidationError(f"Could not resolve hostname: {parsed.hostname}")
    except Exception as e:
        raise ValidationError(f"Error validating URL: {str(e)}")

    # Check for suspicious patterns
    suspicious_patterns = [
        r'file://',
        r'ftp://',
        r'gopher://',
        r'dict://',
        r'@',  # Username in URL (suspicious)
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            raise ValidationError(f"Suspicious pattern detected in URL")

    return url


def validate_prompt(prompt: str) -> str:
    """
    Validate and sanitize prompt text

    Args:
        prompt: User-provided prompt

    Returns:
        Sanitized prompt

    Raises:
        ValidationError: If prompt is invalid
    """
    if not prompt or not isinstance(prompt, str):
        raise ValidationError("Prompt is required")

    # Strip whitespace
    prompt = prompt.strip()

    # Length validation
    if len(prompt) < 1:
        raise ValidationError("Prompt cannot be empty")

    if len(prompt) > 2000:
        raise ValidationError("Prompt too long (max 2000 characters)")

    # Remove HTML tags (prevent XSS if prompt is displayed)
    prompt = bleach.clean(prompt, tags=[], strip=True)

    # Check for path traversal attempts
    if '../' in prompt or '..\\'in prompt:
        raise ValidationError("Invalid characters in prompt")

    # Check for null bytes
    if '\x00' in prompt:
        raise ValidationError("Invalid characters in prompt")

    # Basic SQL injection pattern detection (extra safety layer)
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(--|\#|\/\*)',
        r'(\bOR\b.*=.*)',
        r'(\bAND\b.*=.*)',
    ]
    for pattern in sql_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise ValidationError("Suspicious pattern detected in prompt")

    return prompt


def validate_dimensions(width: int, height: int) -> Tuple[int, int]:
    """
    Validate video dimensions

    Args:
        width: Video width in pixels
        height: Video height in pixels

    Returns:
        Tuple of (width, height)

    Raises:
        ValidationError: If dimensions are invalid
    """
    # Type check
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValidationError("Width and height must be integers")

    # Range validation
    if width < 256 or width > settings.MAX_WIDTH:
        raise ValidationError(
            f"Width must be between 256 and {settings.MAX_WIDTH}, got {width}"
        )

    if height < 256 or height > settings.MAX_HEIGHT:
        raise ValidationError(
            f"Height must be between 256 and {settings.MAX_HEIGHT}, got {height}"
        )

    # Must be multiples of 8 (model requirement)
    if width % 8 != 0:
        raise ValidationError(f"Width must be a multiple of 8, got {width}")

    if height % 8 != 0:
        raise ValidationError(f"Height must be a multiple of 8, got {height}")

    # Aspect ratio validation (optional, prevent extreme ratios)
    aspect_ratio = width / height
    if aspect_ratio < 0.5 or aspect_ratio > 3.0:
        raise ValidationError(
            f"Aspect ratio too extreme: {aspect_ratio:.2f}. "
            "Must be between 0.5 and 3.0"
        )

    return width, height


def validate_num_frames(num_frames: int) -> int:
    """
    Validate number of frames

    Args:
        num_frames: Number of frames to generate

    Returns:
        Validated num_frames

    Raises:
        ValidationError: If invalid
    """
    if not isinstance(num_frames, int):
        raise ValidationError("num_frames must be an integer")

    if num_frames < 25 or num_frames > settings.MAX_FRAMES:
        raise ValidationError(
            f"num_frames must be between 25 and {settings.MAX_FRAMES}, "
            f"got {num_frames}"
        )

    # Must be odd for best results with the model
    if num_frames % 2 == 0:
        raise ValidationError(f"num_frames should be odd, got {num_frames}")

    return num_frames


def validate_seed(seed: int) -> int:
    """
    Validate random seed

    Args:
        seed: Random seed value

    Returns:
        Validated seed

    Raises:
        ValidationError: If invalid
    """
    if not isinstance(seed, int):
        raise ValidationError("Seed must be an integer")

    # Valid range for PyTorch/NumPy seeds
    if seed < 0 or seed > 2**32 - 1:
        raise ValidationError(f"Seed must be between 0 and {2**32-1}, got {seed}")

    return seed


def validate_num_steps(num_steps: int) -> int:
    """
    Validate number of inference steps

    Args:
        num_steps: Number of diffusion steps

    Returns:
        Validated num_steps

    Raises:
        ValidationError: If invalid
    """
    if not isinstance(num_steps, int):
        raise ValidationError("num_steps must be an integer")

    if num_steps < 1 or num_steps > settings.MAX_STEPS:
        raise ValidationError(
            f"num_steps must be between 1 and {settings.MAX_STEPS}, "
            f"got {num_steps}"
        )

    return num_steps


async def validate_file_upload(file: UploadFile) -> bool:
    """
    Validate uploaded file for security

    Args:
        file: FastAPI UploadFile object

    Returns:
        True if valid

    Raises:
        ValidationError: If file is invalid or dangerous
    """
    # Check filename exists
    if not file.filename:
        raise ValidationError("No filename provided")

    # File size check (read in chunks to avoid memory issues)
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    total_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    # Reset file position
    await file.seek(0)

    # Read and count size
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size_bytes:
            raise ValidationError(
                f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
            )

    # Reset file position for actual use
    await file.seek(0)

    # MIME type check
    content_type = file.content_type
    allowed_types = settings.get_allowed_image_types()

    if content_type not in allowed_types:
        raise ValidationError(
            f"Invalid file type: {content_type}. "
            f"Allowed: {', '.join(allowed_types)}"
        )

    # Read first bytes to check magic number
    await file.seek(0)
    header = await file.read(12)
    await file.seek(0)

    # Magic number validation (basic)
    valid_magic = False

    # JPEG
    if header[:3] == b'\xff\xd8\xff':
        valid_magic = True

    # PNG
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        valid_magic = True

    # WebP
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        valid_magic = True

    if not valid_magic:
        raise ValidationError(
            "File content does not match declared type (magic number mismatch)"
        )

    # Filename validation (prevent path traversal)
    if '../' in file.filename or '..\\'in file.filename:
        raise ValidationError("Invalid filename")

    if file.filename.startswith('/') or file.filename.startswith('\\'):
        raise ValidationError("Invalid filename")

    # Check for suspicious extensions
    suspicious_extensions = [
        '.exe', '.sh', '.bat', '.cmd', '.com', '.pif', '.scr',
        '.php', '.asp', '.jsp', '.js', '.html', '.htm'
    ]
    filename_lower = file.filename.lower()
    for ext in suspicious_extensions:
        if filename_lower.endswith(ext):
            raise ValidationError(f"Suspicious file extension: {ext}")

    return True


def validate_webhook_url(url: str) -> str:
    """
    Validate webhook URL

    Args:
        url: Webhook URL

    Returns:
        Validated URL

    Raises:
        ValidationError: If invalid
    """
    if not url:
        return None

    # Use same validation as image URL (prevent SSRF to webhooks too)
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationError("Invalid webhook URL format")

    # Must use https in production
    if parsed.scheme not in ['http', 'https']:
        raise ValidationError("Webhook URL must use http or https")

    # Resolve and check IP
    try:
        ip = socket.gethostbyname(parsed.hostname)
        if is_private_ip(ip):
            raise ValidationError(
                "Webhook URL cannot point to private/internal IP addresses"
            )
    except socket.gaierror:
        raise ValidationError(f"Could not resolve webhook hostname: {parsed.hostname}")

    return url


# Helper function to validate all generation parameters at once
def validate_generation_params(
    image_url: str,
    prompt: str,
    width: int = None,
    height: int = None,
    num_frames: int = None,
    num_steps: int = None,
    seed: int = None,
    webhook_url: str = None
) -> dict:
    """
    Validate all generation parameters

    Returns:
        Dictionary of validated parameters with defaults applied
    """
    # Apply defaults
    width = width if width is not None else settings.DEFAULT_WIDTH
    height = height if height is not None else settings.DEFAULT_HEIGHT
    num_frames = num_frames if num_frames is not None else settings.DEFAULT_NUM_FRAMES
    num_steps = num_steps if num_steps is not None else settings.DEFAULT_NUM_STEPS
    seed = seed if seed is not None else 42

    # Validate each parameter
    validated = {
        'image_url': validate_image_url(image_url),
        'prompt': validate_prompt(prompt),
        'width': validate_dimensions(width, height)[0],
        'height': validate_dimensions(width, height)[1],
        'num_frames': validate_num_frames(num_frames),
        'num_steps': validate_num_steps(num_steps),
        'seed': validate_seed(seed),
    }

    # Optional webhook URL
    if webhook_url:
        validated['webhook_url'] = validate_webhook_url(webhook_url)
    else:
        validated['webhook_url'] = None

    return validated
