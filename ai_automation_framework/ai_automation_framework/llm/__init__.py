"""LLM client implementations."""

from ai_automation_framework.llm.base_client import BaseLLMClient
from ai_automation_framework.llm.openai_client import OpenAIClient
from ai_automation_framework.llm.anthropic_client import AnthropicClient
from ai_automation_framework.llm.ollama_client import OllamaClient
from ai_automation_framework.llm.gemini_client import GeminiClient
from ai_automation_framework.llm.streaming import (
    StreamProcessor,
    ParallelStreamProcessor,
    StreamConfig,
    StreamState,
    StreamStats,
)
from ai_automation_framework.llm.factory import (
    LLMClientFactory,
    create_llm_client,
)


# Auto-register all available LLM providers
def _register_default_providers():
    """Register all default LLM providers with the factory."""
    LLMClientFactory.register_provider("openai", OpenAIClient)
    LLMClientFactory.register_provider("anthropic", AnthropicClient)
    LLMClientFactory.register_provider("ollama", OllamaClient)
    LLMClientFactory.register_provider("gemini", GeminiClient)


# Initialize providers on module import
_register_default_providers()


__all__ = [
    # Base classes
    "BaseLLMClient",
    # Client implementations
    "OpenAIClient",
    "AnthropicClient",
    "OllamaClient",
    "GeminiClient",
    # Streaming
    "StreamProcessor",
    "ParallelStreamProcessor",
    "StreamConfig",
    "StreamState",
    "StreamStats",
    # Factory
    "LLMClientFactory",
    "create_llm_client",
]
