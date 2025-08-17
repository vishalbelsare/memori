# Basic Usage

Learn Memori's core concepts with practical examples.

## Core Concepts

### Memory Types

| Type | Purpose | Example |
|------|---------|---------|
| **Facts** | Objective information | "I use PostgreSQL for databases" |
| **Preferences** | User choices | "I prefer clean, readable code" |
| **Skills** | Abilities & knowledge | "Experienced with FastAPI" |
| **Rules** | Constraints & guidelines | "Always write tests first" |
| **Context** | Session information | "Working on e-commerce project" |

### How It Works

```mermaid
graph LR
    A[LLM Conversation] --> B[Universal Recording]
    B --> C[Memory Agent Processing]
    C --> D[Structured Storage]
    D --> E[Context Injection]
    E --> A
```

1. **Universal Recording**: All LLM conversations automatically captured
2. **Memory Processing**: Pydantic-based entity extraction and categorization  
3. **Structured Storage**: Organized in SQLite/PostgreSQL/MySQL
4. **Context Injection**: Relevant memories added to future conversations

## Simple Example

```python
from memori import Memori

# Initialize
memori = Memori(
    database_connect="sqlite:///my_project.db",
    conscious_ingest=True,
    openai_api_key="sk-..."
)

# Enable recording
memori.enable()

# Use any LLM library
from litellm import completion

# Establish preferences
completion(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "I'm a Python developer who prefers clean, well-documented code"
    }]
)

# Later conversation - preferences remembered
completion(
    model="gpt-4o-mini", 
    messages=[{
        "role": "user",
        "content": "Help me write a function to validate emails"
    }]
)
# Response will include clean code with documentation!
```

## Manual Memory Operations

### Record Conversations
```python
chat_id = memori.record_conversation(
    user_input="I'm learning machine learning",
    ai_output="Start with Python basics and scikit-learn...",
    model="gpt-4o"
)
```

### Search Memories
```python
# Search by content
memories = memori.retrieve_context("machine learning", limit=5)

# Get all memories
all_memories = memori.get_memories(limit=10)
```

### Memory Statistics
```python
stats = memori.get_memory_stats()
print(f"Total conversations: {stats['chat_history_count']}")
print(f"Long-term memories: {stats['long_term_count']}")
```

## Configuration Options

### Basic Configuration
```python
memori = Memori(
    database_connect="sqlite:///memori.db",  # Database connection
    conscious_ingest=True,                   # Enable smart context injection
    namespace="default",                     # Memory namespace
    openai_api_key="sk-..."                 # OpenAI API key
)
```

### Advanced Configuration
```python
memori = Memori(
    database_connect="postgresql://user:pass@localhost/memori",
    template="basic",
    mem_prompt="Focus on Python and web development",
    conscious_ingest=True,
    namespace="web_project", 
    shared_memory=False,
    memory_filters={
        "importance_threshold": 0.4,
        "categories": ["fact", "preference", "skill"]
    },
    openai_api_key="sk-..."
)
```

## Memory Namespaces

Separate memories for different projects:

```python
# Work project memory
work_memori = Memori(namespace="work_project")
work_memori.enable()

# Personal project memory  
personal_memori = Memori(namespace="personal")
personal_memori.enable()

# Each maintains separate memory context
```

## Integration Examples

### OpenAI Direct
```python
import openai

memori.enable()  # Records all OpenAI calls

client = openai.OpenAI()
response = client.chat.completions.create(...)
# Automatically recorded with context injection
```

### Anthropic Direct
```python
import anthropic

memori.enable()  # Records all Anthropic calls

client = anthropic.Anthropic()
response = client.messages.create(...)
# Automatically recorded with context injection
```

### LiteLLM (Recommended)
```python
from litellm import completion

memori.enable()  # Uses native LiteLLM callbacks

completion(model="gpt-4", messages=[...])
completion(model="claude-3", messages=[...]) 
completion(model="gemini-pro", messages=[...])
# All providers automatically supported
```

## Memory Search Tools

### Function Calling Integration
```python
from memori.tools import create_memory_tool

# Create search tool
memory_tool = create_memory_tool(memori)

# Use in LLM function calling
response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "What did I say about testing?"}],
    tools=[memory_tool]
)
```

### Direct Search
```python
from memori.tools import create_memory_search_tool

search_tool = create_memory_search_tool(memori)
result = search_tool("Python preferences", max_results=3)
print(result)
```

## Best Practices

### 1. Use Namespaces
```python
# Separate memories by project/context
work = Memori(namespace="work")
personal = Memori(namespace="personal")
```

### 2. Configure Retention
```python
memori = Memori(
    memory_filters={
        "importance_threshold": 0.3,  # Only store important memories
        "max_short_term": 1000,       # Limit short-term memories
    }
)
```

### 3. Monitor Memory Usage
```python
stats = memori.get_memory_stats()
if stats['short_term_count'] > 1000:
    # Consider cleanup or adjust filters
    pass
```

### 4. Use Configuration Files
```python
from memori import ConfigManager

config = ConfigManager()
config.auto_load()  # Loads from memori.json, env vars

memori = Memori()  # Uses loaded config
```

## Troubleshooting

### Memory Not Recording
```python
# Check if enabled
if not memori.is_enabled:
    memori.enable()

# Verify API key
print(memori.openai_api_key)  # Should not be None

# Check conscious ingestion
print(memori.conscious_ingest)  # Should be True
```

### Context Not Injecting
```python
# Ensure conscious_ingest is enabled
memori = Memori(conscious_ingest=True)

# Check for relevant memories
memories = memori.retrieve_context("your query", limit=3)
print(f"Found {len(memories)} relevant memories")
```

### Database Issues
```python
# Test database connection
try:
    stats = memori.get_memory_stats()
    print("Database connection OK")
except Exception as e:
    print(f"Database error: {e}")
```

## Next Steps

- [Framework Integrations](https://github.com/GibsonAI/memori/tree/main/examples/integrations) - See how Memori works seamlessly with popular AI Agent frameworks
- [Demos](.https://github.com/GibsonAI/memori/tree/main/demos) - Explore Memori's capabilities through these demos
- [Configuration](../configuration/settings.md) - Advanced configuration options