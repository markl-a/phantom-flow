# Contributing to AI Automation Framework

Thank you for your interest in contributing to the AI Automation Framework! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style Guide](#code-style-guide)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling, insulting, or derogatory remarks
- Publishing others' private information
- Any conduct that could reasonably be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.10 or higher
- Git installed
- A GitHub account
- Basic understanding of AI/LLM concepts
- Familiarity with Python async programming (for advanced contributions)

### Find an Issue

1. Check the [issue tracker](https://github.com/markl-a/Automation_with_AI/issues)
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to let others know you're working on it
4. For major changes, open an issue first to discuss your proposal

## Development Environment Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/Automation_with_AI.git
cd Automation_with_AI

# Add upstream remote
git remote add upstream https://github.com/markl-a/Automation_with_AI.git
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install package in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8 mypy
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys (for testing)
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

### 5. Verify Installation

```bash
# Run tests to verify setup
pytest tests/

# Run a simple example
python examples/level1_basics/01_simple_chat.py
```

## Project Structure

```
Automation_with_AI/
├── ai_automation_framework/    # Main framework code
│   ├── core/                   # Core infrastructure
│   ├── llm/                    # LLM clients
│   ├── rag/                    # RAG system
│   ├── agents/                 # Agent implementations
│   ├── tools/                  # Tool collection
│   ├── workflows/              # Workflow engine
│   ├── integrations/           # External integrations
│   └── plugins/                # Plugin system
├── examples/                   # Example code
│   ├── level1_basics/          # Basic examples
│   ├── level2_intermediate/    # Intermediate examples
│   ├── level3_advanced/        # Advanced examples
│   ├── level4_advanced_automation/ # Automation examples
│   └── level5_ai_assisted_dev/ # AI dev tools
├── tests/                      # Test files
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── docs/                       # Documentation
├── deployment/                 # Deployment configs
├── requirements.txt            # Dependencies
├── setup.py                    # Package setup
├── README.md                   # Project README
├── CHANGELOG.md               # Change log
├── CONTRIBUTING.md            # This file
└── LICENSE                    # MIT License
```

## Development Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write your code following the style guide
- Add or update tests as needed
- Update documentation if applicable
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_your_module.py

# Run with coverage
pytest --cov=ai_automation_framework tests/

# Check code style
black --check ai_automation_framework/
flake8 ai_automation_framework/

# Type checking
mypy ai_automation_framework/
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add new feature description"
```

See [Commit Message Guidelines](#commit-message-guidelines) for format details.

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub. See [Pull Request Process](#pull-request-process) for details.

## Code Style Guide

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 100 characters maximum (not 79)
- **Quotes**: Use double quotes `"` for strings
- **Formatting**: Use Black for automatic formatting

```bash
# Format code with Black
black ai_automation_framework/

# Check with flake8
flake8 ai_automation_framework/ --max-line-length=100
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `BaseAgent`, `OpenAIClient`)
- **Functions/Methods**: `snake_case` (e.g., `get_response`, `process_message`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_TOKENS`, `DEFAULT_MODEL`)
- **Private members**: Prefix with `_` (e.g., `_internal_method`)
- **Module names**: `snake_case` (e.g., `base_client.py`)

### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional, Any

def process_messages(
    messages: List[Message],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> Response:
    """Process messages and return response."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative

    Example:
        >>> example_function("test", 42)
        True
    """
    pass
```

### Async Code

- Use `async`/`await` for I/O-bound operations
- Prefix async functions with `a` (e.g., `achat`, `aprocess`)
- Provide both sync and async versions when possible

```python
async def achat(self, messages: List[Message]) -> Response:
    """Async version of chat."""
    async with aiohttp.ClientSession() as session:
        # async implementation
        pass
```

### Error Handling

- Use specific exception types
- Provide helpful error messages
- Log errors appropriately

```python
try:
    response = self.llm.chat(messages)
except ValueError as e:
    self.logger.error(f"Invalid input: {e}")
    raise
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
    raise RuntimeError(f"Failed to process request: {e}")
```

### Logging

Use the framework's logger:

```python
from ai_automation_framework.core.logger import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/).

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no code change)
- `refactor`: Code refactoring (no feature change or bug fix)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates
- `ci`: CI/CD changes
- `build`: Build system changes

### Scope (Optional)

The module or component affected:
- `core`
- `llm`
- `rag`
- `agents`
- `tools`
- `workflows`
- `integrations`
- `examples`
- `docs`

### Subject

- Use imperative mood ("Add feature" not "Added feature")
- Don't capitalize first letter
- No period at the end
- Keep under 50 characters

### Examples

```bash
feat(llm): Add Google Gemini client support
fix(agents): Fix memory leak in BaseAgent
docs(readme): Update installation instructions
test(rag): Add unit tests for vector store
refactor(core): Simplify config loading logic
perf(cache): Improve cache lookup performance
```

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the footer:

```
feat(llm): Change chat interface signature

BREAKING CHANGE: The chat method now requires messages as a list
of Message objects instead of plain dictionaries.
```

## Pull Request Process

### Before Creating PR

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new features
4. Run code formatters and linters
5. Update CHANGELOG.md if applicable

### PR Title

Use the same format as commit messages:

```
feat(llm): Add streaming support for Claude
```

### PR Description

Use the template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests passing
- [ ] No breaking changes (or clearly documented)

## Related Issues
Closes #123
```

### Review Process

1. Automated checks will run (tests, linting)
2. Maintainers will review your code
3. Address any requested changes
4. Once approved, a maintainer will merge

### After Merge

1. Delete your feature branch
2. Update your local main branch
3. Thank you for contributing!

## Testing Requirements

### Unit Tests

- Test individual functions/methods
- Use mocks for external dependencies
- Aim for 80%+ code coverage

```python
import pytest
from unittest.mock import Mock, patch

def test_base_agent_chat():
    """Test BaseAgent.chat method."""
    agent = BaseAgent()
    with patch.object(agent.llm, 'chat') as mock_chat:
        mock_chat.return_value = Response(content="test")
        response = agent.chat("Hello")
        assert response == "test"
        assert len(agent.memory) == 2  # user + assistant
```

### Integration Tests

- Test component interactions
- Use test fixtures for setup
- Test realistic scenarios

```python
@pytest.mark.integration
def test_rag_retrieval():
    """Test RAG retrieval integration."""
    retriever = Retriever()
    retriever.add_documents(["doc1", "doc2"])
    results = retriever.retrieve("query")
    assert len(results) > 0
```

### Async Tests

Use `pytest-asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_chat():
    """Test async chat."""
    client = OpenAIClient()
    response = await client.achat([Message(role="user", content="test")])
    assert response.content is not None
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/unit/test_agents.py::test_base_agent_chat

# Run with coverage
pytest --cov=ai_automation_framework --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

## Documentation

### Code Documentation

- All public APIs must have docstrings
- Use Google-style docstrings
- Include examples in docstrings when helpful

### User Documentation

When adding new features, update:

- `README.md` - If feature is user-facing
- `docs/API_REFERENCE.md` - For API changes
- `docs/GETTING_STARTED.md` - For setup changes
- Example files in `examples/` - For new capabilities

### Creating Examples

- Place in appropriate level directory
- Include clear comments
- Show realistic use cases
- Keep examples focused and simple

```python
"""
Example: Using the new feature

This example demonstrates how to use the newly added feature.
"""

from ai_automation_framework.your_module import YourClass

def main():
    # Initialize
    instance = YourClass()

    # Use the feature
    result = instance.your_method()

    print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

## Issue Reporting

### Bug Reports

Include:
- Python version
- Framework version
- OS and version
- Minimal code to reproduce
- Expected vs actual behavior
- Error messages and stack traces

Template:

```markdown
**Description**
Clear description of the bug

**To Reproduce**
1. Step 1
2. Step 2
3. See error

**Expected Behavior**
What should happen

**Environment**
- Python version: 3.10
- Framework version: 0.5.0
- OS: Ubuntu 22.04

**Code Sample**
```python
# Minimal reproduction code
```

**Error Message**
```
Error traceback
```
```

### Feature Requests

Include:
- Use case description
- Proposed API (if applicable)
- Why this benefits the project
- Willingness to implement

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions and reviews

### Getting Help

- Check existing documentation
- Search closed issues
- Ask in GitHub Discussions
- Be specific and provide context

### Recognition

Contributors will be:
- Listed in the project README
- Credited in release notes
- Mentioned in relevant documentation

## Development Tips

### Best Practices

1. **Start Small**: Begin with small contributions
2. **Ask Questions**: Don't hesitate to ask for clarification
3. **Test Thoroughly**: Write tests before submitting
4. **Document Changes**: Update docs alongside code
5. **Be Patient**: Review process may take time

### Common Pitfalls

- Not running tests before submitting
- Mixing multiple features in one PR
- Not following code style guidelines
- Missing documentation updates
- Not linking related issues

### Useful Commands

```bash
# Keep your fork updated
git fetch upstream
git rebase upstream/main

# Squash commits (if needed)
git rebase -i HEAD~3

# Format all code
black ai_automation_framework/ tests/ examples/

# Run all checks
pytest && black --check . && flake8 . && mypy ai_automation_framework/
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing, please:
1. Check this guide thoroughly
2. Search existing issues and discussions
3. Open a new discussion on GitHub

---

Thank you for contributing to the AI Automation Framework! Your efforts help make this project better for everyone.

**Happy Coding!**
