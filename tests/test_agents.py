"""Tests for agents."""

import pytest
from unittest.mock import Mock, patch
from ai_automation_framework.agents import BaseAgent, ToolAgent, MultiAgentSystem


class TestBaseAgent:
    """Test base agent."""

    def test_agent_initialization(self):
        """Test agent initialization."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            agent = BaseAgent(
                name="TestAgent",
                system_message="You are helpful"
            )
            assert agent.name == "TestAgent"
            assert agent.system_message == "You are helpful"
            assert len(agent.memory) == 1  # System message

    def test_add_message(self):
        """Test adding messages to memory."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            agent = BaseAgent()
            agent.add_message("user", "Hello")
            assert len(agent.memory) >= 1

    def test_clear_memory(self):
        """Test clearing memory."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            agent = BaseAgent(system_message="System")
            agent.add_message("user", "Hello")
            agent.clear_memory(keep_system=True)
            assert len(agent.memory) == 1


class TestToolAgent:
    """Test tool agent."""

    def test_tool_registration(self):
        """Test registering a tool."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            agent = ToolAgent()

            def test_tool(x: int) -> int:
                return x * 2

            schema = {
                "type": "function",
                "function": {"name": "test_tool", "parameters": {}}
            }

            agent.register_tool("test_tool", test_tool, schema)
            assert "test_tool" in agent.tools


class TestMultiAgentSystem:
    """Test multi-agent system."""

    def test_system_initialization(self):
        """Test system initialization."""
        system = MultiAgentSystem()
        assert len(system.agents) == 0

    def test_register_agent(self):
        """Test registering an agent."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            system = MultiAgentSystem()
            agent = BaseAgent(name="Agent1")
            system.register_agent("agent1", agent)
            assert "agent1" in system.agents
