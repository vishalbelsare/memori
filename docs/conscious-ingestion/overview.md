# Conscious Ingestion System

Memori v1.1 introduces a revolutionary conscious ingestion system that mimics human memory patterns to provide intelligent, context-aware AI interactions.

## What is Conscious Ingestion?

Conscious ingestion is an AI-powered memory management system that:

1. **Automatically analyzes** your conversation patterns and preferences
2. **Identifies essential information** worth keeping in immediate memory
3. **Promotes key facts** to short-term memory for instant access
4. **Intelligently injects context** into every AI conversation

## How It Works

### Three-Layer Intelligence

```
┌─────────────────────┐
│   Retrieval Agent   │ ← Selects relevant context for injection
├─────────────────────┤
│  Conscious Agent    │ ← Analyzes patterns, promotes essentials  
├─────────────────────┤
│   Memory Agent      │ ← Processes every conversation
└─────────────────────┘
```

### The Process

1. **Every Conversation** → Memory Agent processes with Pydantic structured outputs
2. **Every 6 Hours** → Conscious Agent analyzes patterns and promotes essentials
3. **Every Query** → Retrieval Agent selects 3-5 most relevant memories
4. **Automatic Context** → Essential + relevant memories injected seamlessly

## Enabling Conscious Ingestion

### Simple Setup

```python
from memori import Memori

memori = Memori(
    database_connect="sqlite:///my_memory.db",
    conscious_ingest=True,  # 🔥 The magic parameter
    openai_api_key="sk-..."  # Required for AI agents
)

memori.enable()  # Start recording and analysis
```

### What Happens

✅ **Background Analysis**: AI agent runs every 6 hours  
✅ **Essential Promotion**: Key personal facts moved to immediate access  
✅ **Smart Context**: 3-5 most relevant memories auto-injected  
✅ **Continuous Learning**: System adapts to your patterns  

## What Gets Learned

### Personal Identity
- Name, role, location
- Company, team, responsibilities
- Contact preferences

### Preferences & Habits
- Technology preferences
- Coding style preferences
- Work schedule and patterns
- Communication style

### Skills & Expertise
- Programming languages
- Frameworks and tools
- Domain knowledge
- Learning goals

### Current Projects
- Active work projects
- Learning objectives
- Immediate priorities
- Deadlines and milestones

### Relationships
- Team members and roles
- Important contacts
- Collaboration patterns
- Communication preferences

### Rules & Guidelines
- Work policies
- Personal principles
- Development standards
- Decision-making criteria

## Memory Categories

Every piece of information gets categorized for intelligent retrieval:

| Category | Description | Auto-Promoted |
|----------|-------------|---------------|
| **fact** | Objective information, technical details | ✅ High frequency |
| **preference** | Personal choices, likes/dislikes | ✅ Personal identity |
| **skill** | Abilities, expertise, learning progress | ✅ Expertise areas |
| **context** | Project info, work environment | ✅ Current projects |
| **rule** | Guidelines, policies, constraints | ✅ Work patterns |

## Context Injection Strategy

### Priority System

When you ask a question, the system injects:

1. **Essential Memories (3)**: Your most important promoted facts
2. **Contextually Relevant (2)**: Specific to your current query
3. **Smart Deduplication**: No repeated information

### Selection Algorithm

```python
# Simplified selection process
essential = get_promoted_essentials(limit=3)
relevant = search_contextual(query, limit=2)
context = combine_without_duplicates(essential, relevant)
inject_into_conversation(context)
```

## Examples

### Personal Assistant

```python
# After a few conversations about your preferences
memori = Memori(conscious_ingest=True)

# This query automatically includes:
# - Your name and role (essential)
# - Your technology preferences (essential)  
# - Recent project context (relevant)
response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Help me choose a database"}]
)
# AI knows you prefer PostgreSQL, your current project needs, etc.
```

### Code Assistant

```python
# System learns your coding patterns
conversations = [
    "I'm a Python developer who prefers FastAPI",
    "I always write tests first",
    "I like clean, documented code with type hints"
]

# Later query gets automatic context:
query = "Help me structure this new microservice"
# AI knows: Python, FastAPI, test-first, clean code preferences
```

## Manual Control

### Trigger Analysis

```python
# Force background analysis (normally every 6 hours)
memori.trigger_conscious_analysis()
```

### View Essential Memories

```python
# See what's been promoted to essential status
essential = memori.get_essential_conversations(limit=10)
for conv in essential:
    print(f"Essential: {conv.get('summary', '')}")
```

### Memory Statistics

```python
# Check memory system health
stats = memori.get_memory_stats()
print(f"Total conversations: {stats['total_conversations']}")
print(f"Essential memories: {len(memori.get_essential_conversations())}")
```

## Configuration Options

### Analysis Interval

```python
# Default: 6 hours
# Can be configured when creating custom conscious agents
from memori.agents import ConsciouscAgent

agent = ConsciouscAgent(api_key="sk-...")
agent.analysis_interval = timedelta(hours=3)  # More frequent
```

### Verbose Mode

```python
# See what's happening behind the scenes
memori = Memori(
    conscious_ingest=True,
    verbose=True  # Shows agent activity
)
```

### Namespace Separation

```python
# Separate memory spaces for different contexts
work_memori = Memori(conscious_ingest=True, namespace="work")
personal_memori = Memori(conscious_ingest=True, namespace="personal")
```

## Performance & Token Usage

### Efficiency Features

- **Structured Outputs**: Pydantic models reduce parsing overhead
- **Essential Priority**: Most important info always included
- **Smart Limits**: Maximum 5 memories to prevent token overflow
- **Background Processing**: Analysis doesn't block conversations
- **Graceful Degradation**: Works even if analysis fails

### Token Optimization

```
Traditional Context Injection:
❌ 2000+ tokens of conversation history

Conscious Ingestion:
✅ 200-500 tokens of essential + relevant facts
```

## Monitoring

### Log Messages

With `verbose=True`, you'll see:

```
[CONSCIOUS] Starting background analysis...
[MEMORY] Processing conversation: "I prefer FastAPI"
[MEMORY] Categorized as 'preference', importance: 0.8
[CONSCIOUS] Promoted 3 essential memories
[RETRIEVAL] Injecting 5 relevant memories for query
```

### Health Checks

```python
# Verify system is working
if memori.conscious_ingest:
    print("✅ Conscious ingestion active")
    
if memori.conscious_agent.last_analysis:
    print(f"✅ Last analysis: {memori.conscious_agent.last_analysis}")
else:
    print("⏳ Analysis pending")
```

## Troubleshooting

### Common Issues

**No API Key**
```
ConsciouscAgent: No OpenAI API key found
```
Solution: Set `OPENAI_API_KEY` environment variable

**Analysis Fails**
```
Failed to analyze memories: rate limit exceeded
```
Solution: Wait for rate limit reset or upgrade plan

**No Essential Memories**
```
No essential information available yet
```
Solution: Have more conversations to build memory base

### Debug Commands

```python
# Check agent status
print(f"Conscious ingest: {memori.conscious_ingest}")
print(f"Last analysis: {memori.conscious_agent.last_analysis}")

# Force analysis
try:
    memori.trigger_conscious_analysis()
    print("✅ Analysis successful")
except Exception as e:
    print(f"❌ Analysis failed: {e}")

# Check memory count
essential = memori.get_essential_conversations()
print(f"Essential memories: {len(essential)}")
```

## Best Practices

### For Better Results

1. **Be Specific**: Share clear information about yourself and preferences
2. **Be Consistent**: Use consistent terminology for technologies and projects
3. **Share Context**: Mention your role, current work, and goals
4. **Natural Conversation**: Talk normally, the system learns from everything

### For Developers

1. **API Key Security**: Always use environment variables
2. **Error Handling**: Implement graceful degradation when agents fail
3. **Monitoring**: Use verbose mode to understand behavior
4. **Testing**: Test with different user profiles and conversation patterns

## Comparison

### Without Conscious Ingestion

```python
memori = Memori(conscious_ingest=False)

# Every conversation needs manual context
messages = [
    {"role": "system", "content": "User prefers Python, FastAPI, PostgreSQL..."},
    {"role": "user", "content": "Help me build an API"}
]
```

### With Conscious Ingestion

```python
memori = Memori(conscious_ingest=True)

# Context automatically injected
messages = [
    {"role": "user", "content": "Help me build an API"}
]
# System automatically knows: Python, FastAPI, PostgreSQL preferences
```

## Future Enhancements

Planned improvements:

- **Multi-model Support**: Support for Claude, Gemini structured outputs
- **Custom Agents**: Domain-specific conscious agents
- **Memory Compression**: Intelligent consolidation over time
- **Adaptive Intervals**: Dynamic analysis frequency
- **Memory Relationships**: Understanding connections between facts

## Getting Started

Ready to try conscious ingestion? Start with our examples:

1. **[Basic Demo](../examples/basic_usage.py)** - Simple conscious ingestion showcase
2. **[Personal Assistant](../examples/personal_assistant.py)** - AI that learns about you
3. **[Interactive Demo](../memori_example.py)** - Live conscious ingestion
4. **[Advanced Example](../examples/conscious_ingestion_demo.py)** - Full feature demonstration

The future of AI memory is here - no more repeating yourself! 🧠✨