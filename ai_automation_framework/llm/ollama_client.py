"""Ollama client for local LLM inference."""

from typing import List, Optional, AsyncIterator
import json
import time
import random
import asyncio
import requests
import aiohttp
from ai_automation_framework.llm.base_client import BaseLLMClient
from ai_automation_framework.core.base import Message, Response


class OllamaClient(BaseLLMClient):
    """
    Ollama client for running local LLM models.

    Supports models like Llama 2, Mistral, Code Llama, and more.
    """

    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs
    ):
        """
        Initialize Ollama client.

        Args:
            model: Model name (e.g., llama2, mistral, codellama)
            base_url: Ollama server URL
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)
            **kwargs: Additional configuration
        """
        super().__init__(
            model=model,
            api_key="not_required",  # Ollama doesn't need API key
            name="OllamaClient",
            **kwargs
        )

        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _messages_to_ollama_format(self, messages: List[Message]) -> str:
        """
        Convert Message objects to Ollama prompt format.

        Ollama uses a simple text prompt format.
        """
        prompt_parts = []

        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}\n")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}\n")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}\n")

        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        if isinstance(error, requests.exceptions.RequestException):
            # Retry on connection errors, timeouts, and server errors
            if isinstance(error, (requests.exceptions.ConnectionError,
                                requests.exceptions.Timeout)):
                return True
            # Check for rate limit or server error status codes
            if hasattr(error, 'response') and error.response is not None:
                status_code = error.response.status_code
                # Retry on 429 (rate limit) and 5xx (server errors)
                return status_code == 429 or status_code >= 500
        return False

    def _is_retryable_async_error(self, error: Exception) -> bool:
        """Check if an async error is retryable."""
        if isinstance(error, aiohttp.ClientError):
            # Retry on connection errors and timeouts
            if isinstance(error, (aiohttp.ClientConnectionError,
                                aiohttp.ClientConnectorError,
                                aiohttp.ServerTimeoutError)):
                return True
            # For ClientResponseError, check status code
            if isinstance(error, aiohttp.ClientResponseError):
                return error.status == 429 or error.status >= 500
        return False

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.base_delay * (2 ** attempt)
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Response:
        """
        Send a chat completion request to Ollama.

        Args:
            messages: List of messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters

        Returns:
            Response object
        """
        self.initialize()

        # Convert messages to prompt
        prompt = self._messages_to_ollama_format(messages)

        # Prepare request
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            }
        }

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # Make request
                response = requests.post(url, json=payload)
                response.raise_for_status()

                result = response.json()

                # Safely access response content
                content = result.get("response", "")
                if not content:
                    self.logger.warning("Empty response from Ollama API")

                return Response(
                    content=content,
                    role="assistant",
                    model=self.model,
                    metadata={
                        "total_duration": result.get("total_duration"),
                        "load_duration": result.get("load_duration"),
                        "prompt_eval_count": result.get("prompt_eval_count"),
                        "eval_count": result.get("eval_count"),
                    }
                )

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.max_retries and self._is_retryable_error(e):
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.warning(
                        f"Ollama request error (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"Ollama request failed: {e}")
                    raise RuntimeError(f"Ollama request failed: {e}") from e
            except (KeyError, json.JSONDecodeError) as e:
                self.logger.error(f"Failed to parse Ollama response: {e}")
                raise RuntimeError(f"Failed to parse Ollama response: {e}") from e

        # If we exhausted all retries
        if last_error:
            self.logger.error(f"Ollama request failed after {self.max_retries + 1} attempts: {last_error}")
            raise RuntimeError(f"Ollama request failed after {self.max_retries + 1} attempts: {last_error}") from last_error

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

        prompt = self._messages_to_ollama_format(messages)
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            }
        }

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as response:
                        response.raise_for_status()
                        result = await response.json()

                        # Safely access response content
                        content = result.get("response", "")
                        if not content:
                            self.logger.warning("Empty response from Ollama API")

                        return Response(
                            content=content,
                            role="assistant",
                            model=self.model,
                            metadata={
                                "total_duration": result.get("total_duration"),
                                "prompt_eval_count": result.get("prompt_eval_count"),
                                "eval_count": result.get("eval_count"),
                            }
                        )
            except aiohttp.ClientError as e:
                last_error = e
                if attempt < self.max_retries and self._is_retryable_async_error(e):
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.warning(
                        f"Ollama async request error (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Ollama async request failed: {e}")
                    raise RuntimeError(f"Ollama async request failed: {e}") from e
            except (KeyError, json.JSONDecodeError) as e:
                self.logger.error(f"Failed to parse Ollama response: {e}")
                raise RuntimeError(f"Failed to parse Ollama response: {e}") from e

        # If we exhausted all retries
        if last_error:
            self.logger.error(f"Ollama async request failed after {self.max_retries + 1} attempts: {last_error}")
            raise RuntimeError(f"Ollama async request failed after {self.max_retries + 1} attempts: {last_error}") from last_error

    async def stream_chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion from Ollama.

        Args:
            messages: List of messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters

        Yields:
            Response chunks
        """
        self.initialize()

        prompt = self._messages_to_ollama_format(messages)
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature or self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()

                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    yield chunk["response"]
                            except json.JSONDecodeError:
                                continue
        except aiohttp.ClientError as e:
            self.logger.error(f"Ollama stream request failed: {e}")
            raise RuntimeError(f"Ollama stream request failed: {e}") from e

    def list_models(self) -> List[str]:
        """
        List available Ollama models.

        Returns:
            List of model names
        """
        url = f"{self.base_url}/api/tags"

        try:
            response = requests.get(url)
            response.raise_for_status()

            result = response.json()
            return [model["name"] for model in result.get("models", [])]

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to list models: {e}")
            return []

    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama library.

        Args:
            model_name: Model name to pull

        Returns:
            True if successful
        """
        url = f"{self.base_url}/api/pull"

        payload = {"name": model_name}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            self.logger.info(f"Successfully pulled model: {model_name}")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to pull model: {e}")
            return False
