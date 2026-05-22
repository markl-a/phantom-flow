"""
Demo: AI Code Assistant

An interactive code assistant that can help with programming tasks:
- Explain code
- Debug issues
- Suggest improvements
- Generate code snippets
- Answer programming questions

Usage:
    python examples/demos/code_assistant_demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_automation_framework.agents import BaseAgent
from ai_automation_framework.llm import OpenAIClient
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax


console = Console()


class CodeAssistant(BaseAgent):
    """Specialized agent for code assistance."""

    def __init__(self, **kwargs):
        system_message = """You are an expert programming assistant with deep knowledge
of Python, JavaScript, and software development best practices.

When helping with code:
- Provide clear, well-commented code examples
- Explain the reasoning behind solutions
- Suggest best practices and optimizations
- Help debug issues systematically
- Consider edge cases and error handling

Format code blocks with proper syntax highlighting using markdown code blocks."""

        super().__init__(
            name="CodeAssistant",
            system_message=system_message,
            **kwargs
        )

    def run(self, task: str, **kwargs) -> str:
        """Process a coding task."""
        return self.chat(task, **kwargs)


def print_welcome():
    """Print welcome message."""
    welcome_text = """
    # 💻 AI Code Assistant

    Your personal programming assistant!

    **I can help you with:**
    - 📝 Writing code snippets
    - 🐛 Debugging issues
    - 📖 Explaining code concepts
    - ⚡ Optimizing code
    - 🎯 Best practices
    - 💡 Algorithm suggestions

    **Commands:**
    - `exit` or `quit`: Exit the assistant
    - `clear`: Clear conversation history
    - `example`: See usage examples
    - `help`: Show this help message

    **Supported Languages:** Python, JavaScript, Java, C++, Go, and more!

    Start by asking a programming question or requesting code help!
    """

    console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))


def show_examples():
    """Show usage examples."""
    examples_text = """
    **Example Requests:**

    1. "Write a Python function to calculate factorial"
    2. "Explain what a decorator is in Python"
    3. "Debug this code: [paste your code]"
    4. "How do I implement a binary search in JavaScript?"
    5. "What's the time complexity of bubble sort?"
    6. "Suggest improvements for this code: [paste code]"
    7. "Generate a REST API endpoint in Python with FastAPI"

    Just ask naturally - I'll understand!
    """

    console.print(Panel(Markdown(examples_text), title="Examples", border_style="cyan"))


def format_response(response: str) -> None:
    """Format and display the response with syntax highlighting."""
    # Check if response contains code blocks
    if "```" in response:
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Regular text
                if part.strip():
                    console.print(Markdown(part))
            else:
                # Code block
                lines = part.split("\n")
                language = lines[0].strip() if lines[0].strip() else "python"
                code = "\n".join(lines[1:])

                if code.strip():
                    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
                    console.print(syntax)
    else:
        # No code blocks, just render as markdown
        console.print(Markdown(response))


def main():
    """Main assistant loop."""
    print_welcome()

    # Initialize assistant
    assistant = CodeAssistant()
    assistant.initialize()

    console.print("\n[bold green]Code Assistant ready! How can I help you today?[/bold green]\n")

    # Main loop
    while True:
        try:
            # Get user input
            user_input = console.input("[bold blue]You:[/bold blue] ").strip()

            # Handle empty input
            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['exit', 'quit']:
                console.print("\n[bold yellow]Happy coding! Goodbye! 👋[/bold yellow]\n")
                break

            elif user_input.lower() == 'clear':
                assistant.clear_memory()
                console.print("\n[bold yellow]✓ Conversation history cleared![/bold yellow]\n")
                continue

            elif user_input.lower() == 'example':
                console.print()
                show_examples()
                console.print()
                continue

            elif user_input.lower() == 'help':
                print_welcome()
                continue

            # Get response from assistant
            console.print()
            with console.status("[bold green]Thinking...", spinner="dots"):
                response = assistant.run(user_input)

            # Display response in a panel
            console.print(Panel(
                "",
                title="🤖 Code Assistant",
                border_style="green"
            ))

            format_response(response)

            console.print()  # Blank line

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit or continue.[/bold yellow]\n")
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
