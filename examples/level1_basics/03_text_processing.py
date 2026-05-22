"""
Level 1 - Example 3: Text Processing Automation

This example demonstrates using LLMs for common text processing tasks:
- Summarization
- Translation
- Sentiment analysis
- Text classification

Learning Goals:
- Automate common text processing tasks
- Batch processing multiple items
- Extract structured information from text
"""

from ai_automation_framework.llm import OpenAIClient
import json


def example_summarization():
    """Example of text summarization."""
    print("\n" + "=" * 50)
    print("1. Text Summarization")
    print("=" * 50)

    client = OpenAIClient()

    long_text = """
    Artificial Intelligence (AI) has become one of the most transformative technologies
    of the 21st century. It encompasses a wide range of techniques and approaches, from
    machine learning and deep learning to natural language processing and computer vision.
    AI systems can now perform tasks that previously required human intelligence, such as
    recognizing images, understanding speech, translating languages, and making complex
    decisions. The impact of AI is being felt across virtually every industry, from
    healthcare and finance to transportation and entertainment. However, the rapid
    advancement of AI also raises important questions about ethics, privacy, job
    displacement, and the future of human-machine interaction. As AI continues to evolve,
    it will be crucial to develop responsible AI systems that benefit humanity while
    minimizing potential risks.
    """

    prompt = f"""
    Summarize the following text in exactly 2 sentences:

    {long_text}
    """

    print("Original text length:", len(long_text), "characters")
    print("\nSummary:")
    print("-" * 50)

    response = client.simple_chat(prompt, temperature=0.3)
    print(response)
    print(f"\nSummary length: {len(response)} characters")


def example_translation():
    """Example of text translation."""
    print("\n" + "=" * 50)
    print("2. Text Translation")
    print("=" * 50)

    client = OpenAIClient()

    texts = {
        "English": "Hello, how are you today?",
        "Spanish": "¿Cómo estás hoy?",
        "French": "Comment allez-vous aujourd'hui?"
    }

    for lang, text in texts.items():
        prompt = f'Translate "{text}" to Chinese. Only output the translation, nothing else.'
        print(f"\n{lang}: {text}")
        response = client.simple_chat(prompt, temperature=0.3)
        print(f"Chinese: {response}")


def example_sentiment_analysis():
    """Example of sentiment analysis."""
    print("\n" + "=" * 50)
    print("3. Sentiment Analysis")
    print("=" * 50)

    client = OpenAIClient()

    reviews = [
        "This product is amazing! Best purchase I've ever made.",
        "Terrible quality, broke after one day. Very disappointed.",
        "It's okay, nothing special but does the job.",
        "I absolutely love it! Exceeded all my expectations!"
    ]

    print("\nAnalyzing customer reviews:")
    print("-" * 50)

    for i, review in enumerate(reviews, 1):
        prompt = f"""
        Analyze the sentiment of this review and respond with ONLY ONE WORD:
        Positive, Negative, or Neutral

        Review: "{review}"
        """

        sentiment = client.simple_chat(prompt, temperature=0.1)
        print(f"\n{i}. {review}")
        print(f"   Sentiment: {sentiment.strip()}")


def example_information_extraction():
    """Example of extracting structured information."""
    print("\n" + "=" * 50)
    print("4. Information Extraction")
    print("=" * 50)

    client = OpenAIClient()

    email_text = """
    From: john.doe@example.com
    Subject: Meeting Request - Project Alpha

    Hi Sarah,

    I hope this email finds you well. I would like to schedule a meeting to discuss
    Project Alpha next Tuesday, March 15th at 2:00 PM. The meeting will be held in
    Conference Room B and should last approximately 1 hour.

    Please confirm if this time works for you.

    Best regards,
    John Doe
    Senior Project Manager
    Phone: (555) 123-4567
    """

    prompt = f"""
    Extract the following information from the email and format as JSON:
    - sender_email
    - sender_name
    - sender_title
    - meeting_date
    - meeting_time
    - meeting_location
    - meeting_duration

    Email:
    {email_text}

    Output only valid JSON, nothing else.
    """

    print("Email:")
    print(email_text)
    print("\nExtracted Information:")
    print("-" * 50)

    response = client.simple_chat(prompt, temperature=0.1)
    print(response)

    # Try to parse as JSON
    try:
        data = json.loads(response)
        print("\n✓ Successfully parsed as JSON")
        for key, value in data.items():
            print(f"  {key}: {value}")
    except json.JSONDecodeError:
        print("\n⚠ Response is not valid JSON")


def example_batch_processing():
    """Example of batch processing multiple items."""
    print("\n" + "=" * 50)
    print("5. Batch Processing")
    print("=" * 50)

    client = OpenAIClient()

    # Classify multiple text snippets
    texts = [
        "Python 3.12 released with new performance improvements",
        "Stock market reaches all-time high",
        "New smartphone features AI-powered camera",
        "Climate summit addresses global warming concerns",
        "Machine learning model breaks accuracy record"
    ]

    categories = ["Technology", "Finance", "Environment", "Politics"]

    print(f"\nClassifying texts into categories: {', '.join(categories)}")
    print("-" * 50)

    for i, text in enumerate(texts, 1):
        prompt = f"""
        Classify this text into ONE of these categories: {', '.join(categories)}
        Output ONLY the category name.

        Text: "{text}"
        """

        category = client.simple_chat(prompt, temperature=0.1)
        print(f"\n{i}. {text}")
        print(f"   Category: {category.strip()}")


def main():
    """Main function demonstrating text processing automation."""
    print("=" * 50)
    print("Level 1 - Example 3: Text Processing")
    print("=" * 50)

    example_summarization()
    example_translation()
    example_sentiment_analysis()
    example_information_extraction()
    example_batch_processing()

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- LLMs excel at various text processing tasks")
    print("- Clear prompts with specific output formats work best")
    print("- Lower temperature for consistent, structured outputs")
    print("- Can process multiple items in batch")


if __name__ == "__main__":
    main()
