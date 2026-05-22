"""Multi-agent system implementation."""

import asyncio
from typing import List, Dict, Any, Optional
from ai_automation_framework.core.base import BaseComponent
from ai_automation_framework.agents.base_agent import BaseAgent


class MultiAgentSystem(BaseComponent):
    """
    Multi-agent system for collaborative problem solving.

    Coordinates multiple specialized agents to work together on complex tasks.
    """

    def __init__(
        self,
        name: str = "MultiAgentSystem",
        agents: Optional[Dict[str, BaseAgent]] = None,
        **kwargs
    ):
        """
        Initialize the multi-agent system.

        Args:
            name: System name
            agents: Dictionary of agent name -> agent instance
            **kwargs: Additional configuration
        """
        super().__init__(name=name, **kwargs)
        self.agents = {}
        self.conversation_history: List[Dict[str, Any]] = []

        # Validate and add agents
        if agents:
            for agent_name, agent in agents.items():
                if not isinstance(agent, BaseAgent):
                    raise TypeError(f"Agent '{agent_name}' must be an instance of BaseAgent, got {type(agent).__name__}")
                self.agents[agent_name] = agent

    def _initialize(self) -> None:
        """Initialize the system."""
        for agent in self.agents.values():
            agent.initialize()
        self.logger.info(f"Initialized MultiAgentSystem with {len(self.agents)} agents")

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register an agent in the system.

        Args:
            name: Agent name
            agent: Agent instance
        """
        if not isinstance(agent, BaseAgent):
            raise TypeError(f"Agent must be an instance of BaseAgent, got {type(agent).__name__}")
        self.agents[name] = agent
        self.logger.info(f"Registered agent: {name}")

    def get_agent(self, name: str) -> BaseAgent:
        """
        Get an agent by name.

        Args:
            name: Agent name

        Returns:
            Agent instance
        """
        if name not in self.agents:
            raise ValueError(f"Agent not found: {name}")
        return self.agents[name]

    def sequential_execution(
        self,
        task: str,
        agent_sequence: List[str]
    ) -> Dict[str, Any]:
        """
        Execute task sequentially through multiple agents.

        Args:
            task: Initial task
            agent_sequence: List of agent names in order

        Returns:
            Results from each agent
        """
        if not agent_sequence:
            raise ValueError("agent_sequence cannot be empty")

        self.initialize()

        results = {}
        current_input = task

        self.logger.info(f"Sequential execution: {' -> '.join(agent_sequence)}")

        for agent_name in agent_sequence:
            agent = self.get_agent(agent_name)
            self.logger.info(f"Executing with agent: {agent_name}")

            try:
                result = agent.run(current_input)
            except Exception as e:
                self.logger.error(f"Agent {agent_name} failed: {e}")
                result = {"error": str(e), "agent": agent_name}

            results[agent_name] = result
            self.conversation_history.append({
                "agent": agent_name,
                "input": current_input,
                "output": result
            })

            # Use output as input for next agent
            if isinstance(result, dict) and "answer" in result:
                current_input = result["answer"]
            else:
                current_input = str(result)

        return results

    def collaborative_execution(
        self,
        task: str,
        coordinator_agent: str,
        worker_agents: List[str]
    ) -> Dict[str, Any]:
        """
        Execute task with coordinator-worker pattern.

        Args:
            task: Task description
            coordinator_agent: Name of coordinator agent
            worker_agents: List of worker agent names

        Returns:
            Execution results
        """
        if not worker_agents:
            raise ValueError("worker_agents cannot be empty")

        self.initialize()

        coordinator = self.get_agent(coordinator_agent)
        self.logger.info(f"Collaborative execution coordinated by: {coordinator_agent}")

        # Coordinator plans the work
        planning_prompt = f"""
        Task: {task}

        Available workers: {', '.join(worker_agents)}

        Plan how to distribute this task among the available workers.
        For each worker, describe what they should do.
        """

        try:
            plan = coordinator.chat(planning_prompt)
            self.logger.info(f"Coordinator created plan")
        except Exception as e:
            self.logger.error(f"Coordinator planning failed: {e}")
            raise

        # Execute with workers
        worker_results = {}
        for worker_name in worker_agents:
            worker = self.get_agent(worker_name)

            worker_task = f"""
            Original task: {task}

            Coordinator's plan: {plan}

            Your role as {worker_name}: Execute your part of the plan.
            """

            try:
                result = worker.run(worker_task)
            except Exception as e:
                self.logger.error(f"Worker {worker_name} failed: {e}")
                result = {"error": str(e), "agent": worker_name}
            worker_results[worker_name] = result

            self.conversation_history.append({
                "agent": worker_name,
                "input": worker_task,
                "output": result
            })

        # Coordinator synthesizes results
        synthesis_prompt = f"""
        Task: {task}

        Worker results:
        {self._format_results(worker_results)}

        Synthesize these results into a final answer.
        """

        final_answer = coordinator.chat(synthesis_prompt)

        return {
            "plan": plan,
            "worker_results": worker_results,
            "final_answer": final_answer
        }

    async def parallel_execution(
        self,
        tasks: Dict[str, str],
        agent_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        並行執行多個獨立任務

        使用異步並行處理來同時執行多個獨立的代理任務，
        大幅減少總執行時間。適合處理互不依賴的任務。

        Args:
            tasks: 任務字典，格式為 {task_id: task_description}
            agent_mapping: 任務到代理的映射，格式為 {task_id: agent_name}

        Returns:
            包含所有任務結果的字典

        Example:
            >>> tasks = {
            ...     "task1": "分析數據集A",
            ...     "task2": "生成報告B",
            ...     "task3": "處理文檔C"
            ... }
            >>> agent_mapping = {
            ...     "task1": "data_agent",
            ...     "task2": "report_agent",
            ...     "task3": "doc_agent"
            ... }
            >>> results = await system.parallel_execution(tasks, agent_mapping)

        Performance:
            - 3個獨立任務並行執行可節省約 60-70% 的時間
            - 執行時間 ≈ max(各任務時間) 而非 sum(各任務時間)
        """
        self.initialize()

        # Validate all agents exist
        for task_id, agent_name in agent_mapping.items():
            if task_id not in tasks:
                raise ValueError(f"No task found for task_id: {task_id}")
            if agent_name not in self.agents:
                raise ValueError(f"Agent not found: {agent_name}")

        self.logger.info(f"Parallel execution: {len(tasks)} tasks across {len(set(agent_mapping.values()))} agents")

        async def execute_single_task(task_id: str, task_description: str, agent_name: str):
            """Execute a single task asynchronously."""
            try:
                agent = self.agents[agent_name]
                self.logger.info(f"Starting task '{task_id}' with agent '{agent_name}'")

                # Run the agent task in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    agent.run,
                    task_description
                )

                self.logger.info(f"Completed task '{task_id}'")
                return {
                    "task_id": task_id,
                    "agent": agent_name,
                    "result": result,
                    "success": True
                }

            except Exception as e:
                self.logger.error(f"Task '{task_id}' failed with agent '{agent_name}': {e}")
                return {
                    "task_id": task_id,
                    "agent": agent_name,
                    "error": str(e),
                    "success": False
                }

        # Create tasks for parallel execution
        async_tasks = []
        for task_id, task_description in tasks.items():
            agent_name = agent_mapping[task_id]
            task = execute_single_task(task_id, task_description, agent_name)
            async_tasks.append(task)

        # Execute all tasks in parallel
        task_results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Process results
        results = {}
        for task_result in task_results:
            if isinstance(task_result, Exception):
                # Handle exceptions from gather
                self.logger.error(f"Task raised exception: {task_result}")
                results["unknown"] = {
                    "success": False,
                    "error": str(task_result)
                }
            else:
                task_id = task_result["task_id"]
                results[task_id] = task_result

                # Add to conversation history
                self.conversation_history.append({
                    "task_id": task_id,
                    "agent": task_result["agent"],
                    "input": tasks[task_id],
                    "output": task_result.get("result") or task_result.get("error"),
                    "success": task_result["success"]
                })

        # Calculate statistics
        successful_tasks = sum(1 for r in results.values() if r.get("success", False))
        failed_tasks = len(results) - successful_tasks

        return {
            "results": results,
            "summary": {
                "total_tasks": len(tasks),
                "successful": successful_tasks,
                "failed": failed_tasks,
                "agents_used": list(set(agent_mapping.values()))
            }
        }

    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format results for display."""
        formatted = []
        for agent_name, result in results.items():
            if isinstance(result, dict) and "answer" in result:
                formatted.append(f"{agent_name}: {result['answer']}")
            else:
                formatted.append(f"{agent_name}: {result}")
        return "\n\n".join(formatted)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self.conversation_history.copy()

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        for agent in self.agents.values():
            agent.clear_memory()
