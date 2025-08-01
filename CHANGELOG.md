# Changelog

All notable changes to Memori will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-08-1

### Added
- **OpenAI-powered Memory Agent**: Intelligent conversation processing using GPT-4 with enum-driven categorization
- **Retrieval Agent**: Smart memory retrieval using OpenAI for query understanding and strategy planning
- **Auto-recording Integrations**: Automatic conversation recording for popular LLM libraries
  - OpenAI API integration with hooks for `chat.completions.create()`
  - LiteLLM integration supporting 100+ models
  - Anthropic Claude API integration
- **Enhanced Memory System**: 
  - Enum-driven memory categorization (STORE_AS_FACT, UPDATE_PREFERENCE, STORE_AS_RULE, etc.)
  - Importance scoring (0.0-1.0) for memory prioritization
  - Memory type classification (SHORT_TERM, LONG_TERM, RULES)
- **Automatic Hook Installation**: `memori.enable()` now automatically installs hooks into LLM libraries
- **Memory Filtering**: Configurable filters for selective memory ingestion
- **Integration Statistics**: Monitor active integrations and recording stats

### Enhanced
- **Database Schema**: Improved with proper indexing and metadata support
- **Memory Retrieval**: Intelligent query planning with multiple search strategies
- **Error Handling**: Graceful fallbacks when OpenAI agents are unavailable
- **Logging**: Enhanced logging with loguru for better debugging

### Changed
- **Memory Agent Architecture**: Switched from keyword-based to OpenAI-powered categorization
- **Enable/Disable Flow**: Now installs/uninstalls LLM library hooks automatically
- **API Interface**: Added `openai_api_key` parameter to Memori constructor

### Examples
- Added `simple_example.py` demonstrating auto-recording functionality
- Shows integration with LiteLLM for automatic conversation capture

### Technical Improvements
- Proper separation of concerns: Memory Agent and Retrieval Agent
- Integration system with hook management
- Fallback mechanisms for offline/API-free usage
- Enhanced memory metadata and reasoning tracking

## [0.0.1] - 2025-07-31

### Added
- Initial Memori implementation
- Basic SQLite database support
- Simple memory categorization
- Manual conversation recording
- Basic memory retrieval
