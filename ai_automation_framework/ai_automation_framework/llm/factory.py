"""
LLM Client Factory - Factory Pattern Implementation

This module provides a factory pattern implementation for creating LLM clients.
It allows for easy registration of new providers and centralized client creation.
"""

import logging
from typing import Dict, Type, Optional, Any

from ai_automation_framework.llm.base_client import BaseLLMClient


logger = logging.getLogger(__name__)


class LLMClientFactory:
    """
    LLM Client Factory - Factory Pattern for LLM Providers

    This factory allows dynamic registration and creation of LLM clients
    from different providers (OpenAI, Anthropic, Ollama, etc.).

    Features:
    - Provider registration/deregistration
    - Client creation by provider name
    - Configuration-based client creation
    - Support for custom providers
    - Thread-safe implementation

    Example:
        >>> from ai_automation_framework.llm.factory import LLMClientFactory
        >>> from ai_automation_framework.llm.openai_client import OpenAIClient
        >>>
        >>> # Register a provider
        >>> LLMClientFactory.register_provider("openai", OpenAIClient)
        >>>
        >>> # Create a client
        >>> client = LLMClientFactory.create("openai", model="gpt-4")
        >>>
        >>> # Create from config
        >>> config = {"provider": "openai", "model": "gpt-4", "temperature": 0.7}
        >>> client = LLMClientFactory.from_config(config)
    """

    _providers: Dict[str, Type[BaseLLMClient]] = {}
    _lock = None  # Will be initialized on first use

    @classmethod
    def _get_lock(cls):
        """Get or create the threading lock."""
        if cls._lock is None:
            import threading
            cls._lock = threading.RLock()
        return cls._lock

    @classmethod
    def register_provider(cls, name: str, client_class: Type[BaseLLMClient]) -> None:
        """
        Register a new LLM provider.

        Args:
            name: Provider name (e.g., "openai", "anthropic", "ollama")
            client_class: Client class that inherits from BaseLLMClient

        Raises:
            TypeError: If client_class is not a subclass of BaseLLMClient
            ValueError: If provider name is empty

        Example:
            >>> from ai_automation_framework.llm.openai_client import OpenAIClient
            >>> LLMClientFactory.register_provider("openai", OpenAIClient)
        """
        if not name or not isinstance(name, str):
            raise ValueError("Provider name must be a non-empty string")

        if not isinstance(client_class, type) or not issubclass(client_class, BaseLLMClient):
            raise TypeError(
                f"Client class must be a subclass of BaseLLMClient, "
                f"got {client_class}"
            )

        with cls._get_lock():
            normalized_name = name.lower().strip()

            if normalized_name in cls._providers:
                logger.warning(
                    f"Provider '{normalized_name}' already registered, overwriting"
                )

            cls._providers[normalized_name] = client_class
            logger.info(f"Registered LLM provider: {normalized_name}")

    @classmethod
    def unregister_provider(cls, name: str) -> bool:
        """
        Unregister an LLM provider.

        Args:
            name: Provider name to unregister

        Returns:
            True if provider was found and removed, False otherwise
        """
        with cls._get_lock():
            normalized_name = name.lower().strip()

            if normalized_name in cls._providers:
                del cls._providers[normalized_name]
                logger.info(f"Unregistered LLM provider: {normalized_name}")
                return True

            logger.warning(f"Provider '{normalized_name}' not found")
            return False

    @classmethod
    def create(
        cls,
        provider: str,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMClient:
        """
        Create an LLM client for the specified provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            model: Model name (provider-specific)
            **kwargs: Additional configuration parameters passed to the client

        Returns:
            Instantiated LLM client

        Raises:
            ValueError: If provider is not registered

        Example:
            >>> client = LLMClientFactory.create(
            ...     "openai",
            ...     model="gpt-4",
            ...     temperature=0.7,
            ...     max_tokens=2000
            ... )
        """
        if not provider or not isinstance(provider, str):
            raise ValueError("Provider must be a non-empty string")

        normalized_name = provider.lower().strip()

        with cls._get_lock():
            if normalized_name not in cls._providers:
                available = ", ".join(cls._providers.keys())
                raise ValueError(
                    f"Unknown provider '{normalized_name}'. "
                    f"Available providers: {available or 'none'}"
                )

            client_class = cls._providers[normalized_name]

        # Create client with provided parameters
        logger.debug(
            f"Creating {normalized_name} client with model={model}, "
            f"kwargs={list(kwargs.keys())}"
        )

        # Pass model if provided
        if model:
            kwargs['model'] = model

        try:
            client = client_class(**kwargs)
            logger.info(
                f"Successfully created {normalized_name} client "
                f"(model: {getattr(client, 'model', 'unknown')})"
            )
            return client
        except Exception as e:
            logger.error(f"Failed to create {normalized_name} client: {e}")
            raise

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> BaseLLMClient:
        """
        Create an LLM client from a configuration dictionary.

        The configuration must include a 'provider' key. All other keys
        are passed as parameters to the client constructor.

        Args:
            config: Configuration dictionary with at least 'provider' key

        Returns:
            Instantiated LLM client

        Raises:
            ValueError: If 'provider' key is missing from config

        Example:
            >>> config = {
            ...     "provider": "anthropic",
            ...     "model": "claude-3-5-sonnet-20241022",
            ...     "temperature": 0.8,
            ...     "max_tokens": 4096
            ... }
            >>> client = LLMClientFactory.from_config(config)
        """
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")

        if 'provider' not in config:
            raise ValueError(
                "Config must contain 'provider' key. "
                f"Received keys: {list(config.keys())}"
            )

        # Extract provider and pass rest as kwargs
        config_copy = config.copy()
        provider = config_copy.pop('provider')

        logger.debug(f"Creating client from config: provider={provider}")

        return cls.create(provider, **config_copy)

    @classmethod
    def list_providers(cls) -> list:
        """
        Get list of registered provider names.

        Returns:
            List of provider names

        Example:
            >>> providers = LLMClientFactory.list_providers()
            >>> print(providers)
            ['openai', 'anthropic', 'ollama']
        """
        with cls._get_lock():
            return sorted(cls._providers.keys())

    @classmethod
    def is_registered(cls, provider: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            provider: Provider name to check

        Returns:
            True if provider is registered

        Example:
            >>> if LLMClientFactory.is_registered("openai"):
            ...     client = LLMClientFactory.create("openai")
        """
        normalized_name = provider.lower().strip()
        with cls._get_lock():
            return normalized_name in cls._providers

    @classmethod
    def get_provider_class(cls, provider: str) -> Optional[Type[BaseLLMClient]]:
        """
        Get the client class for a registered provider.

        Args:
            provider: Provider name

        Returns:
            Client class or None if not registered
        """
        normalized_name = provider.lower().strip()
        with cls._get_lock():
            return cls._providers.get(normalized_name)

    @classmethod
    def clear_providers(cls) -> None:
        """
        Clear all registered providers.

        Warning: This will remove all provider registrations.
        Use with caution, mainly for testing purposes.
        """
        with cls._get_lock():
            count = len(cls._providers)
            cls._providers.clear()
            logger.warning(f"Cleared all {count} registered providers")


# Convenience function for creating clients
def create_llm_client(provider: str, **kwargs) -> BaseLLMClient:
    """
    Convenience function to create an LLM client.

    This is a shorthand for LLMClientFactory.create().

    Args:
        provider: Provider name
        **kwargs: Client configuration parameters

    Returns:
        Instantiated LLM client

    Example:
        >>> from ai_automation_framework.llm.factory import create_llm_client
        >>> client = create_llm_client("openai", model="gpt-4")
    """
    return LLMClientFactory.create(provider, **kwargs)
