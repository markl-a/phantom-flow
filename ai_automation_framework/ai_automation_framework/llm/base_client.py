"""Base LLM client interface."""

from abc import abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from ai_automation_framework.core.base import BaseComponent, Message, Response
from ai_automation_framework.core.exceptions import ConfigError


class BaseLLMClient(BaseComponent):
    """
    Base class for LLM clients.

    Provides a unified interface for different LLM providers.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        """
        Initialize the LLM client.

        Args:
            model: Model name
            api_key: API key for the provider
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Response:
        """
        Send a chat completion request.

        Args:
            messages: List of messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters

        Returns:
            Response object
        """
        pass

    @abstractmethod
    async def achat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Response:
        """
        Async version of chat.

        Args:
            messages: List of messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters

        Returns:
            Response object
        """
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion.

        Args:
            messages: List of messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters

        Yields:
            Response chunks
        """
        pass

    def simple_chat(self, prompt: str, **kwargs) -> str:
        """
        Simple chat interface with a single prompt.

        Args:
            prompt: User prompt
            **kwargs: Additional parameters

        Returns:
            Response content
        """
        messages = [Message(role="user", content=prompt)]
        response = self.chat(messages, **kwargs)
        return response.content

    async def asimple_chat(self, prompt: str, **kwargs) -> str:
        """
        Async simple chat interface.

        Args:
            prompt: User prompt
            **kwargs: Additional parameters

        Returns:
            Response content
        """
        messages = [Message(role="user", content=prompt)]
        response = await self.achat(messages, **kwargs)
        return response.content

    def _initialize(self) -> None:
        """Initialize the client."""
        if not self.api_key:
            self.logger.error(
                f"API key missing for {self.name}",
                extra={"client": self.name, "model": self.model}
            )
            raise ConfigError(
                message=f"API key required for {self.name}",
                context={"client": self.name, "model": self.model}
            )
        self.logger.info(f"Initialized {self.name} with model {self.model}")

    def _cleanup(self) -> None:
        """Cleanup resources."""
        pass
