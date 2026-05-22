"""Google Gemini client implementation."""

from typing import List, Optional, AsyncIterator, Dict, Any
import time
import random
import asyncio
from ai_automation_framework.llm.base_client import BaseLLMClient
from ai_automation_framework.core.base import Message, Response
from ai_automation_framework.core.config import get_config
from ai_automation_framework.core.exceptions import (
    AuthenticationError,
    RateLimitError,
    NetworkError,
    APIError,
    create_error_context,
)

# Lazy import to avoid import errors if google-generativeai is not installed
_genai = None
_genai_types = None


def _get_genai():
    """Lazy import of google.generativeai module."""
    global _genai, _genai_types
    if _genai is None:
        try:
            import google.generativeai as genai
            from google.generativeai import types as genai_types
            _genai = genai
            _genai_types = genai_types
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for GeminiClient. "
                "Install it with: pip install google-generativeai"
            )
    return _genai, _genai_types


class GeminiClient(BaseLLMClient):
    """
    Google Gemini client implementation.

    Supports Gemini Pro, Gemini Pro Vision, Gemini 1.5, and other Google AI models.

    Features:
    - Multi-modal support (text, images, video)
    - Streaming responses
    - Function calling / Tool use
    - Safety settings configuration
    - Automatic retry with exponential backoff

    Example:
        >>> from ai_automation_framework.llm import GeminiClient
        >>> client = GeminiClient(model="gemini-1.5-pro")
        >>> response = client.simple_chat("Hello, how are you?")
        >>> print(response)
    """

    # Available Gemini models
    AVAILABLE_MODELS = [
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro",
        "gemini-pro-vision",
        "gemini-1.0-pro",
        "gemini-1.0-pro-vision",
    ]

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        safety_settings: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize Gemini client.

        Args:
            model: Model name (default: gemini-1.5-pro)
            api_key: Google API key (default: from config)
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)
            safety_settings: Custom safety settings for content filtering
            generation_config: Custom generation configuration
            **kwargs: Additional configuration
        """
        config = get_config()
        model = model or "gemini-1.5-pro"
        api_key = api_key or config.google_api_key

        super().__init__(
            model=model,
            api_key=api_key,
            name="GeminiClient",
            **kwargs
        )

        self.max_retries = max_retries
        self.base_delay = base_delay
        self.safety_settings = safety_settings
        self.generation_config = generation_config
        self._model_instance = None

    def _initialize(self) -> None:
        """Initialize the client."""
        super()._initialize()

        genai, _ = _get_genai()
        genai.configure(api_key=self.api_key)

        # Create model instance with optional configurations
        model_kwargs = {}
        if self.safety_settings:
            model_kwargs['safety_settings'] = self.safety_settings
        if self.generation_config:
            model_kwargs['generation_config'] = self.generation_config

        self._model_instance = genai.GenerativeModel(
            model_name=self.model,
            **model_kwargs
        )

        self.logger.info(f"Initialized Gemini client with model {self.model}")

    def _messages_to_gemini_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Convert Message objects to Gemini format.

        Gemini uses a different message format:
        - "user" role maps to "user"
        - "assistant" role maps to "model"
        - "system" role is handled as a prefix to the first user message
        """
        gemini_messages = []
        system_prefix = ""

        for msg in messages:
            if msg.role == "system":
                # Prepend system message to the conversation context
                system_prefix = f"[System Instructions: {msg.content}]\n\n"
            elif msg.role == "user":
                content = system_prefix + msg.content if system_prefix else msg.content
                system_prefix = ""  # Clear after first use
                gemini_messages.append({
                    "role": "user",
                    "parts": [content]
                })
            elif msg.role == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [msg.content]
                })
            elif msg.role == "tool":
                # Tool responses are typically handled differently
                gemini_messages.append({
                    "role": "user",
                    "parts": [f"[Tool Response: {msg.content}]"]
                })

        return gemini_messages

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        error_str = str(error).lower()

        # Retry on rate limit errors
        if "rate" in error_str and "limit" in error_str:
            return True
        if "quota" in error_str:
            return True
        # Retry on server errors
        if "500" in error_str or "503" in error_str or "502" in error_str:
            return True
        if "internal" in error_str or "unavailable" in error_str:
            return True
        # Don't retry authentication errors
        if "api key" in error_str or "authentication" in error_str or "invalid" in error_str:
            return False

        return False

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.base_delay * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    def _extract_usage_from_response(self, response) -> Optional[Dict[str, int]]:
        """Extract token usage from Gemini response."""
        try:
            if hasattr(response, 'usage_metadata'):
                metadata = response.usage_metadata
                return {
                    "prompt_tokens": getattr(metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(metadata, 'total_token_count', 0),
                }
        except Exception:
            pass
        return None

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Response:
        """
        Send a chat completion request to Gemini.

        Args:
            messages: List of messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters (safety_settings, tools, etc.)

        Returns:
            Response object

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIError: If API call fails
        """
        self.initialize()

        genai, genai_types = _get_genai()
        gemini_messages = self._messages_to_gemini_format(messages)
        last_error = None

        # Build generation config
        gen_config = {}
        if temperature is not None:
            gen_config['temperature'] = temperature
        elif self.temperature:
            gen_config['temperature'] = self.temperature
        if max_tokens is not None:
            gen_config['max_output_tokens'] = max_tokens
        elif self.max_tokens:
            gen_config['max_output_tokens'] = self.max_tokens

        for attempt in range(self.max_retries + 1):
            try:
                # Start a chat session
                chat = self._model_instance.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])

                # Send the last message
                last_message = gemini_messages[-1] if gemini_messages else {"parts": [""]}
                response = chat.send_message(
                    last_message["parts"][0] if last_message["parts"] else "",
                    generation_config=gen_config if gen_config else None,
                    **kwargs
                )

                # Extract content
                content = ""
                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        content = "".join(
                            part.text for part in candidate.content.parts
                            if hasattr(part, 'text')
                        )

                # Extract finish reason
                finish_reason = None
                if response.candidates:
                    finish_reason = str(response.candidates[0].finish_reason)

                # Extract usage
                usage = self._extract_usage_from_response(response)

                return Response(
                    content=content,
                    role="assistant",
                    model=self.model,
                    usage=usage,
                    finish_reason=finish_reason,
                )

            except Exception as e:
                error_str = str(e).lower()

                # Check for authentication errors
                if "api key" in error_str or "authentication" in error_str:
                    self.logger.error(
                        f"Gemini authentication failed: {e}",
                        extra=create_error_context(model=self.model, provider="gemini")
                    )
                    raise AuthenticationError(
                        message=f"Gemini authentication failed: {e}",
                        context=create_error_context(model=self.model, provider="gemini"),
                        original_exception=e
                    ) from e

                last_error = e

                # Check if error is retryable
                if attempt < self.max_retries and self._is_retryable_error(e):
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.warning(
                        f"Gemini API error (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s...",
                        extra=create_error_context(attempt=attempt + 1, delay=delay)
                    )
                    time.sleep(delay)
                elif "rate" in error_str or "quota" in error_str:
                    self.logger.error(
                        f"Gemini rate limit exceeded: {e}",
                        extra=create_error_context(model=self.model, attempts=attempt + 1)
                    )
                    raise RateLimitError(
                        message=f"Gemini rate limit exceeded after {attempt + 1} attempts",
                        context=create_error_context(model=self.model, attempts=attempt + 1),
                        original_exception=e
                    ) from e
                else:
                    self.logger.error(
                        f"Gemini API error: {e}",
                        extra=create_error_context(model=self.model)
                    )
                    raise APIError(
                        message=f"Gemini API error: {e}",
                        context=create_error_context(model=self.model),
                        original_exception=e
                    ) from e

        # If we exhausted all retries
        if last_error:
            raise APIError(
                message=f"Gemini API error after {self.max_retries + 1} attempts: {last_error}",
                context=create_error_context(model=self.model, attempts=self.max_retries + 1),
                original_exception=last_error
            ) from last_error

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
        self.initialize()

        genai, _ = _get_genai()
        gemini_messages = self._messages_to_gemini_format(messages)
        last_error = None

        # Build generation config
        gen_config = {}
        if temperature is not None:
            gen_config['temperature'] = temperature
        elif self.temperature:
            gen_config['temperature'] = self.temperature
        if max_tokens is not None:
            gen_config['max_output_tokens'] = max_tokens
        elif self.max_tokens:
            gen_config['max_output_tokens'] = self.max_tokens

        for attempt in range(self.max_retries + 1):
            try:
                # Start a chat session
                chat = self._model_instance.start_chat(
                    history=gemini_messages[:-1] if len(gemini_messages) > 1 else []
                )

                # Send the last message asynchronously
                last_message = gemini_messages[-1] if gemini_messages else {"parts": [""]}
                response = await chat.send_message_async(
                    last_message["parts"][0] if last_message["parts"] else "",
                    generation_config=gen_config if gen_config else None,
                    **kwargs
                )

                # Extract content
                content = ""
                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        content = "".join(
                            part.text for part in candidate.content.parts
                            if hasattr(part, 'text')
                        )

                # Extract finish reason
                finish_reason = None
                if response.candidates:
                    finish_reason = str(response.candidates[0].finish_reason)

                # Extract usage
                usage = self._extract_usage_from_response(response)

                return Response(
                    content=content,
                    role="assistant",
                    model=self.model,
                    usage=usage,
                    finish_reason=finish_reason,
                )

            except Exception as e:
                error_str = str(e).lower()

                if "api key" in error_str or "authentication" in error_str:
                    self.logger.error(
                        f"Gemini authentication failed: {e}",
                        extra=create_error_context(model=self.model, provider="gemini")
                    )
                    raise AuthenticationError(
                        message=f"Gemini authentication failed: {e}",
                        context=create_error_context(model=self.model, provider="gemini"),
                        original_exception=e
                    ) from e

                last_error = e

                if attempt < self.max_retries and self._is_retryable_error(e):
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.warning(
                        f"Gemini API error (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s...",
                        extra=create_error_context(attempt=attempt + 1, delay=delay)
                    )
                    await asyncio.sleep(delay)
                elif "rate" in error_str or "quota" in error_str:
                    raise RateLimitError(
                        message=f"Gemini rate limit exceeded after {attempt + 1} attempts",
                        context=create_error_context(model=self.model, attempts=attempt + 1),
                        original_exception=e
                    ) from e
                else:
                    raise APIError(
                        message=f"Gemini API error: {e}",
                        context=create_error_context(model=self.model),
                        original_exception=e
                    ) from e

        if last_error:
            raise APIError(
                message=f"Gemini API error after {self.max_retries + 1} attempts: {last_error}",
                context=create_error_context(model=self.model, attempts=self.max_retries + 1),
                original_exception=last_error
            ) from last_error

    async def stream_chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion from Gemini.

        Args:
            messages: List of messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters

        Yields:
            Response chunks
        """
        self.initialize()

        gemini_messages = self._messages_to_gemini_format(messages)

        # Build generation config
        gen_config = {}
        if temperature is not None:
            gen_config['temperature'] = temperature
        elif self.temperature:
            gen_config['temperature'] = self.temperature
        if max_tokens is not None:
            gen_config['max_output_tokens'] = max_tokens
        elif self.max_tokens:
            gen_config['max_output_tokens'] = self.max_tokens

        try:
            # Start a chat session
            chat = self._model_instance.start_chat(
                history=gemini_messages[:-1] if len(gemini_messages) > 1 else []
            )

            # Send the last message with streaming
            last_message = gemini_messages[-1] if gemini_messages else {"parts": [""]}
            response = await chat.send_message_async(
                last_message["parts"][0] if last_message["parts"] else "",
                generation_config=gen_config if gen_config else None,
                stream=True,
                **kwargs
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            error_str = str(e).lower()

            if "api key" in error_str or "authentication" in error_str:
                self.logger.error(
                    f"Gemini authentication failed during stream: {e}",
                    extra=create_error_context(model=self.model, operation="stream")
                )
                raise AuthenticationError(
                    message=f"Gemini authentication failed during stream: {e}",
                    context=create_error_context(model=self.model, operation="stream"),
                    original_exception=e
                ) from e
            elif "rate" in error_str or "quota" in error_str:
                self.logger.error(
                    f"Gemini rate limit exceeded during stream: {e}",
                    extra=create_error_context(model=self.model, operation="stream")
                )
                raise RateLimitError(
                    message=f"Gemini rate limit exceeded during stream: {e}",
                    context=create_error_context(model=self.model, operation="stream"),
                    original_exception=e
                ) from e
            else:
                self.logger.error(
                    f"Gemini API error during stream: {e}",
                    extra=create_error_context(model=self.model, operation="stream")
                )
                raise APIError(
                    message=f"Gemini API error during stream: {e}",
                    context=create_error_context(model=self.model, operation="stream"),
                    original_exception=e
                ) from e

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        self.initialize()

        try:
            result = self._model_instance.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            self.logger.warning(f"Failed to count tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def list_models(self) -> List[str]:
        """
        List available Gemini models.

        Returns:
            List of model names
        """
        self.initialize()

        genai, _ = _get_genai()
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model.name)
            return models
        except Exception as e:
            self.logger.warning(f"Failed to list models: {e}")
            return self.AVAILABLE_MODELS
