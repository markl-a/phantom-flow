"""
Memory Store for Agent Persistence.

This module provides persistent storage backends for agent memory,
enabling agents to maintain conversation history across sessions.

Supported backends:
- SQLite: Local file-based storage (default)
- Redis: Distributed in-memory storage
- JSON File: Simple file-based storage
"""

import json
import sqlite3
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict, field

from ai_automation_framework.core.base import Message


@dataclass
class ConversationMetadata:
    """Metadata for a conversation session."""
    conversation_id: str
    agent_name: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_count: int = 0
    system_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseMemoryStore(ABC):
    """Abstract base class for memory storage backends."""

    @abstractmethod
    def save_messages(
        self,
        conversation_id: str,
        messages: List[Message],
        agent_name: str = "Agent",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save messages to storage.

        Args:
            conversation_id: Unique identifier for the conversation
            messages: List of messages to save
            agent_name: Name of the agent
            metadata: Optional additional metadata
        """
        pass

    @abstractmethod
    def load_messages(
        self,
        conversation_id: str
    ) -> List[Message]:
        """
        Load messages from storage.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            List of messages
        """
        pass

    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from storage.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    def list_conversations(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ConversationMetadata]:
        """
        List all conversations.

        Args:
            agent_name: Filter by agent name
            limit: Maximum number of conversations to return

        Returns:
            List of conversation metadata
        """
        pass

    @abstractmethod
    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        pass

    def generate_conversation_id(self, prefix: str = "") -> str:
        """Generate a unique conversation ID."""
        import uuid
        base_id = str(uuid.uuid4())
        if prefix:
            return f"{prefix}_{base_id}"
        return base_id


class SQLiteMemoryStore(BaseMemoryStore):
    """
    SQLite-based memory storage.

    Provides persistent, file-based storage for agent memory.
    Suitable for single-instance applications.

    Example:
        >>> store = SQLiteMemoryStore("./data/memory.db")
        >>> store.save_messages("conv_123", messages)
        >>> loaded = store.load_messages("conv_123")
    """

    def __init__(
        self,
        db_path: Union[str, Path] = "./data/agent_memory.db",
        table_prefix: str = "agent_memory"
    ):
        """
        Initialize SQLite memory store.

        Args:
            db_path: Path to SQLite database file
            table_prefix: Prefix for table names
        """
        self.db_path = Path(db_path)
        self.table_prefix = table_prefix

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Conversations table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_prefix}_conversations (
                    conversation_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    system_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)

            # Messages table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_prefix}_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message_metadata TEXT,
                    FOREIGN KEY (conversation_id)
                        REFERENCES {self.table_prefix}_conversations(conversation_id)
                        ON DELETE CASCADE
                )
            """)

            # Index for faster lookups
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON {self.table_prefix}_messages(conversation_id)
            """)

            conn.commit()

    def save_messages(
        self,
        conversation_id: str,
        messages: List[Message],
        agent_name: str = "Agent",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save messages to SQLite database."""
        now = datetime.utcnow().isoformat()

        # Extract system message if present
        system_message = None
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                break

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if conversation exists
            cursor.execute(
                f"SELECT conversation_id FROM {self.table_prefix}_conversations WHERE conversation_id = ?",
                (conversation_id,)
            )
            exists = cursor.fetchone() is not None

            if exists:
                # Update existing conversation
                cursor.execute(f"""
                    UPDATE {self.table_prefix}_conversations
                    SET updated_at = ?, message_count = ?, metadata = ?
                    WHERE conversation_id = ?
                """, (now, len(messages), json.dumps(metadata or {}), conversation_id))

                # Delete existing messages
                cursor.execute(
                    f"DELETE FROM {self.table_prefix}_messages WHERE conversation_id = ?",
                    (conversation_id,)
                )
            else:
                # Create new conversation
                cursor.execute(f"""
                    INSERT INTO {self.table_prefix}_conversations
                    (conversation_id, agent_name, system_message, created_at, updated_at, message_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (conversation_id, agent_name, system_message, now, now, len(messages), json.dumps(metadata or {})))

            # Insert messages
            for msg in messages:
                cursor.execute(f"""
                    INSERT INTO {self.table_prefix}_messages
                    (conversation_id, role, content, timestamp, message_metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, msg.role, msg.content, now, json.dumps({})))

            conn.commit()

    def load_messages(self, conversation_id: str) -> List[Message]:
        """Load messages from SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT role, content FROM {self.table_prefix}_messages
                WHERE conversation_id = ?
                ORDER BY id ASC
            """, (conversation_id,))

            messages = []
            for row in cursor.fetchall():
                messages.append(Message(role=row['role'], content=row['content']))

            return messages

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete messages first (due to foreign key)
            cursor.execute(
                f"DELETE FROM {self.table_prefix}_messages WHERE conversation_id = ?",
                (conversation_id,)
            )

            # Delete conversation
            cursor.execute(
                f"DELETE FROM {self.table_prefix}_conversations WHERE conversation_id = ?",
                (conversation_id,)
            )

            conn.commit()
            return cursor.rowcount > 0

    def list_conversations(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ConversationMetadata]:
        """List conversations from SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if agent_name:
                cursor.execute(f"""
                    SELECT * FROM {self.table_prefix}_conversations
                    WHERE agent_name = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (agent_name, limit))
            else:
                cursor.execute(f"""
                    SELECT * FROM {self.table_prefix}_conversations
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,))

            conversations = []
            for row in cursor.fetchall():
                conversations.append(ConversationMetadata(
                    conversation_id=row['conversation_id'],
                    agent_name=row['agent_name'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    message_count=row['message_count'],
                    system_message=row['system_message'],
                    metadata=json.loads(row['metadata'] or '{}')
                ))

            return conversations

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if conversation exists in SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT 1 FROM {self.table_prefix}_conversations WHERE conversation_id = ?",
                (conversation_id,)
            )
            return cursor.fetchone() is not None


class RedisMemoryStore(BaseMemoryStore):
    """
    Redis-based memory storage.

    Provides distributed, in-memory storage for agent memory.
    Suitable for multi-instance applications with high availability needs.

    Example:
        >>> store = RedisMemoryStore(host="localhost", port=6379)
        >>> store.save_messages("conv_123", messages)
        >>> loaded = store.load_messages("conv_123")
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "agent_memory:",
        ttl: Optional[int] = None,  # Time-to-live in seconds
        **kwargs
    ):
        """
        Initialize Redis memory store.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Key prefix for namespacing
            ttl: Optional TTL for keys (in seconds)
            **kwargs: Additional Redis connection parameters
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self.ttl = ttl
        self.kwargs = kwargs
        self._client = None

    def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                    **self.kwargs
                )
            except ImportError:
                raise ImportError(
                    "redis package is required for RedisMemoryStore. "
                    "Install it with: pip install redis"
                )
        return self._client

    def _conversation_key(self, conversation_id: str) -> str:
        """Get Redis key for conversation metadata."""
        return f"{self.prefix}conv:{conversation_id}"

    def _messages_key(self, conversation_id: str) -> str:
        """Get Redis key for messages list."""
        return f"{self.prefix}msgs:{conversation_id}"

    def _index_key(self, agent_name: str = "_all") -> str:
        """Get Redis key for conversation index."""
        return f"{self.prefix}index:{agent_name}"

    def save_messages(
        self,
        conversation_id: str,
        messages: List[Message],
        agent_name: str = "Agent",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save messages to Redis."""
        client = self._get_client()
        now = datetime.utcnow().isoformat()

        # Extract system message
        system_message = None
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                break

        # Check if conversation exists
        exists = client.exists(self._conversation_key(conversation_id))

        # Save conversation metadata
        conv_data = {
            "conversation_id": conversation_id,
            "agent_name": agent_name,
            "system_message": system_message or "",
            "created_at": client.hget(self._conversation_key(conversation_id), "created_at") or now if exists else now,
            "updated_at": now,
            "message_count": len(messages),
            "metadata": json.dumps(metadata or {})
        }
        client.hset(self._conversation_key(conversation_id), mapping=conv_data)

        # Save messages
        messages_key = self._messages_key(conversation_id)
        client.delete(messages_key)  # Clear existing messages

        for msg in messages:
            msg_data = json.dumps({"role": msg.role, "content": msg.content})
            client.rpush(messages_key, msg_data)

        # Add to indexes
        client.sadd(self._index_key("_all"), conversation_id)
        client.sadd(self._index_key(agent_name), conversation_id)

        # Set TTL if configured
        if self.ttl:
            client.expire(self._conversation_key(conversation_id), self.ttl)
            client.expire(messages_key, self.ttl)

    def load_messages(self, conversation_id: str) -> List[Message]:
        """Load messages from Redis."""
        client = self._get_client()
        messages_key = self._messages_key(conversation_id)

        messages = []
        raw_messages = client.lrange(messages_key, 0, -1)

        for raw_msg in raw_messages:
            msg_data = json.loads(raw_msg)
            messages.append(Message(role=msg_data["role"], content=msg_data["content"]))

        return messages

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from Redis."""
        client = self._get_client()

        # Get agent name before deletion for index cleanup
        agent_name = client.hget(self._conversation_key(conversation_id), "agent_name")

        # Delete keys
        deleted = client.delete(
            self._conversation_key(conversation_id),
            self._messages_key(conversation_id)
        )

        # Remove from indexes
        client.srem(self._index_key("_all"), conversation_id)
        if agent_name:
            client.srem(self._index_key(agent_name), conversation_id)

        return deleted > 0

    def list_conversations(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ConversationMetadata]:
        """List conversations from Redis."""
        client = self._get_client()

        # Get conversation IDs from index
        index_key = self._index_key(agent_name) if agent_name else self._index_key("_all")
        conversation_ids = client.smembers(index_key)

        conversations = []
        for conv_id in list(conversation_ids)[:limit]:
            conv_key = self._conversation_key(conv_id)
            conv_data = client.hgetall(conv_key)

            if conv_data:
                conversations.append(ConversationMetadata(
                    conversation_id=conv_data.get("conversation_id", conv_id),
                    agent_name=conv_data.get("agent_name", "Unknown"),
                    created_at=conv_data.get("created_at", ""),
                    updated_at=conv_data.get("updated_at", ""),
                    message_count=int(conv_data.get("message_count", 0)),
                    system_message=conv_data.get("system_message") or None,
                    metadata=json.loads(conv_data.get("metadata", "{}"))
                ))

        # Sort by updated_at
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if conversation exists in Redis."""
        client = self._get_client()
        return client.exists(self._conversation_key(conversation_id)) > 0


class JSONFileMemoryStore(BaseMemoryStore):
    """
    JSON file-based memory storage.

    Simple file-based storage where each conversation is stored as a JSON file.
    Suitable for development and simple use cases.

    Example:
        >>> store = JSONFileMemoryStore("./data/conversations")
        >>> store.save_messages("conv_123", messages)
    """

    def __init__(self, storage_dir: Union[str, Path] = "./data/conversations"):
        """
        Initialize JSON file memory store.

        Args:
            storage_dir: Directory to store conversation files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _conversation_path(self, conversation_id: str) -> Path:
        """Get file path for a conversation."""
        # Use hash to avoid filesystem issues with special characters
        safe_id = hashlib.md5(conversation_id.encode()).hexdigest()[:16]
        return self.storage_dir / f"{safe_id}.json"

    def _index_path(self) -> Path:
        """Get path to conversation index file."""
        return self.storage_dir / "_index.json"

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load conversation index."""
        index_path = self._index_path()
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        """Save conversation index."""
        with open(self._index_path(), 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)

    def save_messages(
        self,
        conversation_id: str,
        messages: List[Message],
        agent_name: str = "Agent",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save messages to JSON file."""
        now = datetime.utcnow().isoformat()

        # Extract system message
        system_message = None
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                break

        # Load existing or create new
        conv_path = self._conversation_path(conversation_id)
        if conv_path.exists():
            with open(conv_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            created_at = data.get("created_at", now)
        else:
            created_at = now

        # Prepare data
        data = {
            "conversation_id": conversation_id,
            "agent_name": agent_name,
            "system_message": system_message,
            "created_at": created_at,
            "updated_at": now,
            "message_count": len(messages),
            "metadata": metadata or {},
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages]
        }

        # Save conversation file
        with open(conv_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Update index
        index = self._load_index()
        index[conversation_id] = {
            "file": conv_path.name,
            "agent_name": agent_name,
            "updated_at": now,
            "message_count": len(messages)
        }
        self._save_index(index)

    def load_messages(self, conversation_id: str) -> List[Message]:
        """Load messages from JSON file."""
        conv_path = self._conversation_path(conversation_id)

        if not conv_path.exists():
            return []

        with open(conv_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = []
        for msg_data in data.get("messages", []):
            messages.append(Message(role=msg_data["role"], content=msg_data["content"]))

        return messages

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation JSON file."""
        conv_path = self._conversation_path(conversation_id)

        if conv_path.exists():
            conv_path.unlink()

            # Update index
            index = self._load_index()
            if conversation_id in index:
                del index[conversation_id]
                self._save_index(index)

            return True
        return False

    def list_conversations(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ConversationMetadata]:
        """List conversations from index."""
        index = self._load_index()

        conversations = []
        for conv_id, info in index.items():
            if agent_name and info.get("agent_name") != agent_name:
                continue

            conv_path = self._conversation_path(conv_id)
            if conv_path.exists():
                with open(conv_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                conversations.append(ConversationMetadata(
                    conversation_id=conv_id,
                    agent_name=data.get("agent_name", "Unknown"),
                    created_at=data.get("created_at", ""),
                    updated_at=data.get("updated_at", ""),
                    message_count=data.get("message_count", 0),
                    system_message=data.get("system_message"),
                    metadata=data.get("metadata", {})
                ))

        # Sort by updated_at and limit
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations[:limit]

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if conversation file exists."""
        return self._conversation_path(conversation_id).exists()


class MemoryStoreFactory:
    """Factory for creating memory store instances."""

    _stores = {
        "sqlite": SQLiteMemoryStore,
        "redis": RedisMemoryStore,
        "json": JSONFileMemoryStore,
    }

    @classmethod
    def create(cls, store_type: str = "sqlite", **kwargs) -> BaseMemoryStore:
        """
        Create a memory store instance.

        Args:
            store_type: Type of store ("sqlite", "redis", "json")
            **kwargs: Store-specific configuration

        Returns:
            Memory store instance

        Example:
            >>> store = MemoryStoreFactory.create("sqlite", db_path="./memory.db")
            >>> store = MemoryStoreFactory.create("redis", host="localhost", port=6379)
        """
        store_type = store_type.lower()
        if store_type not in cls._stores:
            available = ", ".join(cls._stores.keys())
            raise ValueError(f"Unknown store type '{store_type}'. Available: {available}")

        return cls._stores[store_type](**kwargs)

    @classmethod
    def register(cls, name: str, store_class: type) -> None:
        """Register a custom memory store class."""
        if not issubclass(store_class, BaseMemoryStore):
            raise TypeError("Store class must inherit from BaseMemoryStore")
        cls._stores[name.lower()] = store_class
