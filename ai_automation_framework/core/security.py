"""
Security utilities for the AI Automation Framework.

Provides secure HTTP client configuration, API key handling,
and secret management utilities.
"""

import os
import re
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from functools import wraps
import logging

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import certifi
    HAS_CERTIFI = True
except ImportError:
    HAS_CERTIFI = False


logger = logging.getLogger(__name__)


class SecureConfigError(Exception):
    """Raised when there's a security configuration error."""
    pass


class APIKeyValidationError(Exception):
    """Raised when API key validation fails."""
    pass


class SecureConfig:
    """
    Secure configuration management for sensitive values.

    Handles API keys, secrets, and environment variables securely.
    """

    # Known API key patterns for validation
    API_KEY_PATTERNS = {
        'openai': r'^sk-[a-zA-Z0-9]{48,}$',
        'anthropic': r'^sk-ant-[a-zA-Z0-9-]{40,}$',
        'github': r'^gh[ps]_[a-zA-Z0-9]{36,}$',
        'aws_access_key': r'^AKIA[0-9A-Z]{16}$',
    }

    # Minimum key lengths for generic validation
    MIN_KEY_LENGTHS = {
        'default': 20,
        'openai': 51,
        'anthropic': 50,
        'github': 40,
        'aws': 20,
    }

    @classmethod
    def get_secret(
        cls,
        key: str,
        required: bool = True,
        default: Optional[str] = None,
        validate_format: bool = True,
        key_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Securely retrieve a secret from environment variables.

        Args:
            key: Environment variable name
            required: Whether the secret is required
            default: Default value if not found and not required
            validate_format: Whether to validate the key format
            key_type: Type of key for format validation (e.g., 'openai', 'anthropic')

        Returns:
            The secret value or None

        Raises:
            SecureConfigError: If required secret is missing or invalid
        """
        value = os.environ.get(key)

        if value is None:
            if required:
                raise SecureConfigError(f"Required secret '{key}' not found in environment")
            return default

        # Strip whitespace
        value = value.strip()

        if not value:
            if required:
                raise SecureConfigError(f"Required secret '{key}' is empty")
            return default

        # Validate format if requested
        if validate_format and key_type:
            cls._validate_key_format(value, key_type, key)
        elif validate_format:
            # Try to detect key type from env var name
            detected_type = cls._detect_key_type(key)
            if detected_type:
                cls._validate_key_format(value, detected_type, key)

        return value

    @classmethod
    def _detect_key_type(cls, key_name: str) -> Optional[str]:
        """Detect key type from environment variable name."""
        key_lower = key_name.lower()

        if 'openai' in key_lower:
            return 'openai'
        elif 'anthropic' in key_lower or 'claude' in key_lower:
            return 'anthropic'
        elif 'github' in key_lower:
            return 'github'
        elif 'aws' in key_lower and 'access' in key_lower:
            return 'aws_access_key'

        return None

    @classmethod
    def _validate_key_format(cls, value: str, key_type: str, key_name: str) -> None:
        """Validate API key format."""
        # Check minimum length
        min_length = cls.MIN_KEY_LENGTHS.get(key_type, cls.MIN_KEY_LENGTHS['default'])
        if len(value) < min_length:
            raise APIKeyValidationError(
                f"API key '{key_name}' appears too short "
                f"(expected at least {min_length} characters)"
            )

        # Check pattern if available
        pattern = cls.API_KEY_PATTERNS.get(key_type)
        if pattern and not re.match(pattern, value):
            logger.warning(
                f"API key '{key_name}' does not match expected pattern for '{key_type}'. "
                "This may be intentional for custom or newer key formats."
            )

    @staticmethod
    def mask_secret(value: str, visible_chars: int = 4, mask_char: str = '*') -> str:
        """
        Mask a secret for safe logging or display.

        Args:
            value: The secret value to mask
            visible_chars: Number of characters to show at start and end
            mask_char: Character to use for masking

        Returns:
            Masked string (e.g., "sk-a****xyz")
        """
        if not value:
            return ''

        if len(value) <= visible_chars * 2:
            return mask_char * len(value)

        return f"{value[:visible_chars]}{mask_char * 4}{value[-visible_chars:]}"

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_value(value: str, salt: Optional[str] = None) -> str:
        """
        Create a secure hash of a value.

        Args:
            value: The value to hash
            salt: Optional salt for the hash

        Returns:
            Hexadecimal hash string
        """
        if salt:
            value = f"{salt}{value}"
        return hashlib.sha256(value.encode()).hexdigest()


class SecureHTTPClient:
    """
    Secure HTTP client with HTTPS enforcement and best practices.
    """

    def __init__(
        self,
        enforce_https: bool = True,
        verify_ssl: bool = True,
        max_retries: int = 3,
        timeout: int = 30,
        user_agent: str = "AI-Automation-Framework/1.0"
    ):
        """
        Initialize secure HTTP client.

        Args:
            enforce_https: Whether to enforce HTTPS connections
            verify_ssl: Whether to verify SSL certificates
            max_retries: Maximum number of retries for failed requests
            timeout: Default timeout in seconds
            user_agent: User-Agent header value
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for SecureHTTPClient")

        self.enforce_https = enforce_https
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = self._create_session(max_retries, user_agent)

    def _create_session(self, max_retries: int, user_agent: str) -> 'requests.Session':
        """Create a configured requests session."""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        if not self.enforce_https:
            session.mount("http://", adapter)

        # Set default headers
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json',
        })

        # Set SSL verification
        if self.verify_ssl and HAS_CERTIFI:
            session.verify = certifi.where()
        else:
            session.verify = self.verify_ssl

        return session

    def _validate_url(self, url: str) -> str:
        """Validate and potentially upgrade URL to HTTPS."""
        if self.enforce_https:
            if url.startswith('http://'):
                https_url = url.replace('http://', 'https://', 1)
                logger.warning(
                    f"Upgrading insecure HTTP URL to HTTPS: {url} -> {https_url}"
                )
                return https_url
            elif not url.startswith('https://'):
                raise SecureConfigError(
                    f"Invalid URL scheme. HTTPS is required: {url}"
                )
        return url

    def get(self, url: str, **kwargs) -> 'requests.Response':
        """Make a secure GET request."""
        url = self._validate_url(url)
        kwargs.setdefault('timeout', self.timeout)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> 'requests.Response':
        """Make a secure POST request."""
        url = self._validate_url(url)
        kwargs.setdefault('timeout', self.timeout)
        return self.session.post(url, **kwargs)

    def put(self, url: str, **kwargs) -> 'requests.Response':
        """Make a secure PUT request."""
        url = self._validate_url(url)
        kwargs.setdefault('timeout', self.timeout)
        return self.session.put(url, **kwargs)

    def delete(self, url: str, **kwargs) -> 'requests.Response':
        """Make a secure DELETE request."""
        url = self._validate_url(url)
        kwargs.setdefault('timeout', self.timeout)
        return self.session.delete(url, **kwargs)

    def request(self, method: str, url: str, **kwargs) -> 'requests.Response':
        """Make a secure request with any method."""
        url = self._validate_url(url)
        kwargs.setdefault('timeout', self.timeout)
        return self.session.request(method, url, **kwargs)

    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()


def require_api_key(key_name: str, key_type: Optional[str] = None):
    """
    Decorator to require an API key for a function.

    Args:
        key_name: Environment variable name for the API key
        key_type: Type of key for validation (e.g., 'openai', 'anthropic')

    Example:
        @require_api_key('OPENAI_API_KEY', 'openai')
        def call_openai_api(api_key: str, prompt: str):
            # api_key will be injected
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_key = SecureConfig.get_secret(
                key_name,
                required=True,
                key_type=key_type
            )
            return func(api_key, *args, **kwargs)
        return wrapper
    return decorator


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to remove sensitive information.

    Args:
        error: The exception to sanitize

    Returns:
        Sanitized error message
    """
    message = str(error)

    # Patterns that might contain sensitive data
    sensitive_patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_API_KEY]'),
        (r'Bearer\s+[a-zA-Z0-9_-]+', 'Bearer [REDACTED]'),
        (r'api[_-]?key[=:]\s*["\']?[a-zA-Z0-9_-]+["\']?', 'api_key=[REDACTED]'),
        (r'password[=:]\s*["\']?[^\s"\']+["\']?', 'password=[REDACTED]'),
        (r'token[=:]\s*["\']?[a-zA-Z0-9_.-]+["\']?', 'token=[REDACTED]'),
        (r'secret[=:]\s*["\']?[^\s"\']+["\']?', 'secret=[REDACTED]'),
    ]

    for pattern, replacement in sensitive_patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

    return message


# Export all public classes and functions
__all__ = [
    'SecureConfig',
    'SecureHTTPClient',
    'SecureConfigError',
    'APIKeyValidationError',
    'require_api_key',
    'sanitize_error_message',
]
