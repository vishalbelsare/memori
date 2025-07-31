"""
Enums for memory categorization and management
"""

from enum import Enum

class MemoryCategory(Enum):
    """Categories for memory classification"""
    STORE_AS_FACT = "fact"
    UPDATE_PREFERENCE = "preference"
    DISCARD_TRIVIAL = "discard"
    STORE_AS_RULE = "rule"
    STORE_AS_CONTEXT = "context"

class MemoryType(Enum):
    """Types of memory storage"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    RULES = "rules"
    CHAT_HISTORY = "chat_history"

class ImportanceLevel(Enum):
    """Importance levels for memory items"""
    LOW = 0.2
    MEDIUM = 0.5
    HIGH = 0.8
    CRITICAL = 1.0

class MemoryStatus(Enum):
    """Status of memory items"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"