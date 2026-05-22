"""Tests for core components."""

import pytest
from ai_automation_framework.core.config import Config, get_config
from ai_automation_framework.core.base import Message, Response
from ai_automation_framework.core.logger import get_logger


class TestConfig:
    """Test configuration management."""

    def test_config_creation(self):
        """Test creating a config instance."""
        config = Config(
            openai_api_key="test_key",
            default_model="gpt-4",
            temperature=0.7
        )
        assert config.openai_api_key == "test_key"
        assert config.default_model == "gpt-4"
        assert config.temperature == 0.7

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = Config(openai_api_key="test")
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "openai_api_key" in config_dict


class TestMessage:
    """Test Message model."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_with_name(self):
        """Test message with name field."""
        msg = Message(role="assistant", content="Hi", name="bot")
        assert msg.name == "bot"


class TestResponse:
    """Test Response model."""

    def test_response_creation(self):
        """Test creating a response."""
        resp = Response(
            content="Test response",
            model="gpt-4",
            usage={"total_tokens": 100}
        )
        assert resp.content == "Test response"
        assert resp.model == "gpt-4"
        assert resp.usage["total_tokens"] == 100


class TestLogger:
    """Test logging functionality."""

    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test")
        assert logger is not None
