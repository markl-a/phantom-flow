"""
Persistent Agent with Memory Store Integration.

This module provides an agent that automatically persists conversation
history to a storage backend (SQLite, Redis, or JSON files).
"""

from typing import List, Dict, Any, Optional, Union
from ai_automation_framework.core.base import Message
from ai_automation_framework.agents.base_agent import BaseAgent
from ai_automation_framework.agents.memory_store import (
    BaseMemoryStore,
    SQLiteMemoryStore,
    MemoryStoreFactory,
    ConversationMetadata,
)
from ai_automation_framework.llm import BaseLLMClient


class PersistentAgent(BaseAgent):
    """
    Agent with persistent memory storage.

    Extends BaseAgent to automatically save and load conversation history
    from a persistent storage backend.

    Features:
    - Automatic memory persistence after each interaction
    - Resume conversations from previous sessions
    - Support for multiple storage backends (SQLite, Redis, JSON)
    - Conversation management (list, delete, export)

    Example:
        >>> from ai_automation_framework.agents import PersistentAgent
        >>>
        >>> # Create agent with SQLite storage
        >>> agent = PersistentAgent(
        ...     name="MyAssistant",
        ...     conversation_id="user_123_session_1",
        ...     system_message="You are a helpful assistant."
        ... )
        >>>
        >>> # Chat (automatically persisted)
        >>> response = agent.chat("Hello!")
        >>>
        >>> # Later, resume the conversation
        >>> agent2 = PersistentAgent(
        ...     name="MyAssistant",
        ...     conversation_id="user_123_session_1"
        ... )
        >>> response = agent2.chat("What did I say before?")
    """

    def __init__(
        self,
        name: str = "PersistentAgent",
        llm: Optional[BaseLLMClient] = None,
        system_message: Optional[str] = None,
        conversation_id: Optional[str] = None,
        memory_store: Optional[BaseMemoryStore] = None,
        store_type: str = "sqlite",
        store_config: Optional[Dict[str, Any]] = None,
        auto_save: bool = True,
        auto_load: bool = True,
        **kwargs: Any
    ) -> None:
        """
        Initialize persistent agent.

        Args:
            name: Agent name
            llm: LLM client
            system_message: System message defining agent's role
            conversation_id: Unique ID for this conversation (auto-generated if None)
            memory_store: Custom memory store instance
            store_type: Type of memory store ("sqlite", "redis", "json")
            store_config: Configuration for the memory store
            auto_save: Automatically save after each interaction
            auto_load: Automatically load existing conversation on init
            **kwargs: Additional configuration
        """
        # Initialize memory store before parent init
        if memory_store:
            self.memory_store = memory_store
        else:
            store_config = store_config or {}
            self.memory_store = MemoryStoreFactory.create(store_type, **store_config)

        self.conversation_id = conversation_id or self.memory_store.generate_conversation_id(name)
        self.auto_save = auto_save
        self.auto_load = auto_load
        self._metadata: Dict[str, Any] = kwargs.pop('metadata', {})

        # Initialize parent (this sets up memory list)
        super().__init__(name=name, llm=llm, system_message=system_message, **kwargs)

        # Load existing conversation if available and auto_load is enabled
        if self.auto_load and self.memory_store.conversation_exists(self.conversation_id):
            self._load_conversation()

    def _load_conversation(self) -> None:
        """Load conversation from memory store."""
        loaded_messages = self.memory_store.load_messages(self.conversation_id)
        if loaded_messages:
            self.memory = loaded_messages
            self.logger.info(
                f"Loaded {len(loaded_messages)} messages for conversation {self.conversation_id}"
            )

            # Extract system message if present
            for msg in loaded_messages:
                if msg.role == "system":
                    self.system_message = msg.content
                    break

    def _save_conversation(self) -> None:
        """Save conversation to memory store."""
        self.memory_store.save_messages(
            conversation_id=self.conversation_id,
            messages=self.memory,
            agent_name=self.name,
            metadata=self._metadata
        )
        self.logger.debug(
            f"Saved {len(self.memory)} messages for conversation {self.conversation_id}"
        )

    def add_message(self, role: str, content: str) -> None:
        """Add a message to memory and optionally persist."""
        super().add_message(role, content)
        if self.auto_save:
            self._save_conversation()

    def chat(self, user_message: str, **kwargs: Any) -> str:
        """
        Chat with the agent (persisted automatically).

        Args:
            user_message: User's message
            **kwargs: Additional parameters for LLM

        Returns:
            Agent's response
        """
        response = super().chat(user_message, **kwargs)

        # Save is handled by add_message if auto_save is enabled
        # But we ensure it's saved after the full exchange
        if self.auto_save:
            self._save_conversation()

        return response

    async def achat(self, user_message: str, **kwargs: Any) -> str:
        """
        Async chat with the agent.

        Args:
            user_message: User's message
            **kwargs: Additional parameters for LLM

        Returns:
            Agent's response
        """
        self.initialize()

        # Add user message to memory
        self.memory.append(Message(role="user", content=user_message))

        # Get response from LLM
        response = await self.llm.achat(self.memory, **kwargs)

        # Validate response
        if response is None or not hasattr(response, 'content') or response.content is None:
            self.logger.error("Invalid response from LLM: missing or null content")
            raise ValueError("LLM returned invalid response")

        # Add assistant response to memory
        self.memory.append(Message(role="assistant", content=response.content))

        # Save conversation
        if self.auto_save:
            self._save_conversation()

        return response.content

    def save(self) -> None:
        """Manually save the current conversation."""
        self._save_conversation()

    def load(self) -> None:
        """Manually load the conversation from storage."""
        self._load_conversation()

    def clear_memory(self, keep_system: bool = True, delete_from_store: bool = False) -> None:
        """
        Clear conversation memory.

        Args:
            keep_system: Whether to keep system message
            delete_from_store: Whether to also delete from persistent storage
        """
        super().clear_memory(keep_system)

        if delete_from_store:
            self.memory_store.delete_conversation(self.conversation_id)
        elif self.auto_save:
            self._save_conversation()

    def new_conversation(self, conversation_id: Optional[str] = None) -> str:
        """
        Start a new conversation.

        Args:
            conversation_id: Optional ID for new conversation (auto-generated if None)

        Returns:
            New conversation ID
        """
        self.conversation_id = conversation_id or self.memory_store.generate_conversation_id(self.name)
        self.clear_memory(keep_system=True, delete_from_store=False)

        if self.auto_save:
            self._save_conversation()

        self.logger.info(f"Started new conversation: {self.conversation_id}")
        return self.conversation_id

    def switch_conversation(self, conversation_id: str) -> bool:
        """
        Switch to a different conversation.

        Args:
            conversation_id: ID of the conversation to switch to

        Returns:
            True if conversation was found and loaded
        """
        if not self.memory_store.conversation_exists(conversation_id):
            self.logger.warning(f"Conversation {conversation_id} not found")
            return False

        # Save current conversation first
        if self.auto_save:
            self._save_conversation()

        # Switch to new conversation
        self.conversation_id = conversation_id
        self._load_conversation()

        self.logger.info(f"Switched to conversation: {conversation_id}")
        return True

    def list_conversations(self, limit: int = 100) -> List[ConversationMetadata]:
        """
        List all conversations for this agent.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversation metadata
        """
        return self.memory_store.list_conversations(agent_name=self.name, limit=limit)

    def delete_conversation(self, conversation_id: Optional[str] = None) -> bool:
        """
        Delete a conversation from storage.

        Args:
            conversation_id: ID of conversation to delete (current if None)

        Returns:
            True if deleted successfully
        """
        target_id = conversation_id or self.conversation_id
        success = self.memory_store.delete_conversation(target_id)

        if success and target_id == self.conversation_id:
            # Clear current memory if we deleted current conversation
            self.clear_memory(keep_system=True)

        return success

    def export_conversation(self) -> Dict[str, Any]:
        """
        Export current conversation as a dictionary.

        Returns:
            Dictionary with conversation data
        """
        return {
            "conversation_id": self.conversation_id,
            "agent_name": self.name,
            "system_message": self.system_message,
            "messages": [{"role": msg.role, "content": msg.content} for msg in self.memory],
            "metadata": self._metadata
        }

    def import_conversation(
        self,
        data: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Import a conversation from a dictionary.

        Args:
            data: Conversation data dictionary
            conversation_id: Optional new ID (uses data's ID if None)

        Returns:
            Imported conversation ID
        """
        self.conversation_id = conversation_id or data.get("conversation_id", self.memory_store.generate_conversation_id(self.name))

        # Load messages
        self.memory = []
        system_msg = data.get("system_message")
        if system_msg:
            self.memory.append(Message(role="system", content=system_msg))
            self.system_message = system_msg

        for msg_data in data.get("messages", []):
            if msg_data["role"] != "system":  # Skip system as we already added it
                self.memory.append(Message(role=msg_data["role"], content=msg_data["content"]))

        self._metadata = data.get("metadata", {})

        if self.auto_save:
            self._save_conversation()

        return self.conversation_id

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value for the current conversation."""
        self._metadata[key] = value
        if self.auto_save:
            self._save_conversation()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value from the current conversation."""
        return self._metadata.get(key, default)

    def run(self, task: str, **kwargs: Any) -> str:
        """
        Run the agent on a task.

        For PersistentAgent, this is equivalent to chat.

        Args:
            task: Task description (treated as user message)
            **kwargs: Additional parameters

        Returns:
            Agent's response
        """
        return self.chat(task, **kwargs)

    def __enter__(self) -> "PersistentAgent":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures conversation is saved."""
        if self.auto_save:
            self._save_conversation()


class ConversationManager:
    """
    Manager for handling multiple agent conversations.

    Provides utilities for managing multiple conversations across agents.

    Example:
        >>> manager = ConversationManager()
        >>> agent = manager.get_or_create_agent("user_123", "Assistant")
        >>> response = agent.chat("Hello!")
    """

    def __init__(
        self,
        memory_store: Optional[BaseMemoryStore] = None,
        store_type: str = "sqlite",
        store_config: Optional[Dict[str, Any]] = None,
        default_llm: Optional[BaseLLMClient] = None
    ):
        """
        Initialize conversation manager.

        Args:
            memory_store: Shared memory store for all agents
            store_type: Type of memory store if not provided
            store_config: Configuration for memory store
            default_llm: Default LLM client for agents
        """
        if memory_store:
            self.memory_store = memory_store
        else:
            store_config = store_config or {}
            self.memory_store = MemoryStoreFactory.create(store_type, **store_config)

        self.default_llm = default_llm
        self._agents: Dict[str, PersistentAgent] = {}

    def get_or_create_agent(
        self,
        conversation_id: str,
        agent_name: str = "Agent",
        system_message: Optional[str] = None,
        llm: Optional[BaseLLMClient] = None,
        **kwargs
    ) -> PersistentAgent:
        """
        Get an existing agent or create a new one.

        Args:
            conversation_id: Unique conversation identifier
            agent_name: Name of the agent
            system_message: System message for new agents
            llm: LLM client (uses default if None)
            **kwargs: Additional agent configuration

        Returns:
            PersistentAgent instance
        """
        cache_key = f"{agent_name}:{conversation_id}"

        if cache_key not in self._agents:
            self._agents[cache_key] = PersistentAgent(
                name=agent_name,
                conversation_id=conversation_id,
                system_message=system_message,
                llm=llm or self.default_llm,
                memory_store=self.memory_store,
                **kwargs
            )

        return self._agents[cache_key]

    def list_all_conversations(self, limit: int = 100) -> List[ConversationMetadata]:
        """List all conversations across all agents."""
        return self.memory_store.list_conversations(limit=limit)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        # Remove from cache if present
        keys_to_remove = [k for k in self._agents if k.endswith(f":{conversation_id}")]
        for key in keys_to_remove:
            del self._agents[key]

        return self.memory_store.delete_conversation(conversation_id)

    def clear_cache(self) -> None:
        """Clear the agent cache."""
        self._agents.clear()
