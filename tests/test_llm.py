"""Tests for LLM clients."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_automation_framework.llm import OpenAIClient, AnthropicClient
from ai_automation_framework.core.base import Message, Response


class TestOpenAIClient:
    """Test OpenAI client."""

    def test_client_initialization(self):
        """Test client initialization."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient(api_key="test_key")
            assert client.api_key == "test_key"
            assert client.model is not None


class TestAnthropicClient:
    """Test Anthropic client."""

    def test_client_initialization(self):
        """Test client initialization."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            client = AnthropicClient(api_key="test_key")
            assert client.api_key == "test_key"
            assert client.model is not None
