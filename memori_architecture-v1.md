# Memori v1.0

The Open-Source Memory Layer for AI Agents & Multi-Agent Systems !

#### Philosophy of Memory v1.0 :
- Flexible, connect to any database with structured memory processing
- Second-memory for all your LLM testing without need to give context of previous work again and again
- Pydantic-based intelligent categorization instead of simple enum-driven approach
- Basic but solid foundation with entity extraction and memory search capabilities
- Simple, reliable architecture that just works out of the box

#### Tech Stack v1.0 :
- **Core Processing**: Pydantic BaseModel + OpenAI Structured Outputs
- **Database**: SQLite/PostgreSQL for structured storage
- **Memory Agent**: Single intelligent agent for processing and categorization
- **Search**: Basic SQL-based memory retrieval with entity matching
- **Integration**: LiteLLM, OpenAI, Anthropic support

```bash
pip install memoriai
```

##### File Structure v1.0

```md
memori/
├── core/
│   ├── __init__.py
│   ├── memory.py              # Main memory management
│   ├── agent.py               # Pydantic-based memory agent
│   └── database.py            # Database connections & queries
├── database/
│   ├── basic_template.py      # Pydantic schema definitions
│   └── migrations/            # Database setup
├── search/
│   ├── memory_search.py       # Basic memory retrieval
│   └── entity_matcher.py      # Entity-based search
├── utils/
│   ├── pydantic_models/       # All Pydantic schemas
│   └── integrations/          # LLM provider adapters
└── tools/
    └── retrieval_tool.py      # Memory search tool for LLMs
```

## Basic Usage Pattern v1.0

```python
from memori import Memori

office_work = Memori(
    database_connect="sqlite:///office_memory.db",   # SQLite, PostgreSQL supported
    template="basic_v1",
    mem_prompt="Only record {python} related stuff !",  # optional parameter
    conscious_ingest=True,  # Fetches necessary data from memory for context
)

office_work.enable()  # Initialize database and start memory processing

from litellm import completion
from dotenv import load_dotenv
import json

load_dotenv()

# Memory automatically processes conversations using Pydantic models
response = completion(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "I'm learning PyTorch for deep learning projects"
        }
    ]
)

# Memory agent automatically:
# - Extracts entities (PyTorch, deep learning, projects)
# - Categorizes the memory (skill, fact, preference, etc.)
# - Stores structured data with confidence scores
# - Makes it searchable for future retrieval

print(response)
```

## Pydantic Schema Templates v1.0

### Core Memory Processing Models

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime

# Basic Memory Categorization
class MemoryCategory(BaseModel):
    primary_category: Literal["fact", "preference", "skill", "context", "rule"]
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in categorization")
    reasoning: str = Field(description="Why this category was chosen")

# Entity Extraction
class ExtractedEntities(BaseModel):
    people: List[str] = Field(default_factory=list, description="Names mentioned")
    technologies: List[str] = Field(default_factory=list, description="Tech/tools mentioned")
    topics: List[str] = Field(default_factory=list, description="Main topics discussed")
    skills: List[str] = Field(default_factory=list, description="Skills mentioned")
    projects: List[str] = Field(default_factory=list, description="Projects mentioned")
    keywords: List[str] = Field(default_factory=list, description="Important keywords")

# Basic Importance Scoring
class MemoryImportance(BaseModel):
    importance_score: float = Field(ge=0.0, le=1.0, description="Overall importance")
    retention_type: Literal["short_term", "long_term", "permanent"] 
    reasoning: str = Field(description="Why this importance level")

# Complete Memory Processing
class ProcessedMemory(BaseModel):
    category: MemoryCategory
    entities: ExtractedEntities
    importance: MemoryImportance
    summary: str = Field(description="Concise summary of the memory")
    searchable_content: str = Field(description="Content optimized for search")
    should_store: bool = Field(description="Whether to store this memory")
    timestamp: datetime = Field(default_factory=datetime.now)
```

### Database Schema v1.0

```yml
# Main Chat History
chat_history:
  - chat_id: TEXT (primary key)
  - user_input: TEXT
  - llm_output: TEXT
  - model: TEXT
  - session_id: TEXT
  - timestamp: DATETIME
  - metadata: JSON

# Short-term Memory (limited storage, recent conversations)
short_term_memory:
  - memory_id: TEXT (primary key)
  - chat_id: TEXT (foreign key)
  - processed_data: JSON  # Full ProcessedMemory object
  - importance_score: REAL
  - created_at: DATETIME
  - expires_at: DATETIME

# Long-term Memory (permanent storage for important memories)
long_term_memory:
  - memory_id: TEXT (primary key) 
  - original_chat_id: TEXT
  - processed_data: JSON  # Full ProcessedMemory object
  - category_primary: TEXT
  - importance_score: REAL
  - created_at: DATETIME
  - last_accessed: DATETIME
  - access_count: INTEGER

# User Rules & Preferences
memory_rules:
  - rule_id: TEXT (primary key)
  - rule_text: TEXT
  - rule_type: TEXT  # preference, instruction, constraint
  - active: BOOLEAN
  - created_at: DATETIME
  - updated_at: DATETIME

# Entity Index for Search
memory_entities:
  - entity_id: TEXT (primary key)
  - memory_id: TEXT (foreign key to long_term_memory)
  - entity_type: TEXT  # person, technology, topic, skill, project
  - entity_value: TEXT
  - relevance_score: REAL
  - source_memory_type: TEXT  # short_term or long_term
```

## Memory Agent v1.0

### Pydantic-Based Processing

```python
class MemoriAgent:
    """Single agent handling all memory operations with Pydantic models"""
    
    def __init__(self, config):
        self.config = config
        self.client = OpenAI()
    
    async def process_conversation(self, user_input: str, llm_output: str, context: Dict) -> ProcessedMemory:
        """Process conversation using structured Pydantic output"""
        
        conversation_text = f"User: {user_input}\nAssistant: {llm_output}"
        
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a memory processing agent. Analyze conversations and extract structured information.
                    
                    Your job is to:
                    1. Categorize the memory type (fact, preference, skill, context, rule)
                    2. Extract relevant entities (people, tech, topics, skills, projects)
                    3. Score the importance for retention decisions
                    4. Create searchable summary content
                    5. Decide if this memory should be stored
                    
                    Focus on practical, useful information that would help in future conversations."""
                },
                {
                    "role": "user", 
                    "content": f"Process this conversation:\n\n{conversation_text}\n\nContext: {json.dumps(context)}"
                }
            ],
            response_format=ProcessedMemory
        )
        
        return response.parsed
    
    def determine_storage_location(self, processed_memory: ProcessedMemory) -> str:
        """Decide whether memory goes to short-term or long-term storage"""
        
        if processed_memory.importance.retention_type == "permanent":
            return "long_term"
        elif processed_memory.importance.retention_type == "long_term":
            return "long_term" 
        else:
            return "short_term"
```

## Memory Search v1.0

### Basic Retrieval Engine

```python
class MemorySearch:
    """Basic memory search using SQL queries and entity matching"""
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    def search_memories(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search memories using keyword matching and entity lookup"""
        
        # Simple keyword search in summaries and content
        keyword_results = self._keyword_search(query, max_results)
        
        # Entity-based search for more specific queries
        entity_results = self._entity_search(query, max_results)
        
        # Combine and rank results
        combined_results = self._merge_results(keyword_results, entity_results)
        
        return combined_results[:max_results]
    
    def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """Basic SQL LIKE search in memory content"""
        sql = """
            SELECT memory_id, processed_data, importance_score, created_at
            FROM long_term_memory 
            WHERE processed_data->>'summary' LIKE ? 
               OR processed_data->>'searchable_content' LIKE ?
            ORDER BY importance_score DESC, created_at DESC
            LIMIT ?
        """
        return self.db.execute(sql, [f"%{query}%", f"%{query}%", limit]).fetchall()
    
    def _entity_search(self, query: str, limit: int) -> List[Dict]:
        """Search by matching entities"""
        sql = """
            SELECT m.memory_id, m.processed_data, m.importance_score, m.created_at
            FROM long_term_memory m
            JOIN memory_entities e ON m.memory_id = e.memory_id
            WHERE e.entity_value LIKE ?
            ORDER BY e.relevance_score DESC, m.importance_score DESC
            LIMIT ?
        """
        return self.db.execute(sql, [f"%{query}%", limit]).fetchall()

# Memory Search Tool for LLM Integration
def create_memory_search_tool(memori_instance):
    """Create memory search tool for LLM function calling"""
    
    def memory_search(query: str, max_results: int = 5) -> str:
        """Search through stored memories for relevant information"""
        try:
            results = memori_instance.search_engine.search_memories(query, max_results)
            
            if not results:
                return "No relevant memories found."
            
            formatted_results = []
            for result in results:
                memory_data = json.loads(result['processed_data'])
                formatted_results.append({
                    "summary": memory_data['summary'],
                    "category": memory_data['category']['primary_category'],
                    "importance": result['importance_score'],
                    "date": result['created_at'],
                    "entities": memory_data['entities']
                })
            
            return json.dumps({
                "found": len(formatted_results),
                "memories": formatted_results
            }, indent=2)
            
        except Exception as e:
            return f"Memory search error: {str(e)}"
    
    return memory_search
```

## Conscious Ingestion v1.0

### Basic Context Retrieval

```python
conscious_ingest_v1 = {
    "enabled": True,
    "sources": [
        {
            "name": "recent_short_term",
            "query": "SELECT * FROM short_term_memory ORDER BY created_at DESC LIMIT 5",
            "weight": 1.0
        },
        {
            "name": "relevant_rules", 
            "query": "SELECT * FROM memory_rules WHERE active = TRUE",
            "weight": 0.8
        },
        {
            "name": "high_importance_memories",
            "query": "SELECT * FROM long_term_memory WHERE importance_score > 0.7 ORDER BY last_accessed DESC LIMIT 3",
            "weight": 0.6
        }
    ],
    "max_context_tokens": 1500
}

def get_conscious_context(memori_instance, current_query: str) -> str:
    """Retrieve relevant context for conscious ingestion"""
    
    context_parts = []
    
    # Get recent short-term memories
    recent_memories = memori_instance.db.execute(
        "SELECT processed_data FROM short_term_memory ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    
    for memory in recent_memories:
        data = json.loads(memory['processed_data'])
        context_parts.append(f"[Recent] {data['summary']}")
    
    # Get relevant rules
    rules = memori_instance.db.execute(
        "SELECT rule_text FROM memory_rules WHERE active = TRUE"
    ).fetchall()
    
    for rule in rules:
        context_parts.append(f"[Rule] {rule['rule_text']}")
    
    # Search for relevant long-term memories
    relevant_memories = memori_instance.search_engine.search_memories(current_query, 3)
    for memory in relevant_memories:
        data = json.loads(memory['processed_data'])
        context_parts.append(f"[Memory] {data['summary']}")
    
    return "\n".join(context_parts[:10])  # Limit context size
```

## Enhanced Tool Integration v1.0

### LLM Integration Example

```python
from memori import Memori
from memori.tools import create_memory_search_tool

# Initialize Memori v1.0
personal = Memori(
    database_connect="sqlite:///personal_memory.db",
    template="basic_v1", 
    mem_prompt="Focus on programming, learning, and personal projects",
    conscious_ingest=True
)

personal.enable()

# Create memory search tool
memory_tool = create_memory_search_tool(personal)

# LLM Integration with memory search capability
response = completion(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "What Python libraries have I been working with recently?"
        }
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "memory_search",
                "description": "Search through stored memories for relevant information",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for memories"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ],
    tool_choice="auto"
)

print(response)
```

## Workflow v1.0 - How Everything Works

### Memory Processing Pipeline

```
User Input + LLM Response
           ↓
    Memory Agent (Pydantic Processing)
           ↓
    [Categorization + Entity Extraction + Importance Scoring]
           ↓
    Storage Decision (Short-term vs Long-term)
           ↓
    Database Storage + Entity Indexing
```

### Memory Retrieval Pipeline

```
User Query → Memory Search Tool → SQL-based Search → Entity Matching → Results Ranking → Formatted Response
```

### Conscious Ingestion Flow

```
New User Query → Context Retrieval (Recent + Rules + Relevant) → Inject into LLM Prompt → Enhanced Response
```

## Core Features v1.0

✅ **Pydantic-Based Processing**: Structured memory extraction with validation
✅ **Intelligent Categorization**: Fact, preference, skill, context, rule classification  
✅ **Entity Extraction**: People, technologies, topics, skills, projects
✅ **Basic Search**: Keyword and entity-based memory retrieval
✅ **Conscious Ingestion**: Automatic context injection from stored memories
✅ **Flexible Storage**: Short-term and long-term memory management
✅ **LLM Integration**: Easy tool integration with OpenAI, Anthropic, etc.
✅ **Multi-Database Support**: SQLite, PostgreSQL compatibility

## Roadmap to v2.0

### Current v1.0 Limitations
- No vector search capabilities
- Basic SQL-only search
- No memory relationships or graphs
- No automatic aging or consolidation
- No advanced privacy/encryption features
- Single agent architecture

### Migration Path to v2.0
- Add vector database support
- Implement graph relationships
- Add memory lifecycle management
- Introduce multi-agent architecture
- Enhance search with semantic capabilities
- Add privacy and security features

---

*Memori v1.0 - Solid Foundation for Intelligent Memory*

