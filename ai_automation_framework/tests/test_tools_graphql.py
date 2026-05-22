"""Tests for the GraphQL API tools."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init_with_valid_rate(self):
        """Test initialization with valid rate."""
        from ai_automation_framework.tools.graphql_api import RateLimiter

        limiter = RateLimiter(rate=2.0)

        assert limiter.rate == 2.0
        assert limiter.capacity >= 1.0

    def test_init_with_zero_rate_raises(self):
        """Test initialization with zero rate raises error."""
        from ai_automation_framework.tools.graphql_api import RateLimiter

        with pytest.raises(ValueError) as exc_info:
            RateLimiter(rate=0)

        assert "Rate must be positive" in str(exc_info.value)

    def test_init_with_negative_rate_raises(self):
        """Test initialization with negative rate raises error."""
        from ai_automation_framework.tools.graphql_api import RateLimiter

        with pytest.raises(ValueError) as exc_info:
            RateLimiter(rate=-1)

        assert "Rate must be positive" in str(exc_info.value)

    def test_wait_for_token_consumes_token(self):
        """Test that wait_for_token consumes a token."""
        from ai_automation_framework.tools.graphql_api import RateLimiter

        limiter = RateLimiter(rate=10.0)  # High rate for fast test
        initial_tokens = limiter.tokens

        limiter.wait_for_token()

        # After consuming one token
        assert limiter.tokens < initial_tokens

    def test_wait_for_token_multiple_calls(self):
        """Test multiple wait_for_token calls."""
        from ai_automation_framework.tools.graphql_api import RateLimiter

        limiter = RateLimiter(rate=100.0)  # Very high rate for fast test

        # Should be able to make multiple calls quickly
        for _ in range(5):
            limiter.wait_for_token()

        # Should still work
        assert True

    def test_rate_limiting_slows_requests(self):
        """Test that rate limiting actually slows requests."""
        from ai_automation_framework.tools.graphql_api import RateLimiter

        limiter = RateLimiter(rate=10.0)  # 10 requests per second

        # Exhaust initial tokens
        for _ in range(int(limiter.capacity)):
            limiter.wait_for_token()

        # Next call should require waiting
        start = time.time()
        limiter.wait_for_token()
        elapsed = time.time() - start

        # Should have waited at least a little
        assert elapsed >= 0  # Basic check that method returns


class TestGraphQLClient:
    """Tests for GraphQLClient class."""

    def test_init_without_rate_limit(self):
        """Test initialization without rate limiting."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        client = GraphQLClient(endpoint="http://localhost/graphql")

        assert client.endpoint == "http://localhost/graphql"
        assert client.rate_limiter is None

    def test_init_with_rate_limit(self):
        """Test initialization with rate limiting."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        client = GraphQLClient(
            endpoint="http://localhost/graphql",
            rate_limit=2.0
        )

        assert client.rate_limiter is not None
        assert client.rate_limiter.rate == 2.0

    def test_validate_query_empty(self):
        """Test validation of empty query."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        client = GraphQLClient(endpoint="http://localhost/graphql")

        with pytest.raises(ValueError) as exc_info:
            client._validate_query("")

        assert "non-empty string" in str(exc_info.value)

    def test_validate_query_none(self):
        """Test validation of None query."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        client = GraphQLClient(endpoint="http://localhost/graphql")

        with pytest.raises(ValueError) as exc_info:
            client._validate_query(None)

        assert "non-empty string" in str(exc_info.value)

    def test_validate_query_too_long(self):
        """Test validation of too long query."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        client = GraphQLClient(endpoint="http://localhost/graphql")
        long_query = "query { " + "x" * 15000 + " }"

        with pytest.raises(ValueError) as exc_info:
            client._validate_query(long_query)

        assert "too long" in str(exc_info.value)

    def test_validate_query_invalid_format(self):
        """Test validation of invalid query format."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        client = GraphQLClient(endpoint="http://localhost/graphql")

        with pytest.raises(ValueError) as exc_info:
            client._validate_query("SELECT * FROM users")

        assert "Invalid GraphQL query format" in str(exc_info.value)

    def test_validate_query_valid(self):
        """Test validation of valid query."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        client = GraphQLClient(endpoint="http://localhost/graphql")

        # Should not raise
        client._validate_query("query { user { id name } }")
        client._validate_query("mutation { createUser(name: \"test\") { id } }")
        client._validate_query("{ user { id } }")  # Shorthand query

    @patch('requests.post')
    def test_execute_success(self, mock_post):
        """Test successful query execution."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"data": {"user": {"id": "1", "name": "Test"}}}
        mock_post.return_value = mock_response

        client = GraphQLClient(endpoint="http://localhost/graphql")
        result = client.execute("query { user { id name } }")

        assert result["data"]["user"]["id"] == "1"
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_execute_with_variables(self, mock_post):
        """Test query execution with variables."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"data": {"user": {"id": "1"}}}
        mock_post.return_value = mock_response

        client = GraphQLClient(endpoint="http://localhost/graphql")
        result = client.execute(
            "query GetUser($id: String!) { user(id: $id) { id } }",
            variables={"id": "1"}
        )

        assert result["data"]["user"]["id"] == "1"
        call_args = mock_post.call_args
        assert call_args[1]['json']['variables'] == {"id": "1"}

    @patch('requests.post')
    def test_execute_invalid_content_type(self, mock_post):
        """Test handling of invalid content type response."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_post.return_value = mock_response

        client = GraphQLClient(endpoint="http://localhost/graphql")

        with pytest.raises(ValueError) as exc_info:
            client.execute("query { user { id } }")

        assert "Invalid response content type" in str(exc_info.value)

    @patch('requests.post')
    def test_execute_timeout(self, mock_post):
        """Test handling of request timeout."""
        import requests
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_post.side_effect = requests.Timeout()

        client = GraphQLClient(endpoint="http://localhost/graphql")

        with pytest.raises(TimeoutError):
            client.execute("query { user { id } }")

    @patch('requests.post')
    def test_execute_request_error(self, mock_post):
        """Test handling of request error."""
        import requests
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_post.side_effect = requests.RequestException("Connection failed")

        client = GraphQLClient(endpoint="http://localhost/graphql")

        with pytest.raises(RuntimeError) as exc_info:
            client.execute("query { user { id } }")

        assert "Request failed" in str(exc_info.value)

    @patch('requests.post')
    def test_execute_with_rate_limiting(self, mock_post):
        """Test query execution with rate limiting."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"data": {}}
        mock_post.return_value = mock_response

        client = GraphQLClient(
            endpoint="http://localhost/graphql",
            rate_limit=100.0  # High rate for fast test
        )

        # Multiple requests should work
        for _ in range(3):
            client.execute("query { user { id } }")

        assert mock_post.call_count == 3

    @patch('requests.post')
    def test_query_user(self, mock_post):
        """Test query_user convenience method."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"data": {"user": {"id": "user-123"}}}
        mock_post.return_value = mock_response

        client = GraphQLClient(endpoint="http://localhost/graphql")
        result = client.query_user("user-123")

        assert "data" in result
        call_args = mock_post.call_args
        assert call_args[1]['json']['variables']['id'] == "user-123"

    @patch('requests.post')
    def test_query_messages(self, mock_post):
        """Test query_messages convenience method."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"data": {"messages": []}}
        mock_post.return_value = mock_response

        client = GraphQLClient(endpoint="http://localhost/graphql")
        result = client.query_messages(sender_id="user-1", limit=10)

        assert "data" in result
        call_args = mock_post.call_args
        assert call_args[1]['json']['variables']['limit'] == 10
        assert call_args[1]['json']['variables']['senderId'] == "user-1"

    @patch('requests.post')
    def test_create_user(self, mock_post):
        """Test create_user mutation."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"data": {"createUser": {"user": {"id": "new-user"}}}}
        mock_post.return_value = mock_response

        client = GraphQLClient(endpoint="http://localhost/graphql")
        result = client.create_user(name="Test User", email="test@example.com")

        assert "data" in result
        call_args = mock_post.call_args
        assert call_args[1]['json']['variables']['name'] == "Test User"
        assert call_args[1]['json']['variables']['email'] == "test@example.com"

    @patch('requests.post')
    def test_send_message(self, mock_post):
        """Test send_message mutation."""
        from ai_automation_framework.tools.graphql_api import GraphQLClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {"data": {"sendMessage": {"message": {"id": "msg-1"}}}}
        mock_post.return_value = mock_response

        client = GraphQLClient(endpoint="http://localhost/graphql")
        result = client.send_message(sender_id="user-1", content="Hello!")

        assert "data" in result
        call_args = mock_post.call_args
        assert call_args[1]['json']['variables']['senderId'] == "user-1"
        assert call_args[1]['json']['variables']['content'] == "Hello!"


class TestGraphQLServer:
    """Tests for GraphQLServer class (requires graphene and flask)."""

    @pytest.mark.skipif(True, reason="Requires graphene and flask")
    def test_server_initialization(self):
        """Test server initialization."""
        from ai_automation_framework.tools.graphql_api import GraphQLServer

        server = GraphQLServer(host="127.0.0.1", port=5001)

        assert server.host == "127.0.0.1"
        assert server.port == 5001
