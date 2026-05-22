"""
Level 2 - Example 3: Workflow Automation

This example demonstrates workflow automation using chains and pipelines
for complex, multi-step processing tasks.

Learning Goals:
- Build sequential processing chains
- Create parallel workflows with pipelines
- Combine multiple AI operations
- Handle data transformations
"""

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.workflows import Chain, Pipeline


def example_simple_chain():
    """Example of a simple sequential chain."""
    print("\n" + "=" * 50)
    print("1. Simple Sequential Chain")
    print("=" * 50)

    client = OpenAIClient()

    # Define processing steps
    def extract_keywords(text):
        """Step 1: Extract keywords."""
        print("\n[Step 1: Extracting keywords]")
        prompt = f"Extract the main keywords from this text as a comma-separated list:\n\n{text}"
        result = client.simple_chat(prompt, temperature=0.3)
        print(f"Keywords: {result}")
        return result

    def categorize(keywords):
        """Step 2: Categorize keywords."""
        print("\n[Step 2: Categorizing keywords]")
        prompt = f"Categorize these keywords into topics:\n\n{keywords}"
        result = client.simple_chat(prompt, temperature=0.3)
        print(f"Categories: {result}")
        return result

    def create_summary(categories):
        """Step 3: Create summary."""
        print("\n[Step 3: Creating summary]")
        prompt = f"Create a brief summary based on these categories:\n\n{categories}"
        result = client.simple_chat(prompt, temperature=0.5)
        print(f"Summary: {result}")
        return result

    # Create chain
    chain = Chain(steps=[extract_keywords, categorize, create_summary])

    # Input text
    text = """
    Artificial intelligence is revolutionizing healthcare through machine learning
    algorithms that can diagnose diseases, predict patient outcomes, and personalize
    treatment plans. Deep learning models analyze medical images with high accuracy,
    while natural language processing helps extract insights from medical records.
    """

    print(f"\nInput text: {text}\n")
    print("=" * 50)

    # Run chain
    final_result = chain.run(text)

    print("\n" + "=" * 50)
    print("✓ Chain completed!")
    print(f"\nFinal Result:\n{final_result}")


def example_content_pipeline():
    """Example of content creation pipeline."""
    print("\n" + "=" * 50)
    print("2. Content Creation Pipeline")
    print("=" * 50)

    client = OpenAIClient()

    # Define pipeline stages
    def research_stage(context):
        """Research stage."""
        print("\n[Stage: Research]")
        topic = context["input"]["topic"]
        prompt = f"Provide key facts about {topic} in 3-4 bullet points."
        facts = client.simple_chat(prompt)
        print(f"Facts gathered:\n{facts}")
        return facts

    def outline_stage(context):
        """Outline stage."""
        print("\n[Stage: Create Outline]")
        topic = context["input"]["topic"]
        facts = context["results"]["research"]
        prompt = f"Create a 3-section outline for an article about {topic} using these facts:\n{facts}"
        outline = client.simple_chat(prompt)
        print(f"Outline created:\n{outline}")
        return outline

    def write_stage(context):
        """Writing stage."""
        print("\n[Stage: Write Content]")
        outline = context["results"]["outline"]
        prompt = f"Write a short article based on this outline:\n{outline}"
        article = client.simple_chat(prompt, max_tokens=500)
        print(f"Article written ({len(article)} chars)")
        return article

    def polish_stage(context):
        """Polish stage."""
        print("\n[Stage: Polish Content]")
        article = context["results"]["write"]
        prompt = f"Improve this article's clarity and flow:\n\n{article}"
        polished = client.simple_chat(prompt, max_tokens=500)
        print("Article polished")
        return polished

    # Create pipeline
    pipeline = Pipeline(name="ContentCreationPipeline")

    # Add stages with dependencies
    pipeline.add_stage("research", research_stage)
    pipeline.add_stage("outline", outline_stage, depends_on=["research"])
    pipeline.add_stage("write", write_stage, depends_on=["outline"])
    pipeline.add_stage("polish", polish_stage, depends_on=["write"])

    # Run pipeline
    topic = "benefits of renewable energy"
    print(f"\nTopic: {topic}")
    print("=" * 50)

    results = pipeline.run({"topic": topic})

    # Display results
    print("\n" + "=" * 50)
    print("Pipeline Results")
    print("=" * 50)

    print("\n📝 FINAL ARTICLE:")
    print("-" * 50)
    print(results["polish"])


def example_data_processing_chain():
    """Example of data processing chain."""
    print("\n" + "=" * 50)
    print("3. Data Processing Chain")
    print("=" * 50)

    client = OpenAIClient()

    # Simulate customer feedback data
    feedback_data = [
        "Great product! Very satisfied with the purchase.",
        "Terrible experience. Product broke after one use.",
        "It's okay, nothing special but works fine.",
        "Amazing quality! Highly recommend to everyone.",
        "Disappointed with the quality. Not worth the price."
    ]

    def analyze_sentiment(feedbacks):
        """Analyze sentiment of all feedbacks."""
        print("\n[Step 1: Analyzing sentiment]")
        sentiments = []
        for feedback in feedbacks:
            prompt = f"Classify sentiment as Positive, Negative, or Neutral: '{feedback}'"
            sentiment = client.simple_chat(prompt, temperature=0.1, max_tokens=10)
            sentiments.append(sentiment.strip())
        print(f"Sentiments: {sentiments}")
        return {"feedbacks": feedbacks, "sentiments": sentiments}

    def calculate_stats(data):
        """Calculate statistics."""
        print("\n[Step 2: Calculating statistics]")
        sentiments = data["sentiments"]
        stats = {
            "total": len(sentiments),
            "positive": sum(1 for s in sentiments if "Positive" in s),
            "negative": sum(1 for s in sentiments if "Negative" in s),
            "neutral": sum(1 for s in sentiments if "Neutral" in s)
        }
        print(f"Statistics: {stats}")
        return {**data, "stats": stats}

    def generate_report(data):
        """Generate summary report."""
        print("\n[Step 3: Generating report]")
        stats = data["stats"]

        prompt = f"""Create a brief customer feedback summary based on these statistics:
        - Total feedbacks: {stats['total']}
        - Positive: {stats['positive']}
        - Negative: {stats['negative']}
        - Neutral: {stats['neutral']}

        Provide insights and recommendations."""

        report = client.simple_chat(prompt, temperature=0.7)
        print("Report generated")
        return report

    # Create chain
    chain = Chain(steps=[analyze_sentiment, calculate_stats, generate_report])

    print("\nProcessing customer feedbacks:")
    for i, feedback in enumerate(feedback_data, 1):
        print(f"{i}. {feedback}")

    print("\n" + "=" * 50)

    # Run chain
    final_report = chain.run(feedback_data)

    print("\n" + "=" * 50)
    print("📊 FINAL REPORT:")
    print("-" * 50)
    print(final_report)


def main():
    """Main function demonstrating workflow automation."""
    print("=" * 50)
    print("Level 2 - Example 3: Workflow Automation")
    print("=" * 50)

    example_simple_chain()
    example_content_pipeline()
    example_data_processing_chain()

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- Chains execute steps sequentially")
    print("- Pipelines support complex dependencies")
    print("- Workflows automate multi-step processes")
    print("- Each stage can transform data for the next")


if __name__ == "__main__":
    main()
