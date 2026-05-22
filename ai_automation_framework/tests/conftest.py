"""Pytest configuration and shared fixtures."""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Generator


# Environment setup for tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "DEFAULT_MODEL": "gpt-4",
        "TEMPERATURE": "0.7",
    }
    with patch.dict(os.environ, test_env):
        yield


# Mock LLM clients
@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    with patch("openai.OpenAI") as mock:
        client = Mock()
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mock response"))],
            usage=MagicMock(total_tokens=100, prompt_tokens=50, completion_tokens=50),
            model="gpt-4"
        )
        mock.return_value = client
        yield mock


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    with patch("anthropic.Anthropic") as mock:
        client = Mock()
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Mock response")],
            usage=MagicMock(input_tokens=50, output_tokens=50),
            model="claude-3-opus-20240229"
        )
        mock.return_value = client
        yield mock


# Sample data fixtures
@pytest.fixture
def sample_messages():
    """Create sample messages for testing."""
    from ai_automation_framework.core.base import Message
    return [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello!"),
        Message(role="assistant", content="Hi there!"),
    ]


@pytest.fixture
def sample_config():
    """Create a sample configuration."""
    from ai_automation_framework.core.config import Config
    return Config(
        openai_api_key="test_key",
        default_model="gpt-4",
        temperature=0.7
    )


# Temporary directory fixtures
@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for file-based tests."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_text_file(temp_test_dir):
    """Create a sample text file for testing."""
    file_path = temp_test_dir / "sample.txt"
    file_path.write_text("This is a sample text file.\nLine 2.\nLine 3.")
    return file_path


@pytest.fixture
def sample_csv_file(temp_test_dir):
    """Create a sample CSV file for testing."""
    file_path = temp_test_dir / "sample.csv"
    file_path.write_text("name,age,city\nAlice,30,New York\nBob,25,Los Angeles\n")
    return file_path


@pytest.fixture
def sample_json_file(temp_test_dir):
    """Create a sample JSON file for testing."""
    import json
    file_path = temp_test_dir / "sample.json"
    data = {"name": "Test", "values": [1, 2, 3]}
    file_path.write_text(json.dumps(data))
    return file_path


# Database fixtures
@pytest.fixture
def temp_sqlite_db(temp_test_dir):
    """Create a temporary SQLite database."""
    import sqlite3
    db_path = temp_test_dir / "test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)
    cursor.execute("INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')")
    cursor.execute("INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com')")
    conn.commit()
    conn.close()
    return db_path


# Mock HTTP responses
@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response."""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_response.text = '{"success": true, "data": "test"}'
        mock_response.content = b'{"success": true, "data": "test"}'
        mock_response.headers = {"Content-Type": "application/json"}

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response

        yield {"get": mock_get, "post": mock_post, "response": mock_response}


# Async fixtures
@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Skip markers
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marks tests that require real API keys"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async tests"
    )
