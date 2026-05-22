"""
Level 1 - Example 4: Streaming Responses

This example demonstrates streaming responses from LLMs for better user experience:
- Real-time response streaming
- Async processing
- Progress indicators

Learning Goals:
- Implement streaming for real-time feedback
- Use async/await for non-blocking operations
- Improve user experience with progressive responses
"""

import asyncio
import sys
from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.core.base import Message


async def example_basic_streaming():
    """Example of basic response streaming."""
    print("\n" + "=" * 50)
    print("1. Basic Streaming")
    print("=" * 50)

    client = OpenAIClient()

    prompt = "Write a short story (3-4 paragraphs) about a robot discovering emotions."

    print(f"\nPrompt: {prompt}")
    print("\nStreaming Response:")
    print("-" * 50)

    messages = [Message(role="user", content=prompt)]

    # Stream the response
    async for chunk in client.stream_chat(messages):
        print(chunk, end="", flush=True)

    print("\n" + "-" * 50)


async def example_async_multiple():
    """Example of processing multiple requests concurrently."""
    print("\n" + "=" * 50)
    print("2. Async Multiple Requests")
    print("=" * 50)

    client = OpenAIClient()

    prompts = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?"
    ]

    print("\nProcessing 3 questions concurrently...")
    print("-" * 50)

    # Create tasks for concurrent execution
    tasks = [
        client.asimple_chat(prompt, max_tokens=100)
        for prompt in prompts
    ]

    # Wait for all tasks to complete
    responses = await asyncio.gather(*tasks)

    # Display results
    for prompt, response in zip(prompts, responses):
        print(f"\nQ: {prompt}")
        print(f"A: {response}")
        print()


async def example_streaming_with_callback():
    """Example of streaming with progress callback."""
    print("\n" + "=" * 50)
    print("3. Streaming with Progress Indicator")
    print("=" * 50)

    client = OpenAIClient()

    prompt = "Explain machine learning in simple terms (2-3 paragraphs)."

    print(f"\nPrompt: {prompt}")
    print("\nStreaming Response:")
    print("-" * 50)

    messages = [Message(role="user", content=prompt)]

    full_response = ""
    chunk_count = 0

    async for chunk in client.stream_chat(messages):
        full_response += chunk
        chunk_count += 1
        print(chunk, end="", flush=True)

        # Show progress every 20 chunks
        if chunk_count % 20 == 0:
            sys.stdout.flush()

    print("\n" + "-" * 50)
    print(f"\nReceived {chunk_count} chunks")
    print(f"Total characters: {len(full_response)}")


async def example_streaming_comparison():
    """Compare streaming vs non-streaming."""
    print("\n" + "=" * 50)
    print("4. Streaming vs Non-Streaming Comparison")
    print("=" * 50)

    client = OpenAIClient()

    prompt = "List 5 benefits of using AI in business."

    # Non-streaming (waits for complete response)
    print("\nNon-Streaming (waits for complete response):")
    print("-" * 50)
    print("Waiting...", end="", flush=True)

    import time
    start = time.time()
    response = await client.asimple_chat(prompt)
    elapsed = time.time() - start

    print(f"\rResponse received in {elapsed:.2f}s")
    print(response)

    # Streaming (shows response as it arrives)
    print("\n\nStreaming (shows response as it arrives):")
    print("-" * 50)

    messages = [Message(role="user", content=prompt)]
    start = time.time()

    async for chunk in client.stream_chat(messages):
        print(chunk, end="", flush=True)

    elapsed = time.time() - start
    print(f"\n\n✓ Completed streaming in {elapsed:.2f}s")


def main():
    """Main function demonstrating streaming responses."""
    print("=" * 50)
    print("Level 1 - Example 4: Streaming Responses")
    print("=" * 50)

    # Run async examples
    asyncio.run(example_basic_streaming())
    asyncio.run(example_async_multiple())
    asyncio.run(example_streaming_with_callback())
    asyncio.run(example_streaming_comparison())

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- Streaming provides real-time feedback to users")
    print("- Async operations allow concurrent processing")
    print("- Better user experience with progressive responses")
    print("- Useful for long responses or multiple requests")


if __name__ == "__main__":
    main()
