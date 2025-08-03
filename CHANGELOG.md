# Changelog

All notable changes to Memoriai will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-08-03

### 🧠 **Enhanced Conscious Ingestion System**

Major improvements to the intelligent memory processing and context injection system.

#### ✨ New Features

**Conscious Agent System**
- **Background Analysis**: Automatic analysis of long-term memory patterns every 6 hours
- **Essential Memory Promotion**: Promotes key personal facts to short-term memory for immediate access
- **Intelligent Context Selection**: AI-powered identification of most relevant memories for context injection
- **Personal Identity Extraction**: Automatically identifies and prioritizes user identity, preferences, and ongoing projects

**Enhanced Context Injection**
- **Essential Conversations**: Priority context from promoted memories for immediate relevance
- **Smart Memory Retrieval**: Up to 5 most relevant memories automatically injected into conversations
- **Category-Aware Context**: Different context strategies for facts, preferences, skills, and rules
- **Reduced Token Usage**: More efficient context injection with summarized essential information

**Improved Memory Processing**
- **Pydantic-Based Agents**: Structured memory processing with OpenAI Structured Outputs
- **Multi-Dimensional Scoring**: Frequency, recency, and importance scoring for memory selection
- **Entity Relationship Mapping**: Enhanced entity extraction and relationship tracking
- **Advanced Categorization**: Improved classification of facts, preferences, skills, context, and rules

#### 🔧 API Enhancements

**Conscious Ingestion Control**
```python
memori = Memori(
    database_connect="sqlite:///memory.db",
    conscious_ingest=True,  # Enable intelligent background analysis
    openai_api_key="sk-..."
)
```

**Memory Retrieval Methods**
- `get_essential_conversations()` - Access promoted essential memories
- `trigger_conscious_analysis()` - Manually trigger background analysis
- `retrieve_context()` - Enhanced context retrieval with essential memory priority

#### 📊 Background Processing

**Conscious Agent Features**
- **Automated Analysis**: Runs every 6 hours to analyze memory patterns
- **Selection Criteria**: Personal identity, preferences, skills, current projects, relationships
- **Memory Promotion**: Automatically promotes essential conversations to short-term memory
- **Analysis Reasoning**: Detailed reasoning for memory selection decisions

#### 🎯 Context Injection Improvements

**Essential Memory Integration**
- Essential conversations always included in context
- Smart memory limit management (3 essential + 2 specific)
- Category-based context prioritization
- Improved relevance scoring for memory selection

#### 🛠️ Developer Experience

**Enhanced Examples**
- Updated `memori_example.py` with conscious ingestion showcase
- New `memory_retrieval_example.py` demonstrating function calling integration
- Advanced configuration examples with conscious agent settings

## [1.0.0] - 2025-08-03

### 🎉 **Production-Ready Memory Layer for AI Agents**

Complete professional-grade memory system with modular architecture, comprehensive error handling, and configuration management.

### ✨ Core Features
- **Universal LLM Integration**: Works with ANY LLM library (LiteLLM, OpenAI, Anthropic)
- **Pydantic-based Intelligence**: Structured memory processing with validation
- **Automatic Context Injection**: Relevant memories automatically added to conversations
- **Multiple Memory Types**: Short-term, long-term, rules, and entity relationships
- **Advanced Search**: Full-text search with semantic ranking

### 🏗️ Architecture
- **Modular Design**: Separated concerns with clear component boundaries
- **SQL Query Centralization**: Dedicated query modules for maintainability
- **Configuration Management**: Pydantic-based settings with auto-loading
- **Comprehensive Error Handling**: Context-aware exceptions with sanitized logging
- **Production Logging**: Structured logging with multiple output targets

### 🗄️ Database Support
- **Multi-Database**: SQLite, PostgreSQL, MySQL connectors
- **Query Optimization**: Indexed searches and connection pooling
- **Schema Management**: Version-controlled migrations and templates
- **Full-Text Search**: FTS5 support for advanced text search

### 🔧 Developer Experience
- **Type Safety**: Full Pydantic validation throughout
- **Simple API**: One-line enablement with `memori.enable()`
- **Flexible Configuration**: File, environment, or programmatic setup
- **Rich Examples**: Basic usage, personal assistant, advanced config

### 📊 Memory Processing
- **Entity Extraction**: People, technologies, projects, skills
- **Smart Categorization**: Facts, preferences, skills, rules, context
- **Importance Scoring**: Multi-dimensional relevance assessment
- **Relationship Mapping**: Entity interconnections and memory graphs

### 🔌 Integrations
- **LiteLLM Native**: Uses official callback system (recommended)
- **OpenAI/Anthropic**: Clean wrapper classes for direct usage
- **Tool Support**: Memory search tools for function calling

### 🛡️ Security & Reliability
- **Input Sanitization**: Protection against injection attacks
- **Error Context**: Detailed error information without exposing secrets
- **Graceful Degradation**: Continues operation when components fail
- **Resource Management**: Automatic cleanup and connection pooling

### 📁 Project Structure
```
memoriai/
├── core/              # Main memory interface and database
├── config/            # Configuration management system
├── agents/            # Pydantic-based memory processing
├── database/          # Multi-database support and queries
├── integrations/      # LLM provider integrations
├── utils/             # Helpers, validation, logging
└── tools/             # Memory search and retrieval tools
```

### 🎯 Philosophy Alignment
- **Second-memory for LLM work**: Never repeat context again
- **Flexible database connections**: Production-ready adapters
- **Simple, reliable architecture**: Just works out of the box
- **Conscious context injection**: Intelligent memory retrieval

### ⚡ Quick Start
```python
from memoriai import Memori

memori = Memori(
    database_connect="sqlite:///my_memory.db",
    conscious_ingest=True,
    openai_api_key="sk-..."
)
memori.enable()  # Start recording all LLM conversations

# Use any LLM library - context automatically injected!
from litellm import completion
response = completion(model="gpt-4", messages=[...])
```

### 📚 Documentation
- Clean, focused README aligned with project vision
- Essential examples without complexity bloat
- Configuration guides for development and production
- Architecture documentation for contributors

### 🗂️ Archive Management
- Moved outdated files to `archive/` folder
- Updated `.gitignore` to exclude archive from version control
- Preserved development history while cleaning main structure

### 💡 Breaking Changes from Pre-1.0
- Moved from enum-driven to Pydantic-based processing
- Simplified API surface with focus on `enable()/disable()`
- Restructured package layout for better modularity
- Enhanced configuration system replaces simple parameters

---

*This release represents the culmination of the vision outlined in the original architecture documents, delivering a production-ready memory layer that "just works" for AI developers.*