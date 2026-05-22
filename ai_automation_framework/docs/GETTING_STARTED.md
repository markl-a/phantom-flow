# Getting Started with AI Automation Framework

This guide will help you get started with the AI Automation Framework from installation to building your first AI application.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Your First AI Application](#your-first-ai-application)
- [Core Concepts](#core-concepts)
- [Next Steps](#next-steps)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- OpenAI API key (for cloud LLMs) or Ollama (for local LLMs)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/Automation_with_AI.git
cd Automation_with_AI
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Configuration

### Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required for OpenAI models
OPENAI_API_KEY=sk-your-key-here

# Optional for Claude models
ANTHROPIC_API_KEY=your-key-here

# Other optional settings
DEFAULT_MODEL=gpt-4o
LOG_LEVEL=INFO
```

### Using Local LLMs (Optional)

If you want to use local LLMs with Ollama:

```bash
# Install Ollama from https://ollama.ai

# Pull a model
ollama pull llama2

# The framework will automatically detect Ollama on localhost:11434
```

## Your First AI Application

### Example 1: Simple Chat

Create a file `my_first_app.py`:

```python
from ai_automation_framework.llm import OpenAIClient

# Create a client
client = OpenAIClient()

# Simple chat
response = client.simple_chat("Explain quantum computing in simple terms")
print(response)
```

Run it:

```bash
python my_first_app.py
```

### Example 2: Chat with Memory

```python
from ai_automation_framework.agents import BaseAgent

# Create an agent with memory
agent = BaseAgent(
    name="MyAssistant",
    system_message="You are a helpful programming assistant."
)

# Initialize the agent
agent.initialize()

# Have a conversation
response1 = agent.chat("What is Python?")
print("Response 1:", response1)

response2 = agent.chat("What are its main use cases?")
print("Response 2:", response2)

# The agent remembers context!
response3 = agent.chat("What did we just discuss?")
print("Response 3:", response3)
```

### Example 3: Document Q&A with RAG

```python
from ai_automation_framework.rag import Retriever
from ai_automation_framework.llm import OpenAIClient

# Create knowledge base
retriever = Retriever()

# Add documents
documents = [
    "Python is a high-level programming language known for its simplicity.",
    "JavaScript is primarily used for web development and runs in browsers.",
    "Rust is a systems programming language focused on safety and performance."
]

retriever.add_documents(documents)

# Query
query = "Tell me about Python"
context = retriever.get_context_string(query)

# Generate answer
client = OpenAIClient()
prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
answer = client.simple_chat(prompt)
print(answer)
```

## Core Concepts

### 1. LLM Clients

LLM clients provide a unified interface to different AI providers:

```python
from ai_automation_framework.llm import OpenAIClient, AnthropicClient, OllamaClient

# Choose your provider
client = OpenAIClient()  # For GPT models
# client = AnthropicClient()  # For Claude models
# client = OllamaClient(model="llama2")  # For local models
```

### 2. Agents

Agents combine LLMs with memory and capabilities:

```python
from ai_automation_framework.agents import BaseAgent

agent = BaseAgent(
    name="MyAgent",
    system_message="Your role and personality here"
)

# Agents maintain conversation history
agent.chat("First message")
agent.chat("Second message - remembers first")
```

### 3. RAG (Retrieval-Augmented Generation)

RAG enhances LLM responses with relevant information:

```python
from ai_automation_framework.rag import Retriever

# Create retriever
retriever = Retriever()

# Index your knowledge
retriever.add_documents(your_documents)

# Retrieve relevant context
context = retriever.get_context_string(query)
```

### 4. Tools

Tools extend agent capabilities:

```python
from ai_automation_framework.tools.common_tools import (
    CalculatorTool,
    FileSystemTool,
    DateTimeTool
)

# Use tools directly
result = CalculatorTool.calculate("2 + 2 * 3")
print(result)  # {"result": 8, "success": True}

# Or register with agents for automatic use
```

### 5. Workflows

Automate multi-step processes:

```python
from ai_automation_framework.workflows import Chain

def step1(input):
    # Process input
    return processed_data

def step2(data):
    # Further processing
    return final_result

# Create chain
chain = Chain(steps=[step1, step2])

# Run
result = chain.run(initial_input)
```

## Next Steps

### Learning Path

1. **Basics** - Start with `examples/level1_basics/`
   - Simple chat interactions
   - Prompt engineering
   - Text processing
   - Streaming responses

2. **Intermediate** - Move to `examples/level2_intermediate/`
   - RAG implementation
   - Function calling
   - Workflow automation
   - Document processing

3. **Advanced** - Explore `examples/level3_advanced/`
   - Multi-agent systems
   - Complex task planning
   - Agent collaboration

### Try the Demos

Run the interactive demos:

```bash
# Chatbot with memory
python examples/demos/chatbot_demo.py

# Document Q&A
python examples/demos/document_qa_demo.py

# Code assistant
python examples/demos/code_assistant_demo.py
```

### Explore Features

- **Usage Tracking**: Monitor costs and token usage
- **Caching**: Speed up responses and reduce costs
- **Document Loaders**: Process PDFs, Word docs, text files
- **Local LLMs**: Run models privately with Ollama

### Build Your Own

Start building your own applications:

```python
# Your custom application
from ai_automation_framework.agents import BaseAgent
from ai_automation_framework.llm import OpenAIClient

# Create specialized agent
class MySpecialAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyAgent",
            system_message="Your custom instructions"
        )

    def run(self, task):
        # Your custom logic
        return self.chat(task)

# Use it
agent = MySpecialAgent()
result = agent.run("Your task here")
```

## Getting Help

- **Examples**: Check `examples/` directory for code samples
- **API Reference**: See framework source code with detailed docstrings
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions

## Common Issues

### Issue: API Key Not Found

Make sure you've set up your `.env` file with your API keys.

### Issue: Module Import Errors

Ensure you've installed all dependencies and activated your virtual environment.

### Issue: Ollama Connection Error

Make sure Ollama is running: `ollama serve`

---

**Happy building! 🚀**
