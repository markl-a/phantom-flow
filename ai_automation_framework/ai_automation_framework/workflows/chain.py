"""Chain for sequential processing."""

from typing import List, Callable, Any, Dict, Optional
from ai_automation_framework.core.base import BaseComponent


class Chain(BaseComponent):
    """
    Chain for sequential processing of tasks.

    Each step in the chain receives the output of the previous step.
    """

    def __init__(self, steps: Optional[List[Callable]] = None, **kwargs):
        """
        Initialize the chain.

        Args:
            steps: List of processing steps (functions)
            **kwargs: Additional configuration
        """
        super().__init__(name="Chain", **kwargs)
        self.steps = steps or []

    def _initialize(self) -> None:
        """Initialize the chain."""
        self.logger.info(f"Initialized Chain with {len(self.steps)} steps")

    def add_step(self, step: Callable) -> "Chain":
        """
        Add a step to the chain.

        Args:
            step: Processing function

        Returns:
            Self for chaining

        Raises:
            TypeError: If step is not callable
        """
        if not callable(step):
            raise TypeError(f"Step must be callable, got {type(step).__name__}")
        self.steps.append(step)
        return self

    def run(self, initial_input: Any) -> Any:
        """
        Run the chain with initial input.

        Args:
            initial_input: Initial input to the chain

        Returns:
            Final output after all steps

        Raises:
            ValueError: If initial_input is None
            RuntimeError: If step execution fails
        """
        if initial_input is None:
            raise ValueError("initial_input cannot be None")

        self.initialize()

        current_output = initial_input
        self.logger.info(f"Starting chain execution with {len(self.steps)} steps")

        for i, step in enumerate(self.steps, 1):
            step_name = getattr(step, '__name__', f'<step_{i}>')
            self.logger.debug(f"Executing step {i}/{len(self.steps)}: {step_name}")
            try:
                current_output = step(current_output)
            except Exception as e:
                error_msg = f"Error executing step {i}/{len(self.steps)} ({step_name}): {str(e)}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg) from e

        self.logger.info("Chain execution completed")
        return current_output

    def __call__(self, initial_input: Any) -> Any:
        """Make chain callable."""
        return self.run(initial_input)
