"""
API Key Authentication and Rate Limiting Middleware
Provides secure authentication and rate limiting for FastAPI endpoints
"""

import hashlib
import hmac
from fastapi import Header, HTTPException, status
from datetime import datetime
from typing import Optional
from config import settings


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class RateLimitError(HTTPException):
    """Custom rate limit error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "60"},
        )


def hash_api_key(api_key: str) -> str:
    """
    Hash API key using SHA-256 for database storage and comparison

    Args:
        api_key: Plain text API key

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def constant_time_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks

    Args:
        a: First string
        b: Second string

    Returns:
        True if strings match, False otherwise
    """
    return hmac.compare_digest(a, b)


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate API key format (basic checks)

    Args:
        api_key: API key to validate

    Returns:
        True if format is valid
    """
    if not api_key:
        return False

    # Minimum length
    if len(api_key) < 16:
        return False

    # Must be alphanumeric or URL-safe characters
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed_chars for c in api_key):
        return False

    return True


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, description="API Key for authentication")
) -> str:
    """
    FastAPI dependency for API key authentication

    Validates API key from X-API-Key header and returns hashed key
    for use in database queries

    Args:
        x_api_key: API key from request header

    Returns:
        SHA-256 hash of the valid API key

    Raises:
        AuthenticationError: If API key is missing, invalid, or not authorized
    """

    # Check if API key is provided
    if not x_api_key:
        raise AuthenticationError("Missing API key. Include 'X-API-Key' header.")

    # Validate format
    if not validate_api_key_format(x_api_key):
        raise AuthenticationError("Invalid API key format")

    # Hash the provided key
    key_hash = hash_api_key(x_api_key)

    # Get configured API keys
    configured_keys = settings.get_api_key_list()

    # Hash configured keys and compare
    valid = False
    for configured_key in configured_keys:
        configured_hash = hash_api_key(configured_key)
        if constant_time_compare(key_hash, configured_hash):
            valid = True
            break

    if not valid:
        # Don't log the actual key, just a prefix for debugging
        print(f"Authentication failed for key: {x_api_key[:4]}...")
        raise AuthenticationError("Invalid API key")

    # Return the hash for use in database queries
    return key_hash


async def verify_api_key_with_rate_limit(
    x_api_key: Optional[str] = Header(None),
    endpoint: str = "unknown"
) -> str:
    """
    FastAPI dependency for API key authentication with rate limiting

    This version checks rate limits in the database before allowing the request.
    Use this for endpoints that should be rate-limited.

    Args:
        x_api_key: API key from request header
        endpoint: Endpoint name for rate limit tracking

    Returns:
        SHA-256 hash of the valid API key

    Raises:
        AuthenticationError: If authentication fails
        RateLimitError: If rate limit is exceeded

    Note:
        Requires database connection to check rate limits.
        For serverless handler, rate limiting is done in database.py
    """

    # First, verify the API key
    key_hash = await verify_api_key(x_api_key)

    # Rate limiting will be checked in the endpoint using database
    # This is a placeholder for the dependency injection pattern

    return key_hash


# Simple in-memory rate limiter for testing/development
# (Production should use database-backed rate limiting)
class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter for development/testing
    Not suitable for production (doesn't persist across restarts or scale)
    """

    def __init__(self):
        self._requests = {}  # {key_hash: [timestamps]}

    def check_rate_limit(self, key_hash: str, limit: int = None) -> bool:
        """
        Check if request is within rate limit

        Args:
            key_hash: Hashed API key
            limit: Requests per minute (defaults to config value)

        Returns:
            True if within limit, False if exceeded
        """
        if limit is None:
            limit = settings.RATE_LIMIT_PER_MINUTE

        now = datetime.utcnow()

        # Initialize if key not seen before
        if key_hash not in self._requests:
            self._requests[key_hash] = []

        # Remove requests older than 1 minute
        self._requests[key_hash] = [
            ts for ts in self._requests[key_hash]
            if (now - ts).total_seconds() < 60
        ]

        # Check if limit exceeded
        if len(self._requests[key_hash]) >= limit:
            return False

        # Add current request
        self._requests[key_hash].append(now)
        return True

    def get_request_count(self, key_hash: str) -> int:
        """Get current request count for key in last minute"""
        now = datetime.utcnow()
        if key_hash not in self._requests:
            return 0

        # Count requests in last minute
        recent = [
            ts for ts in self._requests[key_hash]
            if (now - ts).total_seconds() < 60
        ]
        return len(recent)


# Global rate limiter instance for development
_dev_rate_limiter = InMemoryRateLimiter()


def check_rate_limit_dev(key_hash: str) -> bool:
    """
    Development/testing rate limit check

    Args:
        key_hash: Hashed API key

    Returns:
        True if within limit

    Raises:
        RateLimitError: If rate limit exceeded
    """
    if not _dev_rate_limiter.check_rate_limit(key_hash):
        count = _dev_rate_limiter.get_request_count(key_hash)
        raise RateLimitError(
            f"Rate limit exceeded. {count} requests in last minute. "
            f"Limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute"
        )
    return True


# Helper function to generate secure API keys
def generate_api_key() -> str:
    """
    Generate a secure random API key

    Returns:
        URL-safe random string (32 bytes = 43 characters)
    """
    import secrets
    return secrets.token_urlsafe(32)


if __name__ == "__main__":
    # Generate example API keys
    print("Example API Keys:")
    for i in range(3):
        key = generate_api_key()
        print(f"  {i+1}. {key}")

    print("\nAdd these to your .env file as:")
    print("API_KEYS=key1,key2,key3")
