"""Centralized settings management for AI Automation Framework.

This module provides a Settings class for managing environment-based configuration
with validation and sensible defaults for various service URLs and API keys.
"""

import os
from typing import Optional
from pathlib import Path


class Settings:
    """
    Settings class for managing application configuration.

    Loads configuration from environment variables with sensible defaults.
    Supports .env file loading if python-dotenv is available.

    Attributes:
        OPENAI_API_KEY: OpenAI API key (required)
        ANTHROPIC_API_KEY: Anthropic API key (required)
        N8N_BASE_URL: n8n workflow automation base URL (optional)
        OLLAMA_BASE_URL: Ollama local LLM base URL (optional)
        DATABASE_URL: Database connection URL (optional)
        REDIS_URL: Redis connection URL (optional)
    """

    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        # Try to load .env file if python-dotenv is available
        self._load_dotenv()

        # Required API Keys
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

        # Service URLs with defaults to localhost
        self.N8N_BASE_URL: str = os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/ai_automation.db")
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Validate required settings
        self._validate()

    def _load_dotenv(self) -> None:
        """Load environment variables from .env file if python-dotenv is available."""
        try:
            from dotenv import load_dotenv

            # Look for .env file in current directory and parent directories
            env_path = Path.cwd() / ".env"
            if env_path.exists():
                load_dotenv(env_path)
            else:
                # Try loading from default location
                load_dotenv()
        except ImportError:
            # python-dotenv not installed, skip .env loading
            pass

    def _validate(self) -> None:
        """
        Validate required settings.

        Raises:
            ValueError: If required settings are missing or invalid.
        """
        missing_required: list[str] = []

        # Check required API keys
        if not self.OPENAI_API_KEY:
            missing_required.append("OPENAI_API_KEY")
        if not self.ANTHROPIC_API_KEY:
            missing_required.append("ANTHROPIC_API_KEY")

        if missing_required:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_required)}. "
                "Please set these in your environment or .env file."
            )

        # Validate URL formats (basic validation)
        self._validate_url("N8N_BASE_URL", self.N8N_BASE_URL)
        self._validate_url("OLLAMA_BASE_URL", self.OLLAMA_BASE_URL)
        self._validate_url("REDIS_URL", self.REDIS_URL)

    def _validate_url(self, name: str, url: str) -> None:
        """
        Validate URL format.

        Args:
            name: Name of the setting (for error messages)
            url: URL to validate

        Raises:
            ValueError: If URL is invalid
        """
        if not url:
            raise ValueError(f"{name} cannot be empty")

        # Basic URL validation - check if it starts with a valid scheme
        valid_schemes = ("http://", "https://", "redis://", "sqlite://", "postgresql://", "mysql://")
        if not any(url.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(
                f"{name} must start with a valid scheme "
                f"(http://, https://, redis://, sqlite://, postgresql://, mysql://). "
                f"Got: {url}"
            )

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a setting value by key.

        Args:
            key: Setting key name
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return getattr(self, key, default)

    def __repr__(self) -> str:
        """Return string representation of settings (with masked API keys)."""
        return (
            f"Settings("
            f"OPENAI_API_KEY={'***' if self.OPENAI_API_KEY else None}, "
            f"ANTHROPIC_API_KEY={'***' if self.ANTHROPIC_API_KEY else None}, "
            f"N8N_BASE_URL={self.N8N_BASE_URL}, "
            f"OLLAMA_BASE_URL={self.OLLAMA_BASE_URL}, "
            f"DATABASE_URL={self._mask_url(self.DATABASE_URL)}, "
            f"REDIS_URL={self._mask_url(self.REDIS_URL)}"
            f")"
        )

    @staticmethod
    def _mask_url(url: str) -> str:
        """
        Mask sensitive information in URLs (passwords).

        Args:
            url: URL to mask

        Returns:
            Masked URL string
        """
        if not url:
            return url

        # Mask password in URL if present (e.g., redis://user:password@host)
        if "://" in url and "@" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                creds, host = rest.rsplit("@", 1)
                if ":" in creds:
                    user, _ = creds.split(":", 1)
                    return f"{scheme}://{user}:***@{host}"

        return url


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(force_reload: bool = False) -> Settings:
    """
    Get or create global settings instance (singleton pattern).

    Args:
        force_reload: If True, force recreation of settings instance

    Returns:
        Settings instance

    Raises:
        ValueError: If required settings are missing

    Example:
        >>> from ai_automation_framework.core import get_settings
        >>> settings = get_settings()
        >>> print(settings.OPENAI_API_KEY)
    """
    global _settings

    if _settings is None or force_reload:
        _settings = Settings()

    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None
