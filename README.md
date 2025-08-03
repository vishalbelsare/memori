# Memoriai

**The Open-Source Memory Layer for AI Agents & Multi-Agent Systems v1.1**

*Give your AI agents structured, persistent memory with intelligent context injection - no more repeating yourself!*

[![PyPI version](https://badge.fury.io/py/memoriai.svg)](https://badge.fury.io/py/memoriai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 Philosophy

- **Second-memory for all your LLM work** - Never repeat context again
- **Intelligent conscious ingestion** - AI-powered background analysis and context injection
- **Flexible database connections** - SQLite, PostgreSQL, MySQL support  
- **Pydantic-based intelligence** - Structured memory processing with validation
- **Simple, reliable architecture** - Just works out of the box

## ⚡ Quick Start

```bash
pip install memoriai
```

```python
from memoriai import Memori

# Create your workspace memory
office_work = Memori(
    database_connect="sqlite:///office_memory.db",
    conscious_ingest=True,  # Auto-inject relevant context
    openai_api_key="your-key"
)

office_work.enable()  # Start recording conversations

# Use ANY LLM library - context automatically injected!
from litellm import completion

response = completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Help me with Python testing"}]
)
# ✨ Previous conversations about Python and testing automatically included
```

## 🧠 How It Works

### 1. **Universal Recording**
```python
office_work.enable()  # Records ALL LLM conversations
```

### 2. **Intelligent Processing**
- **Entity Extraction**: Extracts people, technologies, projects
- **Smart Categorization**: Facts, preferences, skills, rules
- **Pydantic Validation**: Structured, type-safe memory storage

### 3. **Conscious Context Injection**
```python
conscious_ingest=True  # AI-powered background analysis + automatic context injection
```

**What happens behind the scenes:**
- 🧠 **Background Analysis**: Every 6 hours, analyzes your memory patterns
- 🎯 **Essential Memory Promotion**: Promotes key personal facts to immediate access
- 📝 **Smart Context Injection**: Automatically includes 3-5 most relevant memories
- 🔄 **Continuous Learning**: Adapts to your preferences and conversation patterns

## 🧠 Conscious Ingestion System

### **How it learns about you:**

```python
memori = Memori(
    database_connect="sqlite:///my_memory.db",
    conscious_ingest=True,  # 🔥 The magic happens here
    openai_api_key="sk-..."
)
```

### **Intelligence Layers:**

1. **Memory Agent** - Processes every conversation with Pydantic structured outputs
2. **Conscious Agent** - Analyzes patterns every 6 hours, promotes essential memories  
3. **Retrieval Agent** - Intelligently selects the most relevant context for injection

### **What gets prioritized:**
- 👤 **Personal Identity**: Your name, role, location, basic info
- ❤️ **Preferences & Habits**: What you like, work patterns, routines
- 🛠️ **Skills & Tools**: Technologies you use, expertise areas
- 📊 **Current Projects**: Ongoing work, learning goals
- 🤝 **Relationships**: Important people, colleagues, connections
- 🔄 **Repeated References**: Information you mention frequently

## 🗄️ Memory Types

| Type | Purpose | Example | Auto-Promoted |
|------|---------|---------|---------------|
| **Facts** | Objective information | "I use PostgreSQL for databases" | ✅ High frequency |
| **Preferences** | User choices | "I prefer clean, readable code" | ✅ Personal identity |
| **Skills** | Abilities & knowledge | "Experienced with FastAPI" | ✅ Expertise areas |
| **Rules** | Constraints & guidelines | "Always write tests first" | ✅ Work patterns |
| **Context** | Session information | "Working on e-commerce project" | ✅ Current projects |

## 🔧 Configuration

### Simple Setup
```python
from memoriai import Memori

memori = Memori(
    database_connect="sqlite:///my_memory.db",
    template="basic",
    conscious_ingest=True,
    openai_api_key="sk-..."
)
```

### Advanced Configuration
```python
from memoriai import Memori, ConfigManager

# Load from memori.json or environment
config = ConfigManager()
config.auto_load()

memori = Memori()
memori.enable()
```

Create `memori.json`:
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@localhost/memori"
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

## 🛠️ Memory Management

### **Automatic Background Analysis**
```python
# Automatic analysis every 6 hours (when conscious_ingest=True)
memori.enable()  # Starts background conscious agent

# Manual analysis trigger
memori.trigger_conscious_analysis()

# Get essential conversations
essential = memori.get_essential_conversations(limit=5)
```

### **Memory Retrieval Tools**
```python
from memoriai.tools import create_memory_tool

# Create memory search tool for your LLM
memory_tool = create_memory_tool(memori)

# Use in function calling
tools = [memory_tool]
completion(model="gpt-4", messages=[...], tools=tools)
```

### **Context Control**
```python
# Get relevant context for a query
context = memori.retrieve_context("Python testing", limit=5)
# Returns: 3 essential + 2 specific memories

# Search by category
skills = memori.search_memories_by_category("skill", limit=10)

# Get memory statistics
stats = memori.get_memory_stats()
```

## 📋 Database Schema

```sql
-- Core tables created automatically
chat_history        # All conversations
short_term_memory   # Recent context (expires)
long_term_memory    # Permanent insights  
rules_memory        # User preferences
memory_entities     # Extracted entities
memory_relationships # Entity connections
```

## 📁 Project Structure

```
memoriai/
├── core/           # Main Memori class, database manager
├── agents/         # Memory processing with Pydantic  
├── database/       # SQLite/PostgreSQL/MySQL support
├── integrations/   # LiteLLM, OpenAI, Anthropic
├── config/         # Configuration management
├── utils/          # Helpers, validation, logging
└── tools/          # Memory search tools
```

## 🚀 Examples

- **[Basic Usage](./examples/basic_usage.py)** - Simple memory setup with conscious ingestion
- **[Personal Assistant](./examples/personal_assistant.py)** - AI assistant with intelligent memory
- **[Memory Retrieval](./memory_retrival_example.py)** - Function calling with memory tools
- **[Advanced Config](./examples/advanced_config.py)** - Production configuration
- **[Interactive Demo](./memori_example.py)** - Live conscious ingestion showcase

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and guidelines.

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

---

*Made for developers who want their AI agents to remember and learn*