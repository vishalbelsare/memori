"""
Memoriai - The Open-Source Memory Layer for AI Agents & Multi-Agent Systems v1.0

Professional-grade memory layer with comprehensive error handling, configuration
management, and modular architecture for production AI systems.
"""

__version__ = "1.0.0"
__author__ = "Harshal More"
__email__ = "harshalmore2468@gmail.com"

# Memory agents
from .agents.memory_agent import MemoryAgent
from .agents.retrieval_agent import MemorySearchEngine

# Configuration system
from .config import (
    AgentSettings,
    ConfigManager,
    DatabaseSettings,
    LoggingSettings,
    MemoriSettings,
)
from .core.database import DatabaseManager

# Core components
from .core.memory import Memori

# Database system
from .database.connectors import MySQLConnector, PostgreSQLConnector, SQLiteConnector
from .database.queries import BaseQueries, ChatQueries, EntityQueries, MemoryQueries

# Wrapper integrations
from .integrations import MemoriAnthropic, MemoriOpenAI

# Tools and integrations
from .tools.memory_tool import MemoryTool, create_memory_search_tool, create_memory_tool

# Utils and models
from .utils import (  # Pydantic models; Enhanced exceptions; Validators and helpers; Logging
    AgentError,
    AsyncUtils,
    AuthenticationError,
    ConfigurationError,
    ConversationContext,
    DatabaseError,
    DataValidator,
    DateTimeUtils,
    EntityType,
    ExceptionHandler,
    ExtractedEntities,
    FileUtils,
    IntegrationError,
    JsonUtils,
    LoggingManager,
    MemoriError,
    MemoryCategory,
    MemoryCategoryType,
    MemoryImportance,
    MemoryNotFoundError,
    MemoryValidator,
    PerformanceUtils,
    ProcessedMemory,
    ProcessingError,
    RateLimitError,
    ResourceExhaustedError,
    RetentionType,
    RetryUtils,
    StringUtils,
    TimeoutError,
    ValidationError,
    get_logger,
)

__all__ = [
    # Core
    "Memori",
    "DatabaseManager",
    # Configuration
    "MemoriSettings",
    "DatabaseSettings",
    "AgentSettings",
    "LoggingSettings",
    "ConfigManager",
    # Agents
    "MemoryAgent",
    "MemorySearchEngine",
    # Database
    "SQLiteConnector",
    "PostgreSQLConnector",
    "MySQLConnector",
    "BaseQueries",
    "MemoryQueries",
    "ChatQueries",
    "EntityQueries",
    # Tools
    "MemoryTool",
    "create_memory_tool",
    "create_memory_search_tool",
    # Integrations
    "MemoriOpenAI",
    "MemoriAnthropic",
    # Pydantic Models
    "ProcessedMemory",
    "MemoryCategory",
    "ExtractedEntities",
    "MemoryImportance",
    "ConversationContext",
    "MemoryCategoryType",
    "RetentionType",
    "EntityType",
    # Enhanced Exceptions
    "MemoriError",
    "DatabaseError",
    "AgentError",
    "ConfigurationError",
    "ValidationError",
    "IntegrationError",
    "AuthenticationError",
    "RateLimitError",
    "MemoryNotFoundError",
    "ProcessingError",
    "TimeoutError",
    "ResourceExhaustedError",
    "ExceptionHandler",
    # Validators
    "DataValidator",
    "MemoryValidator",
    # Helpers
    "StringUtils",
    "DateTimeUtils",
    "JsonUtils",
    "FileUtils",
    "RetryUtils",
    "PerformanceUtils",
    "AsyncUtils",
    # Logging
    "LoggingManager",
    "get_logger",
]
