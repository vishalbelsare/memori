# Memori

**The Open-Source Memory Layer for AI Agents & Multi-Agent Systems**

!!! tip "Philosophy"
    **Second-memory for all your LLM work** - Never repeat context again. Simple, reliable architecture that just works out of the box.

## Why Memori?

Give your AI agents structured, persistent memory with professional-grade architecture:

```python
# Before: Repeating context every time
response = completion(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a Python expert..."},
        {"role": "user", "content": "Remember, I use Flask and pytest..."},
        {"role": "user", "content": "Help me with authentication"}
    ]
)

# After: Automatic context injection
from memori import Memori

memori = Memori(openai_api_key="your-key")
memori.enable()  # Auto-records ALL LLM conversations

# Context automatically injected from memory
response = completion(
    model="gpt-4", 
    messages=[{"role": "user", "content": "Help me with authentication"}]
)
```

## ✨ Key Features

- **🎯 Universal Integration**: Works with ANY LLM library (LiteLLM, OpenAI, Anthropic)
- **🧠 Intelligent Processing**: Pydantic-based memory with entity extraction
- **🔄 Auto-Context Injection**: Relevant memories automatically added to conversations  
- **📊 Multiple Memory Types**: Short-term, long-term, rules, and entity relationships
- **🔍 Advanced Search**: Full-text search with semantic ranking
- **⚙️ Production-Ready**: Comprehensive error handling, logging, and configuration
- **🗄️ Database Support**: SQLite, PostgreSQL, MySQL
- **🛡️ Type Safety**: Full Pydantic validation and type checking

## 🚀 Quick Start

### Installation

```bash
pip install memorisdk litellm
```

### Basic Usage

```python
from memori import Memori

# Initialize with default SQLite database
memori = Memori(
    openai_api_key="your-openai-key",
    conscious_ingest=True  # Intelligent memory filtering
)

# Enable universal memory recording
memori.enable()

# Now use ANY LLM library - memories auto-recorded!
import openai
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "I work with Python and prefer clean code"}]
)

# Or with LiteLLM
from litellm import completion
response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Help me build a Flask API"}]
)
```

## 📋 Memory Types

| Type | Purpose | Retention | Use Case |
|------|---------|-----------|----------|
| **Short-term** | Recent conversations | 7-30 days | Context for current session |
| **Long-term** | Important insights | Permanent | User preferences, key facts |
| **Rules** | User preferences/constraints | Permanent | "I prefer Python", "Use pytest" |
| **Entities** | People, projects, technologies | Tracked | Relationship mapping |

## 🔌 Universal Integration

Works with **ANY** LLM library:

```python
memori.enable()  # Enable universal recording

# LiteLLM (recommended)
from litellm import completion
completion(model="gpt-4", messages=[...])

# OpenAI
import openai
client = openai.OpenAI()
client.chat.completions.create(...)

# Anthropic  
import anthropic
client = anthropic.Anthropic()
client.messages.create(...)

# All automatically recorded and contextualized!
```

## 🔧 Configuration

### Simple Setup
```python
from memori import Memori

memori = Memori(
    database_connect="sqlite:///my_memory.db",
    conscious_ingest=True,
    openai_api_key="sk-..."
)
```

### Advanced Configuration
```python
from memori import ConfigManager

# Load from memori.json or environment
config = ConfigManager()
config.auto_load()

memori = Memori()
memori.enable()
```

## 📚 Next Steps

- [Installation Guide](getting-started/installation.md) - Detailed setup instructions
- [Quick Start](getting-started/quick-start.md) - Get running in 5 minutes  
- [Basic Usage](getting-started/basic-usage.md) - Core concepts and examples
- [Configuration](configuration/settings.md) - Production setup
- [Examples](examples/basic.md) - Real-world use cases

---

*Made for developers who want their AI agents to remember and learn*