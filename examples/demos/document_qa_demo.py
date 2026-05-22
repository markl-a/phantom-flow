"""
Demo: Document Q&A with RAG

A complete demonstration of document-based question answering using RAG.
Upload documents, ask questions, and get accurate answers with sources.

Usage:
    python examples/demos/document_qa_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.rag import Retriever, VectorStore
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


console = Console()


# Sample documents about AI topics
SAMPLE_DOCUMENTS = {
    "Machine Learning": """
    Machine Learning (ML) is a subset of artificial intelligence that enables systems to learn
    and improve from experience without being explicitly programmed. ML algorithms build models
    based on sample data, known as training data, to make predictions or decisions. Common
    approaches include supervised learning, unsupervised learning, and reinforcement learning.
    Applications of ML include image recognition, natural language processing, recommendation
    systems, and autonomous vehicles.
    """,

    "Neural Networks": """
    Neural Networks are computing systems inspired by biological neural networks in animal brains.
    They consist of interconnected nodes (neurons) organized in layers: input layer, hidden layers,
    and output layer. Deep neural networks with many hidden layers are the foundation of deep
    learning. They excel at pattern recognition tasks such as image classification, speech
    recognition, and natural language understanding. Training involves adjusting connection
    weights through backpropagation to minimize prediction errors.
    """,

    "Natural Language Processing": """
    Natural Language Processing (NLP) is a branch of AI that focuses on the interaction between
    computers and human language. NLP combines computational linguistics with machine learning
    and deep learning to process and analyze large amounts of natural language data. Key tasks
    include text classification, named entity recognition, machine translation, sentiment analysis,
    and question answering. Modern NLP heavily relies on transformer architectures and large
    language models like GPT and BERT.
    """,

    "Computer Vision": """
    Computer Vision is a field of AI that enables computers to derive meaningful information from
    digital images, videos, and other visual inputs. It involves methods for acquiring, processing,
    analyzing, and understanding visual data. Applications include facial recognition, object
    detection, image segmentation, autonomous vehicles, medical image analysis, and augmented
    reality. Convolutional Neural Networks (CNNs) are particularly effective for computer vision
    tasks due to their ability to automatically learn spatial hierarchies of features.
    """,

    "Reinforcement Learning": """
    Reinforcement Learning (RL) is a type of machine learning where an agent learns to make
    decisions by performing actions in an environment to maximize cumulative reward. The agent
    learns through trial and error, receiving feedback in the form of rewards or penalties.
    Key concepts include states, actions, rewards, and policies. RL has achieved remarkable
    success in game playing (like AlphaGo), robotics, autonomous systems, and resource management.
    Deep Reinforcement Learning combines RL with deep neural networks for complex decision-making.
    """
}


def setup_knowledge_base():
    """Set up the RAG knowledge base with sample documents."""
    console.print("\n[bold blue]Setting up knowledge base...[/bold blue]")

    # Create retriever
    retriever = Retriever(
        vector_store=VectorStore(collection_name="ai_qa_demo"),
        top_k=2
    )

    # Add documents
    documents = list(SAMPLE_DOCUMENTS.values())
    metadatas = [{"topic": topic, "source": "AI Knowledge Base"}
                 for topic in SAMPLE_DOCUMENTS.keys()]

    with console.status("[bold green]Indexing documents...", spinner="dots"):
        retriever.add_documents(documents, metadatas=metadatas)

    console.print(f"[bold green]✓ Indexed {len(documents)} documents[/bold green]\n")

    return retriever


def answer_question(question: str, retriever: Retriever, llm: OpenAIClient) -> dict:
    """
    Answer a question using RAG.

    Args:
        question: User's question
        retriever: RAG retriever
        llm: LLM client

    Returns:
        Dictionary with answer and sources
    """
    # Retrieve relevant documents
    documents, distances, metadatas = retriever.retrieve(question)

    # Prepare context
    context = "\n\n".join([
        f"[Source {i+1}: {meta['topic']}]\n{doc}"
        for i, (doc, meta) in enumerate(zip(documents, metadatas))
    ])

    # Generate answer
    prompt = f"""Based on the following context, answer the question accurately and concisely.
If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Answer:"""

    answer = llm.simple_chat(prompt, temperature=0.3)

    return {
        "answer": answer,
        "sources": [meta["topic"] for meta in metadatas],
        "num_sources": len(documents)
    }


def print_welcome():
    """Print welcome message."""
    welcome_text = """
    # 📚 Document Q&A Demo

    Ask questions about AI topics and get accurate answers from our knowledge base!

    **Available Topics:**
    - Machine Learning
    - Neural Networks
    - Natural Language Processing
    - Computer Vision
    - Reinforcement Learning

    **Commands:**
    - `topics`: List all available topics
    - `exit` or `quit`: Exit the demo
    - `help`: Show this help message

    Start asking questions!
    """

    console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))


def print_topics():
    """Print available topics."""
    topics_text = "\n".join([f"- {topic}" for topic in SAMPLE_DOCUMENTS.keys()])
    console.print(Panel(
        topics_text,
        title="📑 Available Topics",
        border_style="cyan"
    ))


def main():
    """Main demo loop."""
    print_welcome()

    # Setup
    retriever = setup_knowledge_base()
    llm = OpenAIClient()

    console.print("[bold green]Ready for questions! Type 'help' for commands.[/bold green]\n")

    # Main Q&A loop
    while True:
        try:
            # Get user input
            question = console.input("[bold blue]Your question:[/bold blue] ").strip()

            # Handle empty input
            if not question:
                continue

            # Handle commands
            if question.lower() in ['exit', 'quit']:
                console.print("\n[bold yellow]Thanks for using Document Q&A! Goodbye! 👋[/bold yellow]\n")
                break

            elif question.lower() == 'topics':
                console.print()
                print_topics()
                console.print()
                continue

            elif question.lower() == 'help':
                print_welcome()
                continue

            # Answer question
            console.print()
            with console.status("[bold green]Searching and analyzing...", spinner="dots"):
                result = answer_question(question, retriever, llm)

            # Display answer
            answer_panel = Panel(
                Markdown(result["answer"]),
                title="🤖 Answer",
                border_style="green"
            )
            console.print(answer_panel)

            # Display sources
            sources_text = f"📚 Sources: {', '.join(result['sources'])} ({result['num_sources']} documents)"
            console.print(f"\n[dim]{sources_text}[/dim]\n")

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit or continue asking.[/bold yellow]\n")
            continue

        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]\n")
            console.print("[yellow]Please try again or type 'exit' to quit.[/yellow]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Goodbye! 👋[/bold yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]\n")
        sys.exit(1)
