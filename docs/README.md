# Memori Documentation

## Quick Links

- **[Installation](#installation)** - Get started with Memori
- **[Basic Usage](#basic-usage)** - Simple examples
- **[Configuration](#configuration)** - Setup and customization
- **[API Reference](#api-reference)** - Technical details

## Installation

```bash
pip install memori
```

## Basic Usage

### Simple Memory Setup

```python
from memori import Memori

# Create memory for your workspace
memori = Memori(
    database_connect="sqlite:///my_memory.db",
    conscious_ingest=True,
    openai_api_key="sk-..."
)

# Enable memory recording
memori.enable()

# Use any LLM library - context automatically injected!
from litellm import completion
response = completion(model="gpt-4", messages=[...])
```

### Memory Types

| Type | Purpose | Example |
|------|---------|---------|
| **Facts** | Objective information | "I use PostgreSQL for databases" |
| **Preferences** | User choices | "I prefer clean, readable code" |
| **Skills** | Abilities & knowledge | "Experienced with FastAPI" |
| **Rules** | Constraints | "Always write tests first" |
| **Context** | Session info | "Working on e-commerce project" |

## Configuration

### File-based Configuration

Create `memori.json`:
```json
{
  "database": {
    "connection_string": "sqlite:///memori.db"
  },
  "agents": {
    "openai_api_key": "sk-...",
    "conscious_ingest": true
  },
  "memory": {
    "namespace": "my_project",
    "retention_policy": "30_days"
  }
}
```

### Environment Variables

```bash
export MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
export MEMORI_DATABASE__CONNECTION_STRING="postgresql://..."
```

### Configuration Manager

```python
from memori import ConfigManager

config = ConfigManager()
config.auto_load()  # Loads from files and environment

memori = Memori()
memori.enable()
```

## API Reference

### Core Classes

#### `Memori`
Main memory interface.

```python
Memori(
    database_connect="sqlite:///memori.db",
    conscious_ingest=True,
    openai_api_key="sk-...",
    namespace="default"
)
```

**Methods:**
- `enable()` - Start memory recording
- `disable()` - Stop memory recording  
- `record_conversation()` - Manual conversation recording
- `retrieve_context()` - Search memories
- `get_memories()` - Get stored memories

#### `ConfigManager`
Configuration management.

```python
config = ConfigManager()
config.auto_load()
config.get_setting("database.connection_string")
```

### Database Support

- **SQLite**: `sqlite:///path/to/db.db`
- **PostgreSQL**: `postgresql://user:pass@host/db`
- **MySQL**: `mysql://user:pass@host/db`

### Memory Search

```python
from memori.tools import create_memory_tool

# Create search tool for LLM function calling
memory_tool = create_memory_tool(memori)
tools = [memory_tool]
```

## Examples

See `/examples` directory:
- `basic_usage.py` - Simple memory setup
- `personal_assistant.py` - AI assistant with memory
- `advanced_config.py` - Configuration examples

## Troubleshooting

### Common Issues

**Memory not recording:**
- Check OpenAI API key is set
- Verify `conscious_ingest=True`
- Ensure `memori.enable()` was called

**Database connection errors:**
- Verify connection string format
- Check database permissions
- Ensure database server is running

**Configuration not loading:**
- Check file path and format
- Verify environment variable names
- Use `config.get_config_info()` for debugging

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/memori/issues)
- **Documentation**: This README and inline docstrings
- **Examples**: Check `/examples` directory