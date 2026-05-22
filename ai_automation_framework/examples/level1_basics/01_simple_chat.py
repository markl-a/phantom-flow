"""
Level 1 - Example 1: Simple Chat

This example demonstrates the most basic usage of LLMs - sending a simple prompt
and getting a response.

Learning Goals:
- Initialize an LLM client
- Send a simple chat request
- Handle the response
"""

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.core.config import get_config


def main():
    """Main function demonstrating simple chat."""
    print("=" * 50)
    print("Level 1 - Example 1: Simple Chat")
    print("=" * 50)

    # Initialize configuration
    config = get_config()
    print(f"\nUsing model: {config.default_model}")

    # Create an OpenAI client
    client = OpenAIClient()

    # Simple chat example
    prompt = "Explain what artificial intelligence is in 2-3 sentences."
    print(f"\nPrompt: {prompt}")
    print("\nResponse:")
    print("-" * 50)

    response = client.simple_chat(prompt)
    print(response)

    # Another example with a different prompt
    print("\n" + "=" * 50)
    prompt2 = "Write a haiku about programming."
    print(f"\nPrompt: {prompt2}")
    print("\nResponse:")
    print("-" * 50)

    response2 = client.simple_chat(prompt2)
    print(response2)

    print("\n" + "=" * 50)
    print("✓ Example completed!")


if __name__ == "__main__":
    main()
