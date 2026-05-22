"""
Demo: Interactive Chatbot with Memory

A simple but complete chatbot demonstration using the AI Automation Framework.
Supports conversation history, different LLM backends, and graceful handling.

Usage:
    python examples/demos/chatbot_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.agents import BaseAgent
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


console = Console()


def print_welcome():
    """Print welcome message."""
    welcome_text = """
    # 🤖 AI Chatbot Demo

    Welcome to the AI Automation Framework chatbot demo!

    **Features:**
    - Maintains conversation history
    - Powered by GPT-4o
    - Rich text formatting

    **Commands:**
    - `exit` or `quit`: Exit the chatbot
    - `clear`: Clear conversation history
    - `help`: Show this help message

    Start chatting below!
    """

    console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))


def print_help():
    """Print help message."""
    help_text = """
    **Available Commands:**
    - `exit` or `quit`: Exit the chatbot
    - `clear`: Clear conversation history
    - `help`: Show this help message

    Just type your message to chat with the AI!
    """
    console.print(Panel(Markdown(help_text), title="Help", border_style="yellow"))


def main():
    """Main chatbot loop."""
    print_welcome()

    # Initialize agent
    agent = BaseAgent(
        name="ChatBot",
        system_message="""You are a friendly and helpful AI assistant.
        You provide clear, concise, and accurate responses.
        You maintain context from previous messages in the conversation."""
    )

    agent.initialize()

    console.print("\n[bold green]Chatbot ready! Type your message or 'help' for commands.[/bold green]\n")

    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = console.input("[bold blue]You:[/bold blue] ").strip()

            # Handle empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['exit', 'quit']:
                console.print("\n[bold yellow]Thanks for chatting! Goodbye! 👋[/bold yellow]\n")
                break

            elif user_input.lower() == 'clear':
                agent.clear_memory()
                console.print("\n[bold yellow]✓ Conversation history cleared![/bold yellow]\n")
                continue

            elif user_input.lower() == 'help':
                print_help()
                continue

            # Get response from agent
            console.print()  # Blank line
            with console.status("[bold green]AI is thinking...", spinner="dots"):
                response = agent.chat(user_input)

            # Display response
            console.print(Panel(
                Markdown(response),
                title="🤖 AI Assistant",
                border_style="green"
            ))
            console.print()  # Blank line

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit or continue chatting.[/bold yellow]\n")
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
