"""Base agent implementation."""

from typing import List, Dict, Any, Optional
from abc import abstractmethod
from ai_automation_framework.core.base import BaseComponent, Message, Response
from ai_automation_framework.llm import BaseLLMClient, OpenAIClient


class BaseAgent(BaseComponent):
    """
    Base class for AI agents.

    An agent combines an LLM with memory, tools, and decision-making capabilities.
    """

    def __init__(
        self,
        name: str = "Agent",
        llm: Optional[BaseLLMClient] = None,
        system_message: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the agent.

        Args:
            name: Agent name
            llm: LLM client
            system_message: System message defining agent's role
            **kwargs: Additional configuration
        """
        super().__init__(name=name, **kwargs)
        self.llm: BaseLLMClient = llm or OpenAIClient()
        self.system_message: Optional[str] = system_message
        self.memory: List[Message] = []

        if system_message:
            self.memory.append(Message(role="system", content=system_message))

    def _initialize(self) -> None:
        """Initialize the agent."""
        try:
            self.llm.initialize()
            self.logger.info(f"Initialized agent: {self.name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM for agent {self.name}: {e}")
            raise

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to memory.

        Args:
            role: Message role
            content: Message content
        """
        valid_roles = {"user", "assistant", "system", "tool"}
        if role not in valid_roles:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}")
        self.memory.append(Message(role=role, content=content))

    def get_memory(self) -> List[Message]:
        """
        Get conversation memory.

        Returns:
            List of messages
        """
        return self.memory.copy()

    def clear_memory(self, keep_system: bool = True) -> None:
        """
        Clear conversation memory.

        Args:
            keep_system: Whether to keep system message
        """
        if keep_system and self.system_message:
            self.memory = [Message(role="system", content=self.system_message)]
        else:
            self.memory = []

    def chat(self, user_message: str, **kwargs: Any) -> str:
        """
        Chat with the agent.

        Args:
            user_message: User's message
            **kwargs: Additional parameters for LLM

        Returns:
            Agent's response
        """
        self.initialize()

        # Add user message to memory
        self.add_message("user", user_message)

        # Get response from LLM
        try:
            response: Response = self.llm.chat(self.memory, **kwargs)
        except Exception as e:
            self.logger.error(f"LLM chat failed: {e}")
            raise

        # Validate response content
        if response is None or not hasattr(response, 'content') or response.content is None:
            self.logger.error("Invalid response from LLM: missing or null content")
            raise ValueError("LLM returned invalid response")

        # Add assistant response to memory
        self.add_message("assistant", response.content)

        return response.content

    @abstractmethod
    def run(self, task: str, **kwargs: Any) -> Any:
        """
        Run the agent on a task.

        Args:
            task: Task description
            **kwargs: Additional parameters

        Returns:
            Task result
        """
        pass

    def __call__(self, task: str, **kwargs: Any) -> Any:
        """Make agent callable."""
        return self.run(task, **kwargs)
