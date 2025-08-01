# Changelog

All notable changes to Memori will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### 🎉 **Major Release: Pydantic-based Memory Processing**

This is a complete architectural overhaul moving from enum-driven function calling to Pydantic BaseModel + OpenAI Structured Outputs for more reliable, structured memory processing.

### Added
- **🔧 Pydantic-based Memory Agent**: Complete rewrite using OpenAI Structured Outputs with `client.beta.chat.completions.parse()`
- **📊 Structured Memory Processing**: Full `ProcessedMemory` objects with comprehensive entity extraction
- **🧠 Advanced Entity System**: Automatic extraction of people, technologies, topics, skills, projects, and keywords
- **🔍 Intelligent Search Engine**: Pydantic-based query understanding and multi-strategy search planning
- **💾 Enhanced Database Schema**: 
  - Full-text search (FTS5) support for advanced text search
  - Entity indexing for fast entity-based retrieval
  - Memory relationships table for future graph features
  - Comprehensive metadata storage with ProcessedMemory JSON
- **📈 Multi-dimensional Importance Scoring**: Novelty, relevance, and actionability scores
- **🎯 User Context Management**: Project, skill, and preference tracking for better categorization
- **⚡ Advanced Retrieval Strategies**: Keyword, entity, category, importance, and semantic search

### Enhanced
- **🗄️ Database Architecture**: Complete schema redesign with entity indexing and FTS support
- **🎨 Memory Categories**: Expanded to fact, preference, skill, context, rule with confidence scoring
- **🔄 Retention Types**: Short-term (7 days), long-term, and permanent retention strategies
- **📋 Memory Metadata**: Rich metadata with reasoning, processing timestamps, and agent versioning
- **🔍 Search Capabilities**: Multi-strategy search with relevance ranking and search metadata

### Changed
- **🚀 Breaking Change**: Complete API overhaul - migrated from enum-driven to Pydantic-based approach
- **⚡ OpenAI Integration**: Now uses `gpt-4o` with Structured Outputs for reliable parsing
- **📊 Memory Storage**: ProcessedMemory objects stored as JSON with extracted fields for indexing
- **🎯 Memory Agent**: Switched from function calling to `response_format=ProcessedMemory`
- **🔍 Search Engine**: Replaced RetrievalAgent with MemorySearchEngine using structured query planning

### New Features
- **🏷️ Entity-based Search**: Search memories by specific entities (people, technologies, etc.)
- **📁 Category Filtering**: Filter memories by specific categories
- **⭐ Importance Filtering**: Search high-importance memories
- **👤 User Context**: Track current projects, skills, and preferences for better processing
- **📊 Advanced Statistics**: Comprehensive memory analytics with entity counts and category breakdowns
- **💾 Memory Relationships**: Foundation for future graph-based memory connections

### Technical Improvements
- **✅ Structured Validation**: All memory data validated through Pydantic models
- **🛡️ Error Handling**: Improved error handling with refusal detection and fallback processing
- **📝 Comprehensive Logging**: Detailed logging for memory processing and search operations
- **⚡ Performance**: Optimized database queries with proper indexing and FTS
- **🔧 Maintainability**: Clean separation of concerns with well-defined interfaces

### Examples & Documentation
- **📖 Updated Examples**: Complete rewrite of `simple_example.py` showcasing v1.0 features
- **📊 Usage Patterns**: Demonstrates entity search, category filtering, and context management
- **🎯 Real-world Scenarios**: Examples for coding assistants, learning systems, and preference tracking

### Migration Notes
- **⚠️ Breaking Changes**: This release requires code changes for existing users
- **📈 Benefits**: Significantly more reliable and structured memory processing
- **🎯 Upgrade Path**: See migration guide for converting from v0.x to v1.0

## [0.0.2] - 2025-01-10

### Added (Legacy - Enum-based Approach)
- **OpenAI-powered Memory Agent**: Intelligent conversation processing using GPT-4 with enum-driven categorization  
- **Retrieval Agent**: Smart memory retrieval using OpenAI for query understanding and strategy planning
- **Auto-recording Integrations**: Automatic conversation recording for popular LLM libraries
- **Enhanced Memory System**: Enum-driven memory categorization and importance scoring

## [0.0.1] - 2025-07-31

### Added
- Initial Memori implementation
- Basic SQLite database support
- Simple memory categorization
- Manual conversation recording
- Basic memory retrieval
