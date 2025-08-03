"""
Memoriai - The Open-Source Memory Layer for AI Agents & Multi-Agent Systems v1.0

Pydantic-based intelligent memory processing with structured outputs.
"""

__version__ = "1.0.0"
__author__ = "Harshal More"
__email__ = "harshalmore2468@gmail.com"

# Core components
from .core.memory import Memori
from .core.database import DatabaseManager

# Agents
from .agents.memory_agent import MemoryAgent
from .agents.retrieval_agent import MemorySearchEngine

# Tools
from .tools.memory_tool import MemoryTool, create_memory_tool, create_memory_search_tool

# Pydantic models
from .utils.pydantic_models import (
    ProcessedMemory,
    MemoryCategory,
    ExtractedEntities,
    MemoryImportance,
    ConversationContext,
    MemoryCategoryType,
    RetentionType,
    EntityType,
)

# Exceptions
from .utils.exceptions import MemoriError, DatabaseError, AgentError

# Database connectors
from .database.connectors import SQLiteConnector, PostgreSQLConnector, MySQLConnector

__all__ = [
    # Core
    "Memori",
    "DatabaseManager",
    # Agents
    "MemoryAgent",
    "MemorySearchEngine",
    # Tools
    "MemoryTool",
    "create_memory_tool",
    "create_memory_search_tool",
    # Pydantic Models
    "ProcessedMemory",
    "MemoryCategory",
    "ExtractedEntities",
    "MemoryImportance",
    "ConversationContext",
    "MemoryCategoryType",
    "RetentionType",
    "EntityType",
    # Exceptions
    "MemoriError",
    "DatabaseError",
    "AgentError",
    # Database Connectors
    "SQLiteConnector",
    "PostgreSQLConnector",
    "MySQLConnector",
]
