"""
Memoriai - The Open-Source Memory Layer for AI Agents & Multi-Agent Systems v1.0

Pydantic-based intelligent memory processing with structured outputs.
"""

__version__ = "1.0.0"
__author__ = "Harshal More"
__email__ = "harshalmore2468@gmail.com"

# Agents
from .agents.memory_agent import MemoryAgent
from .agents.retrieval_agent import MemorySearchEngine
from .core.database import DatabaseManager
# Core components
from .core.memory import Memori
# Database connectors
from .database.connectors import (MySQLConnector, PostgreSQLConnector,
                                  SQLiteConnector)
# Tools
from .tools.memory_tool import (MemoryTool, create_memory_search_tool,
                                create_memory_tool)
# Exceptions
from .utils.exceptions import AgentError, DatabaseError, MemoriError
# Pydantic models
from .utils.pydantic_models import (ConversationContext, EntityType,
                                    ExtractedEntities, MemoryCategory,
                                    MemoryCategoryType, MemoryImportance,
                                    ProcessedMemory, RetentionType)

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
