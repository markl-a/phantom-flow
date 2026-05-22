"""
Level 2 - Example 1: Basic RAG (Retrieval-Augmented Generation)

This example demonstrates RAG, which enhances LLM responses with relevant
context from a knowledge base.

Learning Goals:
- Understand the RAG pipeline
- Create a document knowledge base
- Retrieve relevant context for queries
- Generate responses using retrieved context
"""

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.rag import EmbeddingModel, VectorStore, Retriever
from ai_automation_framework.core.base import Message


def create_knowledge_base():
    """Create a simple knowledge base about AI topics."""
    documents = [
        """Machine Learning is a subset of artificial intelligence that enables systems
        to learn and improve from experience without being explicitly programmed. It focuses
        on developing computer programs that can access data and use it to learn for themselves.""",

        """Deep Learning is a subset of machine learning that uses neural networks with
        multiple layers. These neural networks attempt to simulate the behavior of the human
        brain, allowing it to learn from large amounts of data.""",

        """Natural Language Processing (NLP) is a branch of AI that helps computers understand,
        interpret and manipulate human language. NLP draws from many disciplines, including
        computer science and computational linguistics.""",

        """Computer Vision is a field of AI that trains computers to interpret and understand
        the visual world. Using digital images from cameras and videos and deep learning models,
        machines can accurately identify and classify objects.""",

        """Reinforcement Learning is an area of machine learning concerned with how software
        agents ought to take actions in an environment to maximize some notion of cumulative
        reward. It is different from supervised learning in that correct input/output pairs
        need not be presented.""",

        """Transfer Learning is a machine learning technique where a model trained on one task
        is re-purposed on a second related task. It is a popular approach in deep learning
        where pre-trained models are used as the starting point.""",

        """Generative AI refers to artificial intelligence systems that can generate new content,
        such as text, images, audio, and video. Examples include GPT models for text generation
        and DALL-E for image generation.""",
    ]

    return documents


def example_basic_rag():
    """Basic RAG example."""
    print("\n" + "=" * 50)
    print("1. Basic RAG Pipeline")
    print("=" * 50)

    # Create knowledge base
    print("\n📚 Creating knowledge base...")
    documents = create_knowledge_base()
    print(f"Added {len(documents)} documents to knowledge base")

    # Initialize RAG components
    print("\n🔧 Initializing RAG components...")
    retriever = Retriever(
        vector_store=VectorStore(collection_name="ai_knowledge"),
        top_k=3
    )

    # Add documents to retriever
    print("📝 Processing and indexing documents...")
    retriever.add_documents(
        documents=documents,
        metadatas=[{"topic": "AI", "index": i} for i in range(len(documents))]
    )

    # Query the knowledge base
    query = "What is deep learning and how does it work?"
    print(f"\n❓ Query: {query}")

    print("\n🔍 Retrieving relevant documents...")
    retrieved_docs, distances, metadatas = retriever.retrieve(query)

    print(f"\n📄 Retrieved {len(retrieved_docs)} relevant documents:")
    print("-" * 50)
    for i, (doc, distance, metadata) in enumerate(zip(retrieved_docs, distances, metadatas), 1):
        print(f"\n{i}. (Similarity: {1-distance:.3f})")
        print(f"   {doc[:200]}...")

    # Generate answer using retrieved context
    print("\n🤖 Generating answer with RAG...")
    print("-" * 50)

    context = "\n\n".join(retrieved_docs)
    prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""

    client = OpenAIClient()
    response = client.simple_chat(prompt)
    print(response)


def example_rag_vs_no_rag():
    """Compare responses with and without RAG."""
    print("\n" + "=" * 50)
    print("2. RAG vs No RAG Comparison")
    print("=" * 50)

    # Setup
    documents = [
        """XYZ Corporation was founded in 2020 by Dr. Jane Smith and Dr. Bob Johnson.
        The company specializes in quantum computing solutions for financial institutions.
        Headquarters are located in San Francisco, California.""",

        """In 2023, XYZ Corporation released QuantumCore 3.0, their flagship product
        that provides 100x faster computational power for risk analysis compared to
        traditional systems. The product has been adopted by 15 major banks worldwide.""",

        """XYZ Corporation's latest achievement was winning the 2024 Innovation Award
        for their work in quantum encryption. Their technology provides unprecedented
        security for financial transactions.""",
    ]

    retriever = Retriever(
        vector_store=VectorStore(collection_name="xyz_corp"),
        top_k=2
    )
    retriever.add_documents(documents)

    query = "When did XYZ Corporation release QuantumCore 3.0 and what does it do?"

    # Without RAG
    print(f"\n❓ Query: {query}")
    print("\n🤖 Response WITHOUT RAG (no context):")
    print("-" * 50)

    client = OpenAIClient()
    response_no_rag = client.simple_chat(query)
    print(response_no_rag)

    # With RAG
    print("\n🤖 Response WITH RAG (with context):")
    print("-" * 50)

    context = retriever.get_context_string(query)
    prompt_rag = f"""Based on the following context, answer the question accurately.

Context:
{context}

Question: {query}

Answer:"""

    response_rag = client.simple_chat(prompt_rag)
    print(response_rag)

    print("\n💡 Notice: RAG provides accurate, context-specific information!")


def example_metadata_filtering():
    """Example of using metadata for filtering."""
    print("\n" + "=" * 50)
    print("3. Metadata Filtering")
    print("=" * 50)

    documents = [
        "Python 3.12 introduces new performance improvements and syntax features.",
        "JavaScript ES2024 adds new array methods and improved async handling.",
        "Python best practices include using type hints and following PEP 8.",
        "JavaScript debugging can be done using browser dev tools and Node.js debugger.",
        "Python data science libraries include NumPy, Pandas, and Matplotlib.",
    ]

    metadatas = [
        {"language": "python", "topic": "features"},
        {"language": "javascript", "topic": "features"},
        {"language": "python", "topic": "practices"},
        {"language": "javascript", "topic": "debugging"},
        {"language": "python", "topic": "data_science"},
    ]

    retriever = Retriever(
        vector_store=VectorStore(collection_name="programming_docs"),
        top_k=3
    )
    retriever.add_documents(documents, metadatas=metadatas)

    # Query with filter
    query = "Tell me about best practices"

    print(f"\n❓ Query: {query}")
    print("\n🔍 Filtered retrieval (Python only):")
    print("-" * 50)

    docs, distances, metas = retriever.retrieve(
        query,
        where={"language": "python"}
    )

    for i, (doc, meta) in enumerate(zip(docs, metas), 1):
        print(f"{i}. [{meta['language']}] {doc}")


def main():
    """Main function demonstrating RAG."""
    print("=" * 50)
    print("Level 2 - Example 1: Basic RAG")
    print("=" * 50)

    example_basic_rag()
    example_rag_vs_no_rag()
    example_metadata_filtering()

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- RAG enhances LLM responses with relevant context")
    print("- Retrieval finds relevant documents from knowledge base")
    print("- Context is added to prompts for better accuracy")
    print("- Metadata filtering helps narrow down results")


if __name__ == "__main__":
    main()
