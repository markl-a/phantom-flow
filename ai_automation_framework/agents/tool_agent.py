"""Tool-using agent implementation."""

from typing import List, Dict, Any, Callable, Optional
import json
from ai_automation_framework.agents.base_agent import BaseAgent
from ai_automation_framework.core.base import Message


class ToolAgent(BaseAgent):
    """
    Agent that can use tools to accomplish tasks.

    Combines LLM reasoning with tool execution for practical applications.
    """

    def __init__(
        self,
        name: str = "ToolAgent",
        tools: Optional[Dict[str, Callable]] = None,
        tool_schemas: Optional[List[Dict]] = None,
        max_iterations: int = 10,
        **kwargs
    ):
        """
        Initialize the tool agent.

        Args:
            name: Agent name
            tools: Dictionary of tool name -> function
            tool_schemas: OpenAI-style tool schemas
            max_iterations: Maximum reasoning iterations
            **kwargs: Additional configuration
        """
        system_message = """You are a helpful AI assistant with access to tools.
        When you need to use a tool, call the appropriate function.
        Always provide clear explanations of what you're doing."""

        super().__init__(name=name, system_message=system_message, **kwargs)

        self.tools = tools or {}
        self.tool_schemas = tool_schemas or []
        self.max_iterations = max_iterations

    def register_tool(
        self,
        name: str,
        function: Callable,
        schema: Dict[str, Any]
    ) -> None:
        """
        Register a new tool.

        Args:
            name: Tool name
            function: Tool function
            schema: OpenAI-style tool schema
        """
        self.tools[name] = function
        self.tool_schemas.append(schema)
        self.logger.info(f"Registered tool: {name}")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        self.logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        try:
            result = self.tools[tool_name](**arguments)
            return result
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}

    def run(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Run the agent on a task with tool use.

        Args:
            task: Task description
            **kwargs: Additional parameters

        Returns:
            Task result with execution trace
        """
        self.initialize()

        self.logger.info(f"Starting task: {task}")
        self.add_message("user", task)

        iterations = 0
        tool_calls_made = []

        while iterations < self.max_iterations:
            iterations += 1
            self.logger.debug(f"Iteration {iterations}/{self.max_iterations}")

            # Get response from LLM
            response = self.llm.chat(
                self.memory,
                tools=self.tool_schemas if self.tool_schemas else None,
                tool_choice="auto" if self.tool_schemas else None,
                **kwargs
            )

            # Check if we need to call tools
            if response is not None and getattr(response, 'tool_calls', None):
                # Process tool calls
                for tool_call in response.tool_calls:
                    # Validate tool_call structure
                    if not hasattr(tool_call, 'function'):
                        self.logger.warning(f"Invalid tool_call structure: missing 'function' attribute")
                        continue
                    if not hasattr(tool_call.function, 'name') or not hasattr(tool_call.function, 'arguments'):
                        self.logger.warning(f"Invalid tool_call.function structure: missing attributes")
                        continue

                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse tool arguments for {tool_name}: {e}")
                        continue

                    # Execute tool
                    tool_result = self.execute_tool(tool_name, arguments)

                    # Record tool call
                    tool_calls_made.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": tool_result
                    })

                    # Add to memory
                    self.add_message(
                        "assistant",
                        f"Calling tool: {tool_name}"
                    )
                    self.add_message(
                        "tool",
                        json.dumps(tool_result)
                    )

                # Continue to get final response
                continue

            # No tool calls needed, we have final answer
            self.add_message("assistant", response.content)

            return {
                "answer": response.content,
                "tool_calls": tool_calls_made,
                "iterations": iterations
            }

        # Max iterations reached
        self.logger.warning(f"Max iterations ({self.max_iterations}) reached")

        return {
            "answer": "Task incomplete: maximum iterations reached",
            "tool_calls": tool_calls_made,
            "iterations": iterations
        }
