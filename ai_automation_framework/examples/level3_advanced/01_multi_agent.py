"""
Level 3 - Example 1: Multi-Agent Systems

This example demonstrates multi-agent systems where multiple specialized
agents collaborate to solve complex tasks.

Learning Goals:
- Create specialized agents with different roles
- Implement agent collaboration patterns
- Coordinate agents for complex problem solving
- Use sequential and collaborative execution
"""

from ai_automation_framework.agents import BaseAgent, MultiAgentSystem
from ai_automation_framework.llm import OpenAIClient


class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering."""

    def __init__(self, **kwargs):
        system_message = """You are a research specialist. Your role is to gather and
        analyze information on topics. Provide detailed, factual information with sources
        when possible. Be thorough and accurate."""

        super().__init__(
            name="ResearchAgent",
            system_message=system_message,
            **kwargs
        )

    def run(self, task: str, **kwargs) -> dict:
        """Research a topic."""
        response = self.chat(task, **kwargs)
        return {"answer": response, "agent_type": "research"}


class WriterAgent(BaseAgent):
    """Agent specialized in content writing."""

    def __init__(self, **kwargs):
        system_message = """You are a professional content writer. Your role is to
        create engaging, well-structured content. Focus on clarity, style, and readability.
        Use compelling narratives and clear explanations."""

        super().__init__(
            name="WriterAgent",
            system_message=system_message,
            **kwargs
        )

    def run(self, task: str, **kwargs) -> dict:
        """Write content."""
        response = self.chat(task, **kwargs)
        return {"answer": response, "agent_type": "writer"}


class EditorAgent(BaseAgent):
    """Agent specialized in editing and refining content."""

    def __init__(self, **kwargs):
        system_message = """You are an expert editor. Your role is to improve content
        by checking grammar, clarity, structure, and style. Provide specific suggestions
        for improvement and create polished final versions."""

        super().__init__(
            name="EditorAgent",
            system_message=system_message,
            **kwargs
        )

    def run(self, task: str, **kwargs) -> dict:
        """Edit content."""
        response = self.chat(task, **kwargs)
        return {"answer": response, "agent_type": "editor"}


class CriticAgent(BaseAgent):
    """Agent specialized in critical analysis."""

    def __init__(self, **kwargs):
        system_message = """You are a critical analyst. Your role is to evaluate work
        objectively, identify strengths and weaknesses, and provide constructive feedback.
        Be thorough but fair in your assessment."""

        super().__init__(
            name="CriticAgent",
            system_message=system_message,
            **kwargs
        )

    def run(self, task: str, **kwargs) -> dict:
        """Provide critical analysis."""
        response = self.chat(task, **kwargs)
        return {"answer": response, "agent_type": "critic"}


def example_sequential_workflow():
    """Example of sequential agent workflow."""
    print("\n" + "=" * 50)
    print("1. Sequential Workflow")
    print("=" * 50)

    # Create multi-agent system
    system = MultiAgentSystem()

    # Register agents
    system.register_agent("researcher", ResearchAgent())
    system.register_agent("writer", WriterAgent())
    system.register_agent("editor", EditorAgent())

    # Task: Create an article
    task = "Write a short article (3 paragraphs) about the benefits of AI in healthcare"

    print(f"\n📋 Task: {task}")
    print("\n🔄 Sequential execution: Researcher → Writer → Editor")
    print("-" * 50)

    # Execute sequentially
    results = system.sequential_execution(
        task=task,
        agent_sequence=["researcher", "writer", "editor"]
    )

    # Display results
    for agent_name, result in results.items():
        print(f"\n{'='*50}")
        print(f"Agent: {agent_name.upper()}")
        print("=" * 50)
        if isinstance(result, dict) and "answer" in result:
            print(result["answer"])
        else:
            print(result)


def example_collaborative_workflow():
    """Example of collaborative agent workflow."""
    print("\n" + "=" * 50)
    print("2. Collaborative Workflow")
    print("=" * 50)

    # Create multi-agent system
    system = MultiAgentSystem()

    # Register agents with different specializations
    system.register_agent("coordinator", BaseAgent(
        name="CoordinatorAgent",
        system_message="You coordinate work between specialized agents."
    ))
    system.register_agent("tech_expert", BaseAgent(
        name="TechExpert",
        system_message="You are a technical expert specializing in software development."
    ))
    system.register_agent("business_analyst", BaseAgent(
        name="BusinessAnalyst",
        system_message="You are a business analyst specializing in ROI and business value."
    ))
    system.register_agent("ux_designer", BaseAgent(
        name="UXDesigner",
        system_message="You are a UX designer specializing in user experience."
    ))

    # Complex task requiring multiple perspectives
    task = "Evaluate whether we should build a mobile app for our product"

    print(f"\n📋 Task: {task}")
    print("\n👥 Collaborative execution with coordinator")
    print("-" * 50)

    # Execute collaboratively
    result = system.collaborative_execution(
        task=task,
        coordinator_agent="coordinator",
        worker_agents=["tech_expert", "business_analyst", "ux_designer"]
    )

    # Display results
    print("\n📝 COORDINATOR'S PLAN:")
    print("-" * 50)
    print(result["plan"])

    print("\n\n👥 WORKER RESULTS:")
    print("=" * 50)
    for agent_name, agent_result in result["worker_results"].items():
        print(f"\n{agent_name.upper()}:")
        print("-" * 50)
        if isinstance(agent_result, dict) and "answer" in agent_result:
            print(agent_result["answer"])
        else:
            print(agent_result)

    print("\n\n✅ FINAL SYNTHESIS:")
    print("=" * 50)
    print(result["final_answer"])


def example_debate_system():
    """Example of agents engaging in debate."""
    print("\n" + "=" * 50)
    print("3. Agent Debate System")
    print("=" * 50)

    # Create agents with opposing views
    proponent = BaseAgent(
        name="Proponent",
        system_message="You argue in favor of topics presented to you. Be persuasive."
    )

    opponent = BaseAgent(
        name="Opponent",
        system_message="You argue against topics presented to you. Be critical."
    )

    moderator = BaseAgent(
        name="Moderator",
        system_message="You moderate debates and provide balanced conclusions."
    )

    topic = "Remote work is better than office work"
    print(f"\n🎯 Debate Topic: {topic}")
    print("-" * 50)

    # Round 1: Opening arguments
    print("\n\n📢 ROUND 1: Opening Arguments")
    print("=" * 50)

    print("\n✅ Proponent:")
    print("-" * 50)
    pro_arg1 = proponent.chat(f"Present your opening argument in favor of: {topic}")
    print(pro_arg1)

    print("\n\n❌ Opponent:")
    print("-" * 50)
    opp_arg1 = opponent.chat(f"Present your opening argument against: {topic}")
    print(opp_arg1)

    # Round 2: Rebuttals
    print("\n\n🔄 ROUND 2: Rebuttals")
    print("=" * 50)

    print("\n✅ Proponent responds:")
    print("-" * 50)
    pro_rebuttal = proponent.chat(f"Respond to this counter-argument: {opp_arg1}")
    print(pro_rebuttal)

    print("\n\n❌ Opponent responds:")
    print("-" * 50)
    opp_rebuttal = opponent.chat(f"Respond to this argument: {pro_arg1}")
    print(opp_rebuttal)

    # Moderator's conclusion
    print("\n\n⚖️  MODERATOR'S CONCLUSION:")
    print("=" * 50)
    conclusion = moderator.chat(f"""
    Topic: {topic}

    Proponent's arguments:
    {pro_arg1}
    {pro_rebuttal}

    Opponent's arguments:
    {opp_arg1}
    {opp_rebuttal}

    Provide a balanced conclusion summarizing both sides and key insights.
    """)
    print(conclusion)


def example_expert_panel():
    """Example of expert panel consultation."""
    print("\n" + "=" * 50)
    print("4. Expert Panel Consultation")
    print("=" * 50)

    # Create panel of experts
    experts = {
        "security": BaseAgent(
            name="SecurityExpert",
            system_message="You are a cybersecurity expert."
        ),
        "performance": BaseAgent(
            name="PerformanceExpert",
            system_message="You are a software performance expert."
        ),
        "scalability": BaseAgent(
            name="ScalabilityExpert",
            system_message="You are a system scalability expert."
        )
    }

    question = "What are the key considerations for building a real-time chat application?"

    print(f"\n❓ Question: {question}")
    print("\n👨‍💼 Consulting expert panel...")
    print("=" * 50)

    # Collect expert opinions
    opinions = {}
    for expert_name, expert in experts.items():
        print(f"\n{expert_name.upper()} EXPERT:")
        print("-" * 50)
        opinion = expert.chat(f"{question}\nProvide your expert opinion focusing on {expert_name} aspects.")
        print(opinion)
        opinions[expert_name] = opinion

    # Synthesize
    print("\n\n📊 SYNTHESIS:")
    print("=" * 50)
    synthesizer = BaseAgent(name="Synthesizer")

    synthesis_prompt = f"""
    Question: {question}

    Expert opinions:
    """
    for expert_name, opinion in opinions.items():
        synthesis_prompt += f"\n\n{expert_name.upper()}: {opinion}"

    synthesis_prompt += "\n\nSynthesize these expert opinions into a comprehensive answer."

    synthesis = synthesizer.chat(synthesis_prompt)
    print(synthesis)


def main():
    """Main function demonstrating multi-agent systems."""
    print("=" * 50)
    print("Level 3 - Example 1: Multi-Agent Systems")
    print("=" * 50)

    example_sequential_workflow()
    example_collaborative_workflow()
    example_debate_system()
    example_expert_panel()

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- Multiple agents can collaborate on complex tasks")
    print("- Sequential execution passes work through pipeline")
    print("- Collaborative execution coordinates specialized agents")
    print("- Agents can debate, review, and improve each other's work")


if __name__ == "__main__":
    main()
