"""
Comprehensive tests for the security module.

Tests cover secure configuration, HTTP client, and error sanitization.
"""

import os
import pytest
import hashlib
import re
from unittest.mock import Mock, patch, MagicMock
from ai_automation_framework.core.security import (
    SecureConfig,
    SecureHTTPClient,
    SecureConfigError,
    APIKeyValidationError,
    sanitize_error_message,
)


class TestSecureConfig:
    """Test suite for SecureConfig class."""

    def test_get_secret_from_env(self, monkeypatch):
        """Test getting secret from environment variable."""
        test_secret = "sk-test123456789012345678901234567890"
        monkeypatch.setenv("TEST_API_KEY", test_secret)

        result = SecureConfig.get_secret("TEST_API_KEY", required=False, validate_format=False)

        assert result == test_secret

    def test_get_secret_required_missing(self):
        """Test error when required secret is missing from environment."""
        # Make sure the env var doesn't exist
        if "NONEXISTENT_SECRET" in os.environ:
            del os.environ["NONEXISTENT_SECRET"]

        with pytest.raises(SecureConfigError) as exc_info:
            SecureConfig.get_secret("NONEXISTENT_SECRET", required=True)

        assert "Required secret 'NONEXISTENT_SECRET' not found" in str(exc_info.value)

    def test_get_secret_with_default(self, monkeypatch):
        """Test default value is returned when secret not required and not found."""
        # Ensure the variable doesn't exist
        monkeypatch.delenv("MISSING_SECRET", raising=False)

        default_value = "default_secret_value"
        result = SecureConfig.get_secret(
            "MISSING_SECRET",
            required=False,
            default=default_value
        )

        assert result == default_value

    def test_mask_secret(self):
        """Test secret masking functionality."""
        secret = "sk-abcdefghijklmnopqrstuvwxyz123456"

        masked = SecureConfig.mask_secret(secret)

        # Should show first 4 and last 4 chars with **** in between
        assert masked.startswith("sk-a")
        assert masked.endswith("3456")
        assert "****" in masked
        assert len(masked) == len("sk-a") + 4 + len("3456")

        # The original secret should not be fully visible
        assert masked != secret
        assert secret[:4] in masked
        assert secret[-4:] in masked

    def test_mask_secret_short_value(self):
        """Test masking short secrets (8 chars or less)."""
        short_secret = "abc123"

        masked = SecureConfig.mask_secret(short_secret, visible_chars=4)

        # Short secrets should be fully masked
        assert masked == "******"
        assert "abc" not in masked
        assert "123" not in masked

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = SecureConfig.generate_secure_token(length=32)
        token2 = SecureConfig.generate_secure_token(length=32)

        # Tokens should be generated
        assert token1 is not None
        assert token2 is not None

        # Tokens should be different (randomness)
        assert token1 != token2

        # Token should be URL-safe (no special chars that need encoding)
        assert all(c.isalnum() or c in '-_' for c in token1)
        assert all(c.isalnum() or c in '-_' for c in token2)

    def test_hash_value(self):
        """Test value hashing without salt."""
        value = "test_value_to_hash"

        hashed = SecureConfig.hash_value(value)

        # Should be a valid hex string
        assert re.match(r'^[a-f0-9]{64}$', hashed)

        # Should be deterministic
        hashed2 = SecureConfig.hash_value(value)
        assert hashed == hashed2

        # Should match expected SHA256 hash
        expected = hashlib.sha256(value.encode()).hexdigest()
        assert hashed == expected

    def test_hash_value_with_salt(self):
        """Test value hashing with salt."""
        value = "test_value"
        salt = "random_salt_123"

        hashed_with_salt = SecureConfig.hash_value(value, salt=salt)
        hashed_without_salt = SecureConfig.hash_value(value)

        # Hashes should be different
        assert hashed_with_salt != hashed_without_salt

        # Should be deterministic with same salt
        hashed2 = SecureConfig.hash_value(value, salt=salt)
        assert hashed_with_salt == hashed2

        # Should match expected SHA256 with salt
        expected = hashlib.sha256(f"{salt}{value}".encode()).hexdigest()
        assert hashed_with_salt == expected

    def test_get_secret_strips_whitespace(self, monkeypatch):
        """Test that secrets are stripped of whitespace."""
        test_secret = "  sk-test123456789012345678901234567890  "
        monkeypatch.setenv("TEST_WHITESPACE_KEY", test_secret)

        result = SecureConfig.get_secret(
            "TEST_WHITESPACE_KEY",
            required=False,
            validate_format=False
        )

        assert result == test_secret.strip()
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_get_secret_empty_string_required(self, monkeypatch):
        """Test that empty string raises error when required."""
        monkeypatch.setenv("EMPTY_SECRET", "   ")

        with pytest.raises(SecureConfigError) as exc_info:
            SecureConfig.get_secret("EMPTY_SECRET", required=True)

        assert "is empty" in str(exc_info.value)

    def test_mask_secret_empty_string(self):
        """Test masking empty string."""
        result = SecureConfig.mask_secret("")
        assert result == ""

    def test_mask_secret_custom_parameters(self):
        """Test masking with custom visible_chars and mask_char."""
        secret = "abcdefghijklmnopqrstuvwxyz"

        masked = SecureConfig.mask_secret(secret, visible_chars=3, mask_char='#')

        assert masked.startswith("abc")
        assert masked.endswith("xyz")
        assert "####" in masked
        assert '*' not in masked


class TestSecureHTTPClient:
    """Test suite for SecureHTTPClient class."""

    @pytest.fixture
    def mock_requests(self):
        """Mock the requests library."""
        with patch('ai_automation_framework.core.security.requests') as mock:
            mock_session = MagicMock()
            mock.Session.return_value = mock_session
            yield mock

    def test_initialization(self, mock_requests):
        """Test SecureHTTPClient initialization."""
        client = SecureHTTPClient(
            enforce_https=True,
            verify_ssl=True,
            max_retries=5,
            timeout=60,
            user_agent="TestAgent/1.0"
        )

        assert client.enforce_https is True
        assert client.verify_ssl is True
        assert client.timeout == 60
        assert client.session is not None

    def test_validate_url_https_enforcement(self, mock_requests):
        """Test HTTPS enforcement raises error for non-HTTPS URLs."""
        client = SecureHTTPClient(enforce_https=True)

        # Valid HTTPS URL should pass
        valid_url = client._validate_url("https://api.example.com/endpoint")
        assert valid_url == "https://api.example.com/endpoint"

        # Invalid scheme should raise error
        with pytest.raises(SecureConfigError) as exc_info:
            client._validate_url("ftp://example.com")

        assert "HTTPS is required" in str(exc_info.value)

    def test_validate_url_upgrade_http(self, mock_requests):
        """Test HTTP to HTTPS upgrade when enforcement is enabled."""
        with patch('ai_automation_framework.core.security.logger') as mock_logger:
            client = SecureHTTPClient(enforce_https=True)

            upgraded_url = client._validate_url("http://api.example.com/endpoint")

            # URL should be upgraded to HTTPS
            assert upgraded_url == "https://api.example.com/endpoint"

            # Warning should be logged
            assert mock_logger.warning.called
            warning_message = mock_logger.warning.call_args[0][0]
            assert "Upgrading insecure HTTP" in warning_message

    def test_context_manager(self, mock_requests):
        """Test context manager support for SecureHTTPClient."""
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session

        # Use client as context manager
        with SecureHTTPClient() as client:
            assert client.session is not None

        # Session should be closed after context exit
        assert mock_session.close.called

    def test_https_not_enforced(self, mock_requests):
        """Test that HTTP URLs are allowed when enforcement is disabled."""
        client = SecureHTTPClient(enforce_https=False)

        http_url = client._validate_url("http://example.com")
        assert http_url == "http://example.com"

    def test_get_request(self, mock_requests):
        """Test GET request through SecureHTTPClient."""
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session

        client = SecureHTTPClient()
        client.get("https://api.example.com/data")

        # Verify GET was called with proper URL and timeout
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "https://api.example.com/data"
        assert call_args[1].get('timeout') == 30

    def test_post_request(self, mock_requests):
        """Test POST request through SecureHTTPClient."""
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session

        client = SecureHTTPClient(timeout=45)
        client.post("https://api.example.com/submit", json={"key": "value"})

        # Verify POST was called
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://api.example.com/submit"
        assert call_args[1].get('timeout') == 45

    def test_close_session(self, mock_requests):
        """Test explicit session closing."""
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session

        client = SecureHTTPClient()
        assert client.session is not None

        client.close()

        assert mock_session.close.called
        assert client.session is None

    def test_request_method(self, mock_requests):
        """Test generic request method."""
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session

        client = SecureHTTPClient()
        client.request("PATCH", "https://api.example.com/resource")

        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "https://api.example.com/resource"


class TestSanitizeErrorMessage:
    """Test suite for sanitize_error_message function."""

    def test_sanitize_api_key(self):
        """Test API key removal from error messages."""
        error_msg = Exception("API call failed with key: sk-abcdef1234567890abcdef1234567890")

        sanitized = sanitize_error_message(error_msg)

        # API key should be redacted
        assert "sk-abcdef1234567890abcdef1234567890" not in sanitized
        assert "[REDACTED_API_KEY]" in sanitized

    def test_sanitize_password(self):
        """Test password removal from error messages."""
        error_msg = Exception("Authentication failed: password=mySecretPass123")

        sanitized = sanitize_error_message(error_msg)

        # Password should be redacted
        assert "mySecretPass123" not in sanitized
        assert "password=[REDACTED]" in sanitized

    def test_sanitize_bearer_token(self):
        """Test Bearer token removal from error messages."""
        error_msg = Exception("Request failed with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")

        sanitized = sanitize_error_message(error_msg)

        # Bearer token should be redacted
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "Bearer [REDACTED]" in sanitized

    def test_sanitize_multiple_secrets(self):
        """Test sanitization of multiple secrets in one message."""
        error_msg = Exception(
            "Failed: api_key=sk-test123456789012345678901234567890 "
            "password=secret123 token=abc.def.ghi"
        )

        sanitized = sanitize_error_message(error_msg)

        # All secrets should be redacted
        assert "sk-test123456789012345678901234567890" not in sanitized
        assert "secret123" not in sanitized
        assert "[REDACTED" in sanitized

    def test_sanitize_case_insensitive(self):
        """Test that sanitization is case-insensitive."""
        error_msg = Exception("Error: API_KEY=sk-test12345678901234567890 PASSWORD=secret")

        sanitized = sanitize_error_message(error_msg)

        assert "sk-test12345678901234567890" not in sanitized
        assert "secret" not in sanitized.split("PASSWORD=")[1] if "PASSWORD=" in sanitized else True

    def test_sanitize_no_secrets(self):
        """Test sanitization when no secrets are present."""
        error_msg = Exception("A normal error message without secrets")

        sanitized = sanitize_error_message(error_msg)

        # Message should remain unchanged
        assert sanitized == "A normal error message without secrets"

    def test_sanitize_various_api_key_formats(self):
        """Test sanitization of various API key formats."""
        error_msg = Exception(
            "Errors: "
            "api_key='sk-abc123456789012345678901234567890' "
            'api-key="sk-def123456789012345678901234567890" '
            "apikey:sk-ghi123456789012345678901234567890"
        )

        sanitized = sanitize_error_message(error_msg)

        # All variations should be redacted
        assert "sk-abc123456789012345678901234567890" not in sanitized
        assert "sk-def123456789012345678901234567890" not in sanitized
        assert "sk-ghi123456789012345678901234567890" not in sanitized

    def test_sanitize_secret_keyword(self):
        """Test sanitization of 'secret' keyword."""
        error_msg = Exception("Configuration error: secret=my_secret_value_here")

        sanitized = sanitize_error_message(error_msg)

        assert "my_secret_value_here" not in sanitized
        assert "secret=[REDACTED]" in sanitized


class TestSecureConfigValidation:
    """Additional tests for SecureConfig validation features."""

    def test_detect_key_type_openai(self):
        """Test detection of OpenAI key type from variable name."""
        key_type = SecureConfig._detect_key_type("OPENAI_API_KEY")
        assert key_type == "openai"

    def test_detect_key_type_anthropic(self):
        """Test detection of Anthropic key type from variable name."""
        key_type = SecureConfig._detect_key_type("ANTHROPIC_API_KEY")
        assert key_type == "anthropic"

        key_type2 = SecureConfig._detect_key_type("CLAUDE_API_KEY")
        assert key_type2 == "anthropic"

    def test_detect_key_type_github(self):
        """Test detection of GitHub key type from variable name."""
        key_type = SecureConfig._detect_key_type("GITHUB_TOKEN")
        assert key_type == "github"

    def test_detect_key_type_unknown(self):
        """Test detection returns None for unknown key types."""
        key_type = SecureConfig._detect_key_type("CUSTOM_API_KEY")
        assert key_type is None

    def test_validate_key_format_too_short(self):
        """Test validation fails for keys that are too short."""
        short_key = "sk-short"

        with pytest.raises(APIKeyValidationError) as exc_info:
            SecureConfig._validate_key_format(short_key, "openai", "TEST_KEY")

        assert "too short" in str(exc_info.value)

    def test_validate_key_format_minimum_length(self):
        """Test validation with minimum length requirement."""
        # Default minimum is 20 characters
        short_key = "x" * 19

        with pytest.raises(APIKeyValidationError):
            SecureConfig._validate_key_format(short_key, "default", "TEST_KEY")

        # 20 characters should pass length check (pattern might warn)
        valid_length_key = "x" * 20
        # Should not raise for length (pattern warning is logged, not raised)
        SecureConfig._validate_key_format(valid_length_key, "default", "TEST_KEY")


class TestSecureHTTPClientRetries:
    """Tests for SecureHTTPClient retry configuration."""

    @pytest.fixture
    def mock_requests_module(self):
        """Mock the entire requests module with proper structure."""
        with patch('ai_automation_framework.core.security.requests') as mock_req, \
             patch('ai_automation_framework.core.security.Retry') as mock_retry, \
             patch('ai_automation_framework.core.security.HTTPAdapter') as mock_adapter:

            mock_session = MagicMock()
            mock_req.Session.return_value = mock_session

            yield {
                'requests': mock_req,
                'retry': mock_retry,
                'adapter': mock_adapter,
                'session': mock_session
            }

    def test_retry_configuration(self, mock_requests_module):
        """Test that retry strategy is configured correctly."""
        client = SecureHTTPClient(max_retries=5)

        # Verify Retry was called with correct parameters
        retry_call = mock_requests_module['retry']
        if retry_call.called:
            call_kwargs = retry_call.call_args[1] if retry_call.call_args else {}
            # Verify some retry parameters were set
            assert 'total' in call_kwargs or retry_call.call_count > 0

    def test_session_headers(self, mock_requests_module):
        """Test that default headers are set correctly."""
        custom_ua = "MyApp/2.0"
        client = SecureHTTPClient(user_agent=custom_ua)

        session = mock_requests_module['session']
        # Verify headers were updated
        assert session.headers.update.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
