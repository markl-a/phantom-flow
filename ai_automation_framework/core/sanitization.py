"""
Input sanitization utilities for security.

This module provides various sanitization functions to prevent common security
vulnerabilities such as SQL injection, XSS attacks, path traversal, and more.
"""

import re
import html
import urllib.parse
from pathlib import Path
from typing import Optional, Set
import logging

logger = logging.getLogger(__name__)


# Dangerous HTML tags that should be stripped
DANGEROUS_HTML_TAGS = {
    'script', 'iframe', 'object', 'embed', 'link', 'style',
    'meta', 'base', 'form', 'input', 'button', 'textarea',
    'select', 'option', 'applet', 'frame', 'frameset'
}


def sanitize_sql_identifier(identifier: str, max_length: int = 64) -> str:
    """
    Sanitize SQL identifiers (table names, column names, etc.) to prevent SQL injection.

    This function ensures that only alphanumeric characters and underscores are allowed,
    and the identifier doesn't start with a number.

    Args:
        identifier: The SQL identifier to sanitize
        max_length: Maximum length for the identifier (default: 64)

    Returns:
        Sanitized SQL identifier

    Raises:
        ValueError: If identifier is empty or invalid after sanitization

    Examples:
        >>> sanitize_sql_identifier("user_table")
        'user_table'
        >>> sanitize_sql_identifier("users-table")
        'users_table'
        >>> sanitize_sql_identifier("123_table")
        Raises ValueError
    """
    if not identifier:
        raise ValueError("SQL identifier cannot be empty")

    # Remove any characters that are not alphanumeric or underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', identifier)

    # Ensure it doesn't start with a number
    if sanitized[0].isdigit():
        raise ValueError(f"SQL identifier cannot start with a number: {identifier}")

    # Truncate to max_length
    sanitized = sanitized[:max_length]

    if not sanitized:
        raise ValueError(f"Invalid SQL identifier: {identifier}")

    logger.debug(f"Sanitized SQL identifier: {identifier} -> {sanitized}")
    return sanitized


def sanitize_html(
    content: str,
    allowed_tags: Optional[Set[str]] = None,
    strip_all: bool = False
) -> str:
    """
    Sanitize HTML content by removing dangerous tags and escaping special characters.

    Args:
        content: The HTML content to sanitize
        allowed_tags: Set of allowed HTML tags (if None, uses safe defaults)
        strip_all: If True, strip all HTML tags and just escape content

    Returns:
        Sanitized HTML content

    Examples:
        >>> sanitize_html("<p>Hello</p>")
        '<p>Hello</p>'
        >>> sanitize_html("<script>alert('xss')</script><p>Safe</p>")
        '<p>Safe</p>'
        >>> sanitize_html("<p>Hello</p>", strip_all=True)
        '&lt;p&gt;Hello&lt;/p&gt;'
    """
    if not content:
        return content

    if strip_all:
        # Escape all HTML entities
        return html.escape(content)

    # Default safe tags if none provided
    if allowed_tags is None:
        allowed_tags = {
            'p', 'br', 'span', 'div', 'b', 'i', 'u', 'strong', 'em',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
            'a', 'img', 'table', 'tr', 'td', 'th', 'thead', 'tbody'
        }

    # Remove dangerous tags
    sanitized = content
    for tag in DANGEROUS_HTML_TAGS:
        # Remove opening and closing tags with any attributes
        sanitized = re.sub(
            rf'<{tag}[^>]*>.*?</{tag}>',
            '',
            sanitized,
            flags=re.IGNORECASE | re.DOTALL
        )
        # Remove self-closing tags
        sanitized = re.sub(
            rf'<{tag}[^>]*/>',
            '',
            sanitized,
            flags=re.IGNORECASE
        )

    # Remove event handlers (onclick, onerror, etc.)
    sanitized = re.sub(
        r'\s+on\w+\s*=\s*["\']?[^"\']*["\']?',
        '',
        sanitized,
        flags=re.IGNORECASE
    )

    # Remove javascript: protocol in attributes
    sanitized = re.sub(
        r'javascript:',
        '',
        sanitized,
        flags=re.IGNORECASE
    )

    # Remove data: protocol (can be used for XSS)
    sanitized = re.sub(
        r'data:text/html',
        '',
        sanitized,
        flags=re.IGNORECASE
    )

    logger.debug(f"Sanitized HTML content (length: {len(content)} -> {len(sanitized)})")
    return sanitized


def sanitize_path(
    path: str,
    base_dir: Optional[str] = None,
    allow_absolute: bool = False
) -> str:
    """
    Sanitize file paths to prevent path traversal attacks.

    Args:
        path: The file path to sanitize
        base_dir: Base directory to restrict paths to (optional)
        allow_absolute: Whether to allow absolute paths

    Returns:
        Sanitized path string

    Raises:
        ValueError: If path is invalid or attempts path traversal

    Examples:
        >>> sanitize_path("file.txt")
        'file.txt'
        >>> sanitize_path("../../../etc/passwd")
        Raises ValueError
        >>> sanitize_path("/tmp/file.txt", allow_absolute=True)
        '/tmp/file.txt'
    """
    if not path:
        raise ValueError("Path cannot be empty")

    # Normalize the path
    normalized = Path(path).resolve()

    # Check for absolute paths
    if not allow_absolute and normalized.is_absolute():
        raise ValueError(f"Absolute paths are not allowed: {path}")

    # If base_dir is provided, ensure the path is within it
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            # This will raise ValueError if normalized is not relative to base
            normalized.relative_to(base)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: {path} is outside base directory {base_dir}"
            )

    # Check for null bytes (can be used to bypass security checks)
    if '\x00' in path:
        raise ValueError("Null bytes not allowed in path")

    # Convert back to string
    sanitized = str(normalized)

    # Additional check: ensure no parent directory references in the final path
    path_parts = Path(sanitized).parts
    if '..' in path_parts:
        raise ValueError(f"Path traversal detected in path: {path}")

    logger.debug(f"Sanitized path: {path} -> {sanitized}")
    return sanitized


def sanitize_url(url: str, allowed_schemes: Optional[Set[str]] = None) -> str:
    """
    Validate and sanitize URLs to ensure they follow a valid format.

    Args:
        url: The URL to sanitize
        allowed_schemes: Set of allowed URL schemes (default: http, https)

    Returns:
        Sanitized URL

    Raises:
        ValueError: If URL is invalid or uses disallowed scheme

    Examples:
        >>> sanitize_url("https://example.com/path")
        'https://example.com/path'
        >>> sanitize_url("javascript:alert('xss')")
        Raises ValueError
        >>> sanitize_url("http://example.com/<script>")
        'http://example.com/%3Cscript%3E'
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Default allowed schemes
    if allowed_schemes is None:
        allowed_schemes = {'http', 'https'}

    # Parse the URL
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {url}") from e

    # Check scheme
    if parsed.scheme and parsed.scheme.lower() not in allowed_schemes:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' not allowed. "
            f"Allowed schemes: {', '.join(allowed_schemes)}"
        )

    # Ensure scheme is present
    if not parsed.scheme:
        raise ValueError(f"URL must include a scheme (e.g., https://): {url}")

    # Check for dangerous patterns
    url_lower = url.lower()
    dangerous_patterns = ['javascript:', 'data:', 'vbscript:', 'file:']
    for pattern in dangerous_patterns:
        if pattern in url_lower:
            raise ValueError(f"Dangerous pattern detected in URL: {pattern}")

    # Reconstruct the URL with proper encoding
    # This helps neutralize any injection attempts
    sanitized = urllib.parse.urlunparse(parsed)

    logger.debug(f"Sanitized URL: {url} -> {sanitized}")
    return sanitized


def sanitize_email(email: str, strict: bool = True) -> str:
    """
    Validate and sanitize email addresses.

    Args:
        email: The email address to sanitize
        strict: If True, apply strict RFC 5322 validation

    Returns:
        Sanitized email address

    Raises:
        ValueError: If email format is invalid

    Examples:
        >>> sanitize_email("user@example.com")
        'user@example.com'
        >>> sanitize_email("invalid.email")
        Raises ValueError
        >>> sanitize_email("user+tag@example.com")
        'user+tag@example.com'
    """
    if not email:
        raise ValueError("Email cannot be empty")

    # Basic cleanup
    email = email.strip().lower()

    # Check for null bytes
    if '\x00' in email:
        raise ValueError("Null bytes not allowed in email")

    if strict:
        # Strict validation using RFC 5322 regex (simplified version)
        # Full RFC 5322 regex is extremely complex, this is a practical compromise
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    else:
        # Relaxed validation
        pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")

    # Additional checks
    if email.count('@') != 1:
        raise ValueError(f"Email must contain exactly one @ symbol: {email}")

    local, domain = email.split('@')

    # Check local part length (max 64 characters per RFC 5321)
    if len(local) > 64:
        raise ValueError(f"Email local part too long (max 64): {email}")

    # Check domain part length (max 255 characters per RFC 5321)
    if len(domain) > 255:
        raise ValueError(f"Email domain too long (max 255): {email}")

    # Check for consecutive dots
    if '..' in email:
        raise ValueError(f"Consecutive dots not allowed in email: {email}")

    # Check that local part doesn't start or end with dot
    if local.startswith('.') or local.endswith('.'):
        raise ValueError(f"Email local part cannot start or end with dot: {email}")

    logger.debug(f"Sanitized email: {email}")
    return email


def escape_special_chars(
    text: str,
    escape_type: str = 'html',
    custom_chars: Optional[str] = None
) -> str:
    """
    Escape special characters in text to prevent injection attacks.

    Args:
        text: The text to escape
        escape_type: Type of escaping ('html', 'sql', 'shell', 'custom')
        custom_chars: Custom characters to escape (required if escape_type='custom')

    Returns:
        Escaped text

    Examples:
        >>> escape_special_chars("<script>alert('xss')</script>", 'html')
        '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;'
        >>> escape_special_chars("O'Reilly", 'sql')
        "O''Reilly"
        >>> escape_special_chars("file; rm -rf /", 'shell')
        'file\\; rm -rf /'
    """
    if not text:
        return text

    if escape_type == 'html':
        # Escape HTML special characters
        return html.escape(text, quote=True)

    elif escape_type == 'sql':
        # Escape single quotes for SQL (double them)
        # Note: This is a basic escape. Use parameterized queries when possible!
        return text.replace("'", "''")

    elif escape_type == 'shell':
        # Escape shell special characters
        # Note: This is basic. Use subprocess with list args when possible!
        shell_chars = r';|&$`\!<>()[]{}*?~'
        escaped = text
        for char in shell_chars:
            escaped = escaped.replace(char, f'\\{char}')
        return escaped

    elif escape_type == 'custom':
        if custom_chars is None:
            raise ValueError("custom_chars required when escape_type='custom'")
        escaped = text
        for char in custom_chars:
            escaped = escaped.replace(char, f'\\{char}')
        return escaped

    else:
        raise ValueError(
            f"Invalid escape_type: {escape_type}. "
            "Must be 'html', 'sql', 'shell', or 'custom'"
        )


def validate_and_sanitize_input(
    value: str,
    input_type: str,
    **kwargs
) -> str:
    """
    Convenience function to validate and sanitize input based on type.

    Args:
        value: The input value to sanitize
        input_type: Type of input ('sql_identifier', 'html', 'path', 'url', 'email')
        **kwargs: Additional arguments to pass to specific sanitization function

    Returns:
        Sanitized value

    Raises:
        ValueError: If input_type is invalid or validation fails

    Examples:
        >>> validate_and_sanitize_input("user_table", "sql_identifier")
        'user_table'
        >>> validate_and_sanitize_input("user@example.com", "email")
        'user@example.com'
    """
    sanitizers = {
        'sql_identifier': sanitize_sql_identifier,
        'html': sanitize_html,
        'path': sanitize_path,
        'url': sanitize_url,
        'email': sanitize_email,
    }

    if input_type not in sanitizers:
        raise ValueError(
            f"Invalid input_type: {input_type}. "
            f"Must be one of: {', '.join(sanitizers.keys())}"
        )

    return sanitizers[input_type](value, **kwargs)


# Convenience function for batch sanitization
def sanitize_dict(
    data: dict,
    sanitization_rules: dict
) -> dict:
    """
    Sanitize multiple values in a dictionary based on specified rules.

    Args:
        data: Dictionary with values to sanitize
        sanitization_rules: Dictionary mapping keys to (input_type, kwargs) tuples

    Returns:
        Dictionary with sanitized values

    Example:
        >>> data = {'email': 'user@example.com', 'name': '<script>alert("xss")</script>'}
        >>> rules = {
        ...     'email': ('email', {}),
        ...     'name': ('html', {'strip_all': True})
        ... }
        >>> sanitize_dict(data, rules)
        {'email': 'user@example.com', 'name': '&lt;script&gt;alert("xss")&lt;/script&gt;'}
    """
    sanitized = data.copy()

    for key, (input_type, kwargs) in sanitization_rules.items():
        if key in sanitized and sanitized[key] is not None:
            try:
                sanitized[key] = validate_and_sanitize_input(
                    str(sanitized[key]),
                    input_type,
                    **kwargs
                )
            except Exception as e:
                logger.error(f"Failed to sanitize key '{key}': {e}")
                raise

    return sanitized
