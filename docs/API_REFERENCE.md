## API Reference

Comprehensive API documentation for the AI Automation Framework.

## Table of Contents

- [LLM Clients](#llm-clients)
- [Agents](#agents)
- [RAG Components](#rag-components)
- [Tools](#tools)
- [Workflows](#workflows)
- [Core Utilities](#core-utilities)

## LLM Clients

### OpenAIClient

Client for OpenAI GPT models.

```python
from ai_automation_framework.llm import OpenAIClient

client = OpenAIClient(
    model="gpt-4o",              # Model name
    api_key="your-key",          # API key (or from env)
    temperature=0.7,             # Sampling temperature
    max_tokens=4096              # Maximum tokens
)
```

**Methods:**

- `simple_chat(prompt: str, **kwargs) -> str`
  - Simple one-shot chat

- `chat(messages: List[Message], **kwargs) -> Response`
  - Full chat with message history

- `achat(messages: List[Message], **kwargs) -> Response`
  - Async version of chat

- `stream_chat(messages: List[Message], **kwargs) -> AsyncIterator[str]`
  - Stream responses in real-time

### AnthropicClient

Client for Anthropic Claude models.

```python
from ai_automation_framework.llm import AnthropicClient

client = AnthropicClient(
    model="claude-3-5-sonnet-20241022",
    api_key="your-key",
    temperature=0.7
)
```

Same methods as OpenAIClient.

### OllamaClient

Client for local LLMs via Ollama.

```python
from ai_automation_framework.llm import OllamaClient

client = OllamaClient(
    model="llama2",
    base_url="http://localhost:11434"
)
```

**Additional Methods:**

- `list_models() -> List[str]`
  - List available models

- `pull_model(model_name: str) -> bool`
  - Download a model

## Agents

### BaseAgent

Base class for building AI agents with memory.

```python
from ai_automation_framework.agents import BaseAgent

agent = BaseAgent(
    name="MyAgent",
    llm=client,                  # Optional LLM client
    system_message="You are..."  # System prompt
)
```

**Methods:**

- `initialize() -> None`
  - Initialize the agent

- `chat(user_message: str, **kwargs) -> str`
  - Chat with memory

- `add_message(role: str, content: str) -> None`
  - Add to conversation history

- `get_memory() -> List[Message]`
  - Get conversation history

- `clear_memory(keep_system: bool = True) -> None`
  - Clear conversation history

### ToolAgent

Agent that can use tools.

```python
from ai_automation_framework.agents import ToolAgent

agent = ToolAgent(
    name="ToolAgent",
    tools={},                    # Tool registry
    tool_schemas=[],             # OpenAI tool schemas
    max_iterations=10            # Max reasoning loops
)
```

**Methods:**

- `register_tool(name: str, function: Callable, schema: Dict) -> None`
  - Register a new tool

- `execute_tool(tool_name: str, arguments: Dict) -> Any`
  - Execute a tool

- `run(task: str, **kwargs) -> Dict`
  - Run agent with tool use

### MultiAgentSystem

Coordinate multiple agents.

```python
from ai_automation_framework.agents import MultiAgentSystem

system = MultiAgentSystem(
    name="MySystem",
    agents={}                    # Agent registry
)
```

**Methods:**

- `register_agent(name: str, agent: BaseAgent) -> None`
  - Register an agent

- `sequential_execution(task: str, agent_sequence: List[str]) -> Dict`
  - Sequential workflow

- `collaborative_execution(task: str, coordinator: str, workers: List[str]) -> Dict`
  - Collaborative workflow

## RAG Components

### EmbeddingModel

Generate embeddings for text.

```python
from ai_automation_framework.rag import EmbeddingModel

model = EmbeddingModel(
    model="text-embedding-3-small",
    api_key="your-key"
)
```

**Methods:**

- `embed_text(text: str) -> List[float]`
  - Embed single text

- `embed_texts(texts: List[str], batch_size: int = 100) -> List[List[float]]`
  - Embed multiple texts

- `embed_query(query: str) -> List[float]`
  - Embed query (alias for embed_text)

### VectorStore

Store and search embeddings.

```python
from ai_automation_framework.rag import VectorStore

store = VectorStore(
    collection_name="my_collection",
    persist_directory="./data/chroma"
)
```

**Methods:**

- `add_documents(documents: List[str], embeddings: List[List[float]], metadatas: List[Dict] = None, ids: List[str] = None) -> None`
  - Add documents to store

- `search(query_embedding: List[float], top_k: int = 5, where: Dict = None) -> Tuple[List[str], List[float], List[Dict]]`
  - Search for similar documents

- `count() -> int`
  - Get document count

- `delete_collection() -> None`
  - Delete the collection

### Retriever

Complete RAG pipeline.

```python
from ai_automation_framework.rag import Retriever

retriever = Retriever(
    embedding_model=model,       # Optional
    vector_store=store,          # Optional
    top_k=5                      # Results to return
)
```

**Methods:**

- `add_documents(documents: List[str], metadatas: List[Dict] = None, ids: List[str] = None) -> None`
  - Index documents

- `retrieve(query: str, top_k: int = None, where: Dict = None) -> Tuple[List[str], List[float], List[Dict]]`
  - Retrieve relevant documents

- `get_context_string(query: str, top_k: int = None, separator: str = "\n\n") -> str`
  - Get formatted context

## Tools

### Common Tools

Pre-built tools for agents.

```python
from ai_automation_framework.tools.common_tools import (
    CalculatorTool,
    FileSystemTool,
    DateTimeTool,
    WebSearchTool,
    DataProcessingTool
)
```

**CalculatorTool:**
- `calculate(expression: str) -> Dict`
- `calculate_percentage(value: float, percentage: float) -> float`
- `calculate_compound_interest(...) -> Dict`

**FileSystemTool:**
- `read_file(file_path: str) -> Dict`
- `write_file(file_path: str, content: str) -> Dict`
- `list_directory(dir_path: str) -> Dict`

**DateTimeTool:**
- `get_current_datetime(timezone: str = "UTC") -> Dict`
- `calculate_date_difference(date1: str, date2: str) -> Dict`

### Document Loaders

Load documents from various formats.

```python
from ai_automation_framework.tools.document_loaders import (
    TextLoader,
    PDFLoader,
    DocxLoader,
    MarkdownLoader,
    DirectoryLoader
)
```

**TextLoader:**
```python
loader = TextLoader(
    file_path="document.txt",
    encoding="utf-8",
    chunk_size=1000              # Optional chunking
)
documents = loader.load()
```

**PDFLoader:**
```python
loader = PDFLoader(
    file_path="document.pdf",
    extract_images=False
)
documents = loader.load()
```

**DirectoryLoader:**
```python
loader = DirectoryLoader(
    directory_path="./docs",
    glob_pattern="**/*.txt",
    exclude_patterns=["*.tmp"]
)
documents = loader.load()
```

## Workflows

### Chain

Sequential processing chain.

```python
from ai_automation_framework.workflows import Chain

chain = Chain(steps=[func1, func2, func3])
result = chain.run(initial_input)
```

**Methods:**

- `add_step(step: Callable) -> Chain`
  - Add a processing step

- `run(initial_input: Any) -> Any`
  - Execute the chain

### Pipeline

Complex workflow with dependencies.

```python
from ai_automation_framework.workflows import Pipeline

pipeline = Pipeline(name="MyPipeline")

pipeline.add_stage("stage1", func1)
pipeline.add_stage("stage2", func2, depends_on=["stage1"])
pipeline.add_stage("stage3", func3, depends_on=["stage2"])

results = pipeline.run({"input": data})
```

**Methods:**

- `add_stage(name: str, function: Callable, depends_on: List[str] = None) -> Pipeline`
  - Add a pipeline stage

- `run(initial_input: Dict) -> Dict`
  - Execute the pipeline

## Core Utilities

### Config

Configuration management.

```python
from ai_automation_framework.core.config import get_config

config = get_config()
print(config.openai_api_key)
print(config.default_model)
```

### Logger

Logging utilities.

```python
from ai_automation_framework.core.logger import get_logger

logger = get_logger(__name__)
logger.info("Log message")
```

### UsageTracker

Track LLM usage and costs.

```python
from ai_automation_framework.core.usage_tracker import get_usage_tracker

tracker = get_usage_tracker()

# Track usage
tracker.track(
    model="gpt-4o",
    prompt_tokens=100,
    completion_tokens=50
)

# Get statistics
stats = tracker.get_stats()
print(stats)

# Print summary
print(tracker.get_cost_summary())
```

### ResponseCache

Cache LLM responses.

```python
from ai_automation_framework.core.cache import get_cache

cache = get_cache()

# Check cache
cached = cache.get(prompt, model, temperature)

if cached:
    return cached

# Cache response
response = llm.chat(...)
cache.set(prompt, response, model, temperature)
```

---

For more examples and detailed usage, see the `examples/` directory.
