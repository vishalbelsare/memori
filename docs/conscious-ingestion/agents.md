# Agent System Documentation

Memoriai v1.1 features a sophisticated multi-agent system for intelligent memory processing and conscious ingestion.

## Overview

The agent system consists of three specialized AI agents that work together to provide intelligent memory management:

1. **Memory Agent** - Processes every conversation with structured outputs
2. **Conscious Agent** - Analyzes memory patterns and promotes essential information
3. **Retrieval Agent** - Intelligently selects relevant context for injection

## Memory Agent

The Memory Agent is responsible for processing every conversation and extracting structured information using OpenAI's Structured Outputs with Pydantic models.

### Functionality

- **Categorization**: Classifies information as fact, preference, skill, context, or rule
- **Entity Extraction**: Identifies people, technologies, topics, skills, projects, and keywords
- **Importance Scoring**: Determines retention type (short-term, long-term, permanent)
- **Content Generation**: Creates searchable summaries and optimized text
- **Storage Decisions**: Determines what information should be stored and why

### Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **fact** | Factual information, definitions, technical details | "I use PostgreSQL for databases" |
| **preference** | User preferences, likes/dislikes, personal choices | "I prefer clean, readable code" |
| **skill** | Skills, abilities, competencies, learning progress | "Experienced with FastAPI" |
| **context** | Project context, work environment, current situations | "Working on e-commerce project" |
| **rule** | Rules, policies, procedures, guidelines | "Always write tests first" |

### Retention Guidelines

- **short_term**: Recent activities, temporary information (expires ~7 days)
- **long_term**: Important information, learned skills, preferences
- **permanent**: Critical rules, core preferences, essential facts

## Conscious Agent

The Conscious Agent runs background analysis to identify essential personal facts and promote them to short-term memory for immediate access.

### Background Analysis

**Frequency**: Every 6 hours when `conscious_ingest=True`

**Selection Criteria**:
1. **Personal Identity**: Name, occupation, location, basic information
2. **Preferences & Habits**: Likes, dislikes, routines, work patterns
3. **Skills & Expertise**: Technical skills, programming languages, tools
4. **Current Projects**: Ongoing work, projects, learning goals
5. **Relationships**: Important people, colleagues, connections
6. **Repeated References**: Information frequently mentioned or referenced

### Scoring System

The Conscious Agent uses multi-dimensional scoring:

- **Frequency Score**: How often information is referenced
- **Recency Score**: How recent and relevant the information is
- **Importance Score**: How critical the information is for understanding the person

### Essential Memory Promotion

Essential conversations are promoted to short-term memory for immediate context injection:

```python
# Get essential conversations
essential = memori.get_essential_conversations(limit=10)

# Manually trigger analysis
memori.trigger_conscious_analysis()
```

## Retrieval Agent

The Retrieval Agent understands user queries and plans effective memory retrieval strategies using intelligent search planning.

### Query Understanding

- **Intent Analysis**: Understands what the user is actually looking for
- **Parameter Extraction**: Identifies key entities, topics, and concepts
- **Strategy Planning**: Recommends the best approach to find relevant memories
- **Filter Recommendations**: Suggests appropriate filters for category, importance, etc.

### Search Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **keyword_search** | Direct keyword/phrase matching | Specific terms or technologies |
| **entity_search** | Search by entities (people, tech, topics) | "What did Mike say about React?" |
| **category_filter** | Filter by memory categories | "My preferences for code style" |
| **importance_filter** | Filter by importance levels | "Important information about project X" |
| **temporal_filter** | Search within specific time ranges | "Recent work on microservices" |
| **semantic_search** | Conceptual/meaning-based search | Similar concepts and related topics |

### Query Examples

- "What did I learn about X?" → Focus on facts and skills related to X
- "My preferences for Y" → Focus on preference category
- "Rules about Z" → Focus on rule category  
- "Recent work on A" → Temporal filter + context/skill categories
- "Important information about B" → Importance filter + keyword search

## Configuration

### Enabling Conscious Ingestion

```python
from memoriai import Memori

memori = Memori(
    database_connect="sqlite:///memory.db",
    conscious_ingest=True,  # Enable conscious agent system
    openai_api_key="sk-..."  # Required for agents
)

memori.enable()  # Start background analysis
```

### Agent Settings

The agents use OpenAI's structured outputs and require an API key:

- **Model**: GPT-4o (recommended for best results)
- **API Key**: Set via `openai_api_key` parameter or `OPENAI_API_KEY` environment variable
- **Analysis Interval**: 6 hours (configurable)

### Manual Control

```python
# Manually trigger conscious analysis
memori.trigger_conscious_analysis()

# Get essential conversations
essential = memori.get_essential_conversations(limit=5)

# Check if conscious ingestion is enabled
if memori.conscious_ingest:
    print("Conscious ingestion is active")

# Get analysis statistics
stats = memori.get_memory_stats()
```

## Context Injection Strategy

When `conscious_ingest=True`, the system uses an intelligent context injection strategy:

### Priority System

1. **Essential Conversations** (3 memories): Always included from promoted memories
2. **Contextually Relevant** (2 memories): Selected based on current query
3. **Smart Limits**: Maximum 5 memories to avoid token overflow

### Selection Algorithm

```python
# Pseudo-code for context selection
essential_memories = get_essential_conversations(limit=3)
relevant_memories = search_relevant_memories(query, limit=2)

# Combine with deduplication
context = combine_and_deduplicate(essential_memories, relevant_memories)
inject_context(context)
```

## Monitoring and Debugging

### Verbose Mode

Enable verbose logging to see agent activity:

```python
memori = Memori(
    database_connect="sqlite:///memory.db",
    conscious_ingest=True,
    verbose=True  # Show agent activity
)
```

### Log Messages

- Memory processing by Memory Agent
- Background analysis by Conscious Agent
- Context injection by Retrieval Agent
- Essential memory promotions
- Analysis intervals and triggers

## Performance Considerations

### Token Usage

The agent system is designed to be token-efficient:

- **Structured Outputs**: Reduces parsing overhead
- **Essential Memory**: Prioritizes most important information
- **Smart Limits**: Prevents context overflow
- **Summarization**: Creates concise, searchable content

### Background Processing

- **Asynchronous**: Analysis runs in background without blocking
- **Interval-based**: Only runs every 6 hours to minimize API calls
- **Graceful Degradation**: Continues working if agents fail

## Troubleshooting

### Common Issues

**No API Key**:
```
ConsciouscAgent: No OpenAI API key found. Set OPENAI_API_KEY environment variable
```
**Solution**: Set API key in environment or pass to constructor

**Analysis Fails**:
```
Failed to analyze memories: API rate limit exceeded
```
**Solution**: Wait for rate limit reset or upgrade API plan

**No Essential Memories**:
```
No essential information available yet
```
**Solution**: Have more conversations to build up memory base

### Debug Commands

```python
# Check if agents are working
print(f"Conscious ingest enabled: {memori.conscious_ingest}")

# Get last analysis time
print(f"Last analysis: {memori.conscious_agent.last_analysis}")

# Check memory statistics
stats = memori.get_memory_stats()
print(f"Total memories: {stats.get('total_memories', 0)}")

# Get essential conversations
essential = memori.get_essential_conversations()
print(f"Essential conversations: {len(essential)}")
```

## Best Practices

### For Users

1. **Be Specific**: Share clear information about yourself, preferences, and projects
2. **Be Consistent**: Use consistent terminology for technologies and concepts
3. **Share Context**: Mention your role, current projects, and goals
4. **Reference Previous**: Build on previous conversations naturally

### For Developers

1. **API Key Management**: Always use environment variables for API keys
2. **Error Handling**: Implement graceful degradation when agents fail
3. **Monitoring**: Use verbose mode to understand agent behavior
4. **Testing**: Test with different conversation patterns and user types

## Future Enhancements

Planned improvements to the agent system:

- **Multi-Model Support**: Support for other structured output models
- **Custom Agents**: Ability to create specialized agents for specific domains
- **Advanced Reasoning**: More sophisticated memory relationship analysis
- **Adaptive Intervals**: Dynamic analysis frequency based on conversation patterns
- **Memory Compression**: Intelligent memory consolidation over time