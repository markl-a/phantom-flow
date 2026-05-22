"""
GraphQL API 支持
GraphQL API Support

提供 GraphQL 服務器和客戶端功能。
"""

import re
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

try:
    import graphene
    from graphene import ObjectType, String, Int, Float, List as GrapheneList, Field, Schema
    HAS_GRAPHENE = True
except ImportError:
    HAS_GRAPHENE = False
    ObjectType = object
    Schema = object

try:
    from flask import Flask, request, jsonify
    from flask_graphql import GraphQLView
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    The token bucket algorithm maintains a bucket with a maximum capacity.
    Tokens are added at a constant rate (rate per second).
    Each request consumes one token. If no tokens are available, requests must wait.
    """

    def __init__(self, rate: float):
        """
        Initialize rate limiter.

        Args:
            rate: Maximum number of requests per second (e.g., 2.0 = 2 requests/sec)
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")

        self.rate = rate  # tokens per second
        self.capacity = max(1.0, rate)  # maximum tokens
        self.tokens = self.capacity  # current tokens available
        self.last_update = time.time()
        self.lock = threading.Lock()

    def _add_tokens(self):
        """Add tokens based on elapsed time since last update."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

    def wait_for_token(self):
        """
        Wait until a token is available and consume it.

        This method blocks until rate limit allows the request.
        """
        with self.lock:
            while True:
                self._add_tokens()

                if self.tokens >= 1.0:
                    # Consume one token
                    self.tokens -= 1.0
                    return

                # Calculate wait time
                tokens_needed = 1.0 - self.tokens
                wait_time = tokens_needed / self.rate

                # Release lock while sleeping to allow other threads
                # to check if tokens are available
                time.sleep(min(wait_time, 0.1))


# GraphQL 類型定義
if HAS_GRAPHENE:
    class UserType(ObjectType):
        """用戶類型"""
        id = String()
        name = String()
        email = String()
        created_at = String()

    class MessageType(ObjectType):
        """消息類型"""
        id = String()
        content = String()
        sender = Field(UserType)
        timestamp = String()

    class AnalyticsType(ObjectType):
        """分析數據類型"""
        metric_name = String()
        value = Float()
        timestamp = String()


    class Query(ObjectType):
        """查詢根類型"""

        # 用戶查詢
        user = Field(UserType, id=String(required=True))
        users = GrapheneList(UserType, limit=Int(default_value=10))

        # 消息查詢
        message = Field(MessageType, id=String(required=True))
        messages = GrapheneList(
            MessageType,
            sender_id=String(),
            limit=Int(default_value=20)
        )

        # 分析數據查詢
        analytics = GrapheneList(
            AnalyticsType,
            metric_name=String(),
            start_date=String(),
            end_date=String()
        )

        def resolve_user(self, info, id):
            """解析單個用戶"""
            # 這裡應該從數據庫查詢
            return UserType(
                id=id,
                name="John Doe",
                email="john@example.com",
                created_at=datetime.now().isoformat()
            )

        def resolve_users(self, info, limit):
            """解析用戶列表"""
            # 這裡應該從數據庫查詢
            return [
                UserType(
                    id=f"user_{i}",
                    name=f"User {i}",
                    email=f"user{i}@example.com",
                    created_at=datetime.now().isoformat()
                )
                for i in range(limit)
            ]

        def resolve_message(self, info, id):
            """解析單條消息"""
            return MessageType(
                id=id,
                content="Hello, world!",
                sender=UserType(
                    id="user_1",
                    name="John Doe",
                    email="john@example.com",
                    created_at=datetime.now().isoformat()
                ),
                timestamp=datetime.now().isoformat()
            )

        def resolve_messages(self, info, sender_id=None, limit=20):
            """解析消息列表"""
            return [
                MessageType(
                    id=f"msg_{i}",
                    content=f"Message {i}",
                    sender=UserType(
                        id=sender_id or f"user_{i}",
                        name=f"User {i}",
                        email=f"user{i}@example.com",
                        created_at=datetime.now().isoformat()
                    ),
                    timestamp=datetime.now().isoformat()
                )
                for i in range(limit)
            ]

        def resolve_analytics(self, info, metric_name=None, start_date=None, end_date=None):
            """解析分析數據"""
            metrics = ["requests", "errors", "response_time", "users"]
            filtered_metrics = [metric_name] if metric_name else metrics

            return [
                AnalyticsType(
                    metric_name=metric,
                    value=100.0 * (i + 1),
                    timestamp=datetime.now().isoformat()
                )
                for i, metric in enumerate(filtered_metrics)
            ]


    class CreateUser(graphene.Mutation):
        """創建用戶 Mutation"""

        class Arguments:
            name = String(required=True)
            email = String(required=True)

        user = Field(UserType)

        def mutate(self, info, name, email):
            user = UserType(
                id=f"user_{datetime.now().timestamp()}",
                name=name,
                email=email,
                created_at=datetime.now().isoformat()
            )
            return CreateUser(user=user)


    class SendMessage(graphene.Mutation):
        """發送消息 Mutation"""

        class Arguments:
            sender_id = String(required=True)
            content = String(required=True)

        message = Field(MessageType)

        def mutate(self, info, sender_id, content):
            message = MessageType(
                id=f"msg_{datetime.now().timestamp()}",
                content=content,
                sender=UserType(
                    id=sender_id,
                    name="Sender",
                    email="sender@example.com",
                    created_at=datetime.now().isoformat()
                ),
                timestamp=datetime.now().isoformat()
            )
            return SendMessage(message=message)


    class Mutation(ObjectType):
        """Mutation 根類型"""
        create_user = CreateUser.Field()
        send_message = SendMessage.Field()


class GraphQLServer:
    """GraphQL 服務器"""

    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        """
        初始化 GraphQL 服務器

        Args:
            host: 主機地址
            port: 端口號
        """
        if not HAS_GRAPHENE:
            raise ImportError("需要安裝 graphene: pip install graphene")
        if not HAS_FLASK:
            raise ImportError("需要安裝 flask: pip install flask flask-graphql")

        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.schema = Schema(query=Query, mutation=Mutation)

        # 設置 GraphQL 端點
        self.app.add_url_rule(
            '/graphql',
            view_func=GraphQLView.as_view(
                'graphql',
                schema=self.schema,
                graphiql=True  # 啟用 GraphiQL 交互式界面
            )
        )

        # 添加健康檢查端點
        @self.app.route('/health')
        def health():
            return jsonify({'status': 'healthy'})

    def run(self, debug: bool = True):
        """
        運行服務器

        Args:
            debug: 是否啟用調試模式
        """
        print(f"🚀 GraphQL 服務器啟動: http://{self.host}:{self.port}/graphql")
        print(f"📊 GraphiQL 界面: http://{self.host}:{self.port}/graphql")
        self.app.run(host=self.host, port=self.port, debug=debug)


class GraphQLClient:
    """GraphQL 客戶端"""

    # Security constants
    REQUEST_TIMEOUT = 30  # 30 seconds timeout for HTTP requests
    MAX_QUERY_LENGTH = 10000  # Maximum query length in characters

    def __init__(self, endpoint: str, rate_limit: Optional[float] = None):
        """
        初始化 GraphQL 客戶端

        Args:
            endpoint: GraphQL API 端點
            rate_limit: Maximum requests per second (e.g., 2.0 = 2 requests/sec).
                       If None, no rate limiting is applied.
        """
        self.endpoint = endpoint
        self.rate_limiter = RateLimiter(rate_limit) if rate_limit else None

    def _validate_query(self, query: str) -> None:
        """
        驗證 GraphQL 查詢

        Args:
            query: GraphQL 查詢字符串

        Raises:
            ValueError: 如果查詢無效
        """
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValueError(f"Query too long. Maximum length: {self.MAX_QUERY_LENGTH} characters")

        # Check for basic GraphQL syntax
        if not any(keyword in query for keyword in ['query', 'mutation', 'subscription', '{']):
            raise ValueError("Invalid GraphQL query format")

        # Prevent potential injection attacks - check for suspicious patterns
        suspicious_patterns = [
            r'__schema',  # Introspection (might be okay, but flag it)
            r'system\s*\(',  # System calls
            r'eval\s*\(',  # Eval calls
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                print(f"Warning: Query contains potentially suspicious pattern: {pattern}")

    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        執行 GraphQL 查詢

        Args:
            query: GraphQL 查詢字符串
            variables: 查詢變量
            headers: HTTP 請求頭

        Returns:
            查詢結果

        Raises:
            ValueError: 如果查詢無效或響應格式錯誤
        """
        import requests

        # Apply rate limiting if configured
        if self.rate_limiter:
            self.rate_limiter.wait_for_token()

        # Validate query before sending
        self._validate_query(query)

        payload = {'query': query}
        if variables:
            payload['variables'] = variables

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers or {},
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            # Validate response content type before parsing JSON
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                raise ValueError(f"Invalid response content type: {content_type}. Expected application/json")

            # Safely parse JSON response
            try:
                result = response.json()
            except ValueError as e:
                raise ValueError(f"Failed to parse JSON response: {e}")

            # Validate response structure
            if not isinstance(result, dict):
                raise ValueError("Response must be a JSON object")

            return result

        except requests.Timeout:
            raise TimeoutError(f"Request timed out after {self.REQUEST_TIMEOUT} seconds")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def query_user(self, user_id: str) -> Dict[str, Any]:
        """
        查詢單個用戶

        Args:
            user_id: 用戶 ID

        Returns:
            用戶數據
        """
        query = """
        query GetUser($id: String!) {
            user(id: $id) {
                id
                name
                email
                createdAt
            }
        }
        """
        return self.execute(query, variables={'id': user_id})

    def query_messages(
        self,
        sender_id: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        查詢消息列表

        Args:
            sender_id: 發送者 ID
            limit: 限制數量

        Returns:
            消息列表
        """
        query = """
        query GetMessages($senderId: String, $limit: Int) {
            messages(senderId: $senderId, limit: $limit) {
                id
                content
                sender {
                    id
                    name
                }
                timestamp
            }
        }
        """
        variables = {'limit': limit}
        if sender_id:
            variables['senderId'] = sender_id

        return self.execute(query, variables=variables)

    def create_user(self, name: str, email: str) -> Dict[str, Any]:
        """
        創建用戶

        Args:
            name: 用戶名
            email: 郵箱

        Returns:
            創建的用戶數據
        """
        mutation = """
        mutation CreateUser($name: String!, $email: String!) {
            createUser(name: $name, email: $email) {
                user {
                    id
                    name
                    email
                    createdAt
                }
            }
        }
        """
        return self.execute(mutation, variables={'name': name, 'email': email})

    def send_message(self, sender_id: str, content: str) -> Dict[str, Any]:
        """
        發送消息

        Args:
            sender_id: 發送者 ID
            content: 消息內容

        Returns:
            發送的消息數據
        """
        mutation = """
        mutation SendMessage($senderId: String!, $content: String!) {
            sendMessage(senderId: $senderId, content: $content) {
                message {
                    id
                    content
                    sender {
                        id
                        name
                    }
                    timestamp
                }
            }
        }
        """
        return self.execute(
            mutation,
            variables={'senderId': sender_id, 'content': content}
        )


__all__ = ['GraphQLServer', 'GraphQLClient', 'Query', 'Mutation', 'Schema']
