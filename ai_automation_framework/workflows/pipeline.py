"""Pipeline for complex workflow orchestration."""

from typing import Dict, Any, List, Callable, Optional
from ai_automation_framework.core.base import BaseComponent


class Pipeline(BaseComponent):
    """
    Pipeline for complex workflow orchestration.

    Supports branching, parallel execution, and conditional logic.
    """

    def __init__(self, name: str = "Pipeline", **kwargs):
        """
        Initialize the pipeline.

        Args:
            name: Pipeline name
            **kwargs: Additional configuration
        """
        super().__init__(name=name, **kwargs)
        self.stages: Dict[str, Callable] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.results: Dict[str, Any] = {}

    def _initialize(self) -> None:
        """Initialize the pipeline."""
        self.logger.info(f"Initialized Pipeline: {self.name}")

    def add_stage(
        self,
        name: str,
        function: Callable,
        depends_on: Optional[List[str]] = None
    ) -> "Pipeline":
        """
        Add a stage to the pipeline.

        Args:
            name: Stage name
            function: Processing function
            depends_on: List of stage names this stage depends on

        Returns:
            Self for chaining
        """
        self.stages[name] = function
        self.dependencies[name] = depends_on or []
        return self

    def _get_execution_order(self) -> List[str]:
        """
        Determine execution order based on dependencies using topological sort.

        Returns:
            List of stage names in execution order

        Raises:
            ValueError: If circular dependency is detected or dependency not found
        """
        # Use three-color marking for cycle detection
        # WHITE = not visited, GRAY = in progress, BLACK = completed
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {stage: WHITE for stage in self.stages}
        order = []

        def visit(stage: str):
            if color[stage] == GRAY:
                raise ValueError(f"Circular dependency detected involving stage: {stage}")
            if color[stage] == BLACK:
                return

            color[stage] = GRAY

            for dep in self.dependencies.get(stage, []):
                if dep not in self.stages:
                    raise ValueError(f"Dependency '{dep}' not found in pipeline stages")
                visit(dep)

            color[stage] = BLACK
            order.append(stage)

        for stage in self.stages:
            if color[stage] == WHITE:
                visit(stage)

        return order

    def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the pipeline.

        Args:
            initial_input: Initial input data

        Returns:
            Results from all stages
        """
        self.initialize()

        self.results = {"input": initial_input}
        execution_order = self._get_execution_order()

        self.logger.info(f"Executing pipeline with {len(self.stages)} stages")
        self.logger.debug(f"Execution order: {execution_order}")

        for stage_name in execution_order:
            self.logger.debug(f"Executing stage: {stage_name}")

            # Collect inputs from dependencies
            stage_input = {
                "input": initial_input,
                "results": self.results
            }

            # Execute stage
            function = self.stages[stage_name]
            result = function(stage_input)

            # Store result
            self.results[stage_name] = result

        self.logger.info("Pipeline execution completed")
        return self.results

    def __call__(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make pipeline callable."""
        return self.run(initial_input)
