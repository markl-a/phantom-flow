"""
Level 2 - Example 4: Document Processing

This example demonstrates processing various document formats and
building knowledge bases from multiple sources.

Learning Goals:
- Load documents from various formats
- Process and chunk documents
- Build searchable knowledge bases
- Query documents with RAG
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_automation_framework.tools.document_loaders import (
    TextLoader,
    MarkdownLoader,
    DirectoryLoader,
    load_document
)
from ai_automation_framework.rag import Retriever, VectorStore
from ai_automation_framework.llm import OpenAIClient


def create_sample_documents():
    """Create sample documents for demonstration."""
    docs_dir = Path("./sample_docs")
    docs_dir.mkdir(exist_ok=True)

    # Create sample text files
    (docs_dir / "ai_basics.txt").write_text("""
Artificial Intelligence (AI) Overview

Artificial Intelligence refers to the simulation of human intelligence in machines
that are programmed to think and learn. AI systems can perform tasks such as visual
perception, speech recognition, decision-making, and language translation.

Types of AI:
1. Narrow AI - Designed for specific tasks
2. General AI - Human-level intelligence across tasks
3. Super AI - Surpasses human intelligence

Current applications include virtual assistants, recommendation systems,
autonomous vehicles, and medical diagnosis.
""")

    (docs_dir / "machine_learning.txt").write_text("""
Machine Learning Introduction

Machine Learning is a subset of AI that enables systems to learn from data
without being explicitly programmed. It uses algorithms to identify patterns
and make predictions or decisions.

Key Approaches:
- Supervised Learning: Learning from labeled data
- Unsupervised Learning: Finding patterns in unlabeled data
- Reinforcement Learning: Learning through trial and error

Common algorithms include neural networks, decision trees, support vector
machines, and clustering algorithms. ML is used in image recognition,
natural language processing, and predictive analytics.
""")

    (docs_dir / "deep_learning.txt").write_text("""
Deep Learning Fundamentals

Deep Learning is a specialized area of machine learning that uses neural
networks with multiple layers (deep neural networks). These networks can
automatically learn hierarchical representations of data.

Architecture Components:
- Input Layer: Receives raw data
- Hidden Layers: Process and transform data
- Output Layer: Produces final predictions

Deep learning excels at tasks like image classification, speech recognition,
and natural language understanding. Popular frameworks include TensorFlow,
PyTorch, and Keras.
""")

    return str(docs_dir)


def example_load_single_document():
    """Example of loading a single document."""
    print("\n" + "=" * 50)
    print("1. Loading Single Document")
    print("=" * 50)

    docs_dir = create_sample_documents()

    # Load a text file
    file_path = Path(docs_dir) / "ai_basics.txt"
    print(f"\nLoading: {file_path.name}")

    loader = TextLoader(str(file_path))
    documents = loader.load()

    print(f"\n✓ Loaded {len(documents)} document(s)")
    print(f"Content preview:\n{documents[0]['content'][:200]}...")
    print(f"\nMetadata: {documents[0]['metadata']}")


def example_load_directory():
    """Example of loading entire directory."""
    print("\n" + "=" * 50)
    print("2. Loading Directory")
    print("=" * 50)

    docs_dir = create_sample_documents()

    print(f"\nLoading all documents from: {docs_dir}")

    loader = DirectoryLoader(
        docs_dir,
        glob_pattern="*.txt"
    )

    documents = loader.load()

    print(f"\n✓ Loaded {len(documents)} document(s)")

    for doc in documents:
        filename = Path(doc['metadata']['source']).name
        content_preview = doc['content'][:100].replace('\n', ' ')
        print(f"\n- {filename}")
        print(f"  Preview: {content_preview}...")


def example_build_knowledge_base():
    """Example of building searchable knowledge base."""
    print("\n" + "=" * 50)
    print("3. Building Knowledge Base")
    print("=" * 50)

    docs_dir = create_sample_documents()

    # Load documents
    print("\n📚 Loading documents...")
    loader = DirectoryLoader(docs_dir, glob_pattern="*.txt")
    documents = loader.load()

    # Create retriever
    print("🔧 Creating knowledge base...")
    retriever = Retriever(
        vector_store=VectorStore(collection_name="ai_knowledge_base"),
        top_k=2
    )

    # Add documents
    texts = [doc['content'] for doc in documents]
    metadatas = [doc['metadata'] for doc in documents]

    retriever.add_documents(texts, metadatas=metadatas)

    print(f"✓ Indexed {len(documents)} documents")

    # Query the knowledge base
    queries = [
        "What is machine learning?",
        "Tell me about deep learning architectures",
        "What are the types of AI?"
    ]

    print("\n" + "=" * 50)
    print("Querying Knowledge Base")
    print("=" * 50)

    for query in queries:
        print(f"\n❓ Query: {query}")
        print("-" * 50)

        docs, distances, metas = retriever.retrieve(query, top_k=2)

        for i, (doc, distance, meta) in enumerate(zip(docs, distances, metas), 1):
            source = Path(meta['source']).name
            similarity = 1 - distance
            print(f"\n{i}. Source: {source} (Similarity: {similarity:.3f})")
            print(f"   {doc[:200]}...")


def example_document_qa():
    """Example of document-based Q&A."""
    print("\n" + "=" * 50)
    print("4. Document Q&A System")
    print("=" * 50)

    docs_dir = create_sample_documents()

    # Build knowledge base
    print("\n📚 Building knowledge base...")
    loader = DirectoryLoader(docs_dir, glob_pattern="*.txt")
    documents = loader.load()

    retriever = Retriever(
        vector_store=VectorStore(collection_name="doc_qa_kb"),
        top_k=2
    )

    texts = [doc['content'] for doc in documents]
    metadatas = [doc['metadata'] for doc in documents]
    retriever.add_documents(texts, metadatas=metadatas)

    # Initialize LLM
    client = OpenAIClient()

    # Q&A function
    def answer_question(question: str) -> str:
        """Answer a question using the knowledge base."""
        # Retrieve relevant context
        context = retriever.get_context_string(question)

        # Generate answer
        prompt = f"""Based on the following context, answer the question accurately.
If the answer is not in the context, say so.

Context:
{context}

Question: {question}

Answer:"""

        return client.simple_chat(prompt, temperature=0.3)

    # Ask questions
    questions = [
        "What are the main types of AI?",
        "How does supervised learning work?",
        "What frameworks are used for deep learning?",
        "What is quantum computing?"  # Not in docs
    ]

    print("\n" + "=" * 50)
    print("Q&A Session")
    print("=" * 50)

    for question in questions:
        print(f"\n❓ {question}")
        print("-" * 50)

        answer = answer_question(question)
        print(f"🤖 {answer}\n")


def example_chunked_processing():
    """Example of processing large documents in chunks."""
    print("\n" + "=" * 50)
    print("5. Chunked Document Processing")
    print("=" * 50)

    # Create a larger document
    docs_dir = Path("./sample_docs")
    docs_dir.mkdir(exist_ok=True)

    large_content = "\n\n".join([
        f"Section {i+1}: This is section {i+1} of the document. " * 20
        for i in range(5)
    ])

    (docs_dir / "large_doc.txt").write_text(large_content)

    # Load with chunking
    print("\nLoading large document with chunking...")

    loader = TextLoader(
        str(docs_dir / "large_doc.txt"),
        chunk_size=200
    )

    chunks = loader.load()

    print(f"\n✓ Split into {len(chunks)} chunks")

    for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
        print(f"\nChunk {i}:")
        print(f"  Size: {len(chunk['content'])} characters")
        print(f"  Preview: {chunk['content'][:100]}...")


def main():
    """Main function demonstrating document processing."""
    print("=" * 50)
    print("Level 2 - Example 4: Document Processing")
    print("=" * 50)

    example_load_single_document()
    example_load_directory()
    example_build_knowledge_base()
    example_document_qa()
    example_chunked_processing()

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- Document loaders handle various formats")
    print("- Directory loaders process multiple files")
    print("- RAG enables document-based Q&A")
    print("- Chunking helps process large documents")

    # Cleanup
    import shutil
    shutil.rmtree("./sample_docs", ignore_errors=True)


if __name__ == "__main__":
    main()
