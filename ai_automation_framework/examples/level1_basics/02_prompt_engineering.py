"""
Level 1 - Example 2: Prompt Engineering Basics

This example demonstrates basic prompt engineering techniques:
- Clear instructions
- Context provision
- Output format specification
- Temperature control

Learning Goals:
- Understand how prompts affect outputs
- Learn basic prompt engineering patterns
- Control response style and format
"""

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.core.base import Message


def example_basic_prompt():
    """Example of a basic prompt vs an engineered prompt."""
    print("\n" + "=" * 50)
    print("1. Basic vs Engineered Prompts")
    print("=" * 50)

    client = OpenAIClient()

    # Basic prompt
    basic_prompt = "Tell me about Python."
    print(f"\nBasic Prompt: {basic_prompt}")
    print("\nResponse:")
    print("-" * 50)
    response1 = client.simple_chat(basic_prompt)
    print(response1)

    # Engineered prompt with clear instructions
    engineered_prompt = """
    Explain Python programming language in exactly 3 bullet points.
    Focus on: 1) What it is, 2) Main use cases, 3) Key advantages.
    Keep each point to one sentence.
    """
    print(f"\n\nEngineered Prompt: {engineered_prompt}")
    print("\nResponse:")
    print("-" * 50)
    response2 = client.simple_chat(engineered_prompt)
    print(response2)


def example_role_based_prompting():
    """Example of using role-based prompting."""
    print("\n" + "=" * 50)
    print("2. Role-Based Prompting")
    print("=" * 50)

    client = OpenAIClient()

    # Using system message to set role
    messages = [
        Message(role="system", content="You are an expert Python tutor who explains concepts simply for beginners."),
        Message(role="user", content="What are decorators in Python?")
    ]

    print("\nSystem Role: Expert Python tutor for beginners")
    print("User Question: What are decorators in Python?")
    print("\nResponse:")
    print("-" * 50)

    response = client.chat(messages)
    print(response.content)


def example_output_format():
    """Example of specifying output format."""
    print("\n" + "=" * 50)
    print("3. Output Format Specification")
    print("=" * 50)

    client = OpenAIClient()

    # Request JSON format
    prompt = """
    List 3 popular Python web frameworks.
    Format your response as JSON with this structure:
    {
        "frameworks": [
            {"name": "...", "description": "...", "use_case": "..."}
        ]
    }
    """

    print(f"\nPrompt: {prompt}")
    print("\nResponse:")
    print("-" * 50)

    response = client.simple_chat(prompt, temperature=0.3)  # Lower temperature for structured output
    print(response)


def example_temperature_control():
    """Example of temperature control for creativity."""
    print("\n" + "=" * 50)
    print("4. Temperature Control")
    print("=" * 50)

    client = OpenAIClient()

    prompt = "Write a creative one-sentence story about a robot learning to paint."

    # Low temperature (more focused, deterministic)
    print("\nLow Temperature (0.2) - More focused:")
    print("-" * 50)
    response1 = client.simple_chat(prompt, temperature=0.2)
    print(response1)

    # High temperature (more creative, random)
    print("\n\nHigh Temperature (1.5) - More creative:")
    print("-" * 50)
    response2 = client.simple_chat(prompt, temperature=1.5)
    print(response2)


def main():
    """Main function demonstrating prompt engineering."""
    print("=" * 50)
    print("Level 1 - Example 2: Prompt Engineering")
    print("=" * 50)

    example_basic_prompt()
    example_role_based_prompting()
    example_output_format()
    example_temperature_control()

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- Clear, specific prompts get better results")
    print("- System messages set the AI's role and behavior")
    print("- You can request specific output formats")
    print("- Temperature controls creativity vs consistency")


if __name__ == "__main__":
    main()
