# Contributing

Thank you for your interest in contributing to Memori! This guide will help you get started.

## Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Install development dependencies**
4. **Make your changes**
5. **Submit a pull request**

## Development Setup

### Prerequisites
- Python 3.8+
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/GibsonAI/memori.git
cd memori

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Development Dependencies

The development installation includes:
- `pytest` - Testing framework
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking
- `mkdocs` - Documentation

## Project Structure

```
memori/
├── memorisdk/          # Main package
│   ├── core/         # Main memory interface and database
│   ├── config/       # Configuration management
│   ├── agents/       # Memory processing agents
│   ├── database/     # Database connectors and queries
│   ├── integrations/ # LLM provider integrations
│   ├── utils/        # Helpers and utilities
│   └── tools/        # Memory search tools
├── tests/            # Test suite
├── docs/             # Documentation
├── examples/         # Usage examples
└── archive/          # Archived old files
```

## Development Workflow

### 1. Code Style

We use `black` for code formatting and `ruff` for linting:

```bash
# Format code
black memorisdk/ tests/

# Lint code
ruff check memorisdk/ tests/

# Type checking
mypy memorisdk/
```

### 2. Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=memorisdk

# Run specific test file
pytest tests/test_memory.py

# Run specific test
pytest tests/test_memory.py::test_memory_recording
```

### 3. Documentation

Documentation is built with MkDocs:

```bash
# Install docs dependencies
pip install -r docs/requirements.txt

# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

## Contributing Guidelines

### Code Quality

1. **Follow PEP 8** - Use `black` for formatting
2. **Add type hints** - Use Python type annotations
3. **Write docstrings** - Use Google-style docstrings
4. **Add tests** - Maintain high test coverage
5. **Update docs** - Keep documentation current

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add PostgreSQL connection pooling
fix: resolve memory leak in agent processing  
docs: update configuration examples
test: add integration tests for LiteLLM
```

### Pull Requests

1. **Create a feature branch** from `main`
2. **Make focused changes** - One feature per PR
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Ensure CI passes** - All tests and checks must pass

## Types of Contributions

### 🐛 Bug Reports

Use the GitHub issue template:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details

### ✨ Feature Requests

Before implementing a new feature:
1. **Check existing issues** - Avoid duplicates
2. **Open a discussion** - Propose the feature first
3. **Wait for approval** - Ensure it aligns with project goals

### 📚 Documentation

Documentation improvements are always welcome:
- Fix typos and grammar
- Add examples and tutorials
- Improve clarity and organization
- Translate to other languages

### 🧪 Testing

Help improve test coverage:
- Add unit tests for untested code
- Create integration tests
- Add performance benchmarks
- Test edge cases

## Development Tips

### Running Examples

Test your changes with the examples:

```bash
cd examples
python basic_usage.py
python personal_assistant.py
```

### Database Testing

Test with different databases:

```bash
# SQLite (default)
python -c "from memori import Memori; m = Memori(); print('SQLite OK')"

# PostgreSQL (requires setup)
python -c "from memori import Memori; m = Memori(database_connect='postgresql://...'); print('PostgreSQL OK')"
```

### Integration Testing

Test with real LLM providers:

```bash
export OPENAI_API_KEY="sk-..."
python examples/basic_usage.py
```

### Memory Inspection

Check memory storage during development:

```python
from memori import Memori

memori = Memori()
memori.enable()

# ... your code ...

# Inspect memories
stats = memori.get_memory_stats()
print(f"Stored memories: {stats}")

memories = memori.get_memories(limit=5)
for memory in memories:
    print(f"Memory: {memory}")
```

## Architecture Guidelines

### Code Organization

- **Separation of concerns** - Each module has a clear purpose
- **Dependency injection** - Use configuration for external dependencies
- **Error handling** - Use custom exceptions with context
- **Type safety** - Full type annotations and validation

### Database Design

- **SQL in query modules** - Centralized query management
- **Connection pooling** - Efficient resource usage  
- **Migration support** - Schema versioning
- **Multi-database** - Support SQLite, PostgreSQL, MySQL

### API Design

- **Simple interface** - Minimal required configuration
- **Pydantic validation** - Type-safe data structures
- **Error context** - Detailed error information
- **Backwards compatibility** - Careful API evolution

## Getting Help

- **GitHub Issues** - Bug reports and feature requests
- **Discussions** - General questions and ideas  
- **Email** - Direct contact for sensitive issues

## Recognition

Contributors will be:
- Listed in the project README
- Credited in release notes
- Invited to join the maintainers team (for significant contributions)

Thank you for helping make Memori better!