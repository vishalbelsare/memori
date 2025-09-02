# Memori

## Open-Source Memory Engine for LLMs, AI Agents & Multi-Agent Systems

!!! tip "Philosophy"
    **Second-memory for all your LLM work** - Never repeat context again. Simple, reliable architecture that just works out of the box.


## What is Memori?

**Memori** is an open-source memory layer to give your AI agents human-like memory. It remembers what matters, promotes what's essential, and injects structured context intelligently into LLM conversations.

## Why Memori?

Memomi uses multi-agents working together to intelligently promote essential long-term memories to short-term storage for faster context injection.

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

## Key Features

- **Universal Integration**: Works with ANY LLM library (LiteLLM, OpenAI, Anthropic)
- **Intelligent Processing**: Pydantic-based memory with entity extraction
- **Auto-Context Injection**: Relevant memories automatically added to conversations  
- **Multiple Memory Types**: Short-term, long-term, rules, and entity relationships
- **Advanced Search**: Full-text search with semantic ranking
- **Production-Ready**: Comprehensive error handling, logging, and configuration
- **Database Support**: SQLite, PostgreSQL, MySQL
- **Type Safety**: Full Pydantic validation and type checking

## Quick Start

### Installation

```bash
pip install memorisdk
```

### Basic Usage with LiteLLM

Install LiteLLM:

```bash
pip install litellm
```

Set OpenAI API Key:

```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
```

Run the following Python script:

```python
from memori import Memori
from litellm import completion

# Initialize memory
memori = Memori(conscious_ingest=True)
memori.enable()

print("=== First Conversation - Establishing Context ===")
response1 = completion(
    model="gpt-4o-mini",
    messages=[{
        "role": "user", 
        "content": "I'm working on a Python FastAPI project"
    }]
)

print("Assistant:", response1.choices[0].message.content)
print("\n" + "="*50)
print("=== Second Conversation - Memory Provides Context ===")

response2 = completion(
    model="gpt-4o-mini", 
    messages=[{
        "role": "user",
        "content": "Help me add user authentication"
    }]
)
print("Assistant:", response2.choices[0].message.content)
print("\n Notice: Memori automatically knows about your FastAPI Python project!")
```

## Memory Types

| Type | Purpose | Retention | Use Case |
|------|---------|-----------|----------|
| **Short-term** | Recent conversations | 7-30 days | Context for current session |
| **Long-term** | Important insights | Permanent | User preferences, key facts |
| **Rules** | User preferences/constraints | Permanent | "I prefer Python", "Use pytest" |
| **Entities** | People, projects, technologies | Tracked | Relationship mapping |

## Universal Integration

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

## Configuration

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

---

*Made for developers who want their AI agents to remember and learn*