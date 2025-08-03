"""
Utils package for Memoriai - Comprehensive utilities and helpers
"""

# Core Pydantic models
from .pydantic_models import (
    ConversationContext, EntityType,
    ExtractedEntities, MemoryCategory,
    MemoryCategoryType, MemoryImportance,
    ProcessedMemory, RetentionType
)

# Enhanced exception handling
from .exceptions import (
    MemoriError,
    DatabaseError,
    AgentError,
    ConfigurationError,
    ValidationError,
    IntegrationError,
    AuthenticationError,
    RateLimitError,
    MemoryNotFoundError,
    ProcessingError,
    TimeoutError,
    ResourceExhaustedError,
    ExceptionHandler,
)

# Validation utilities
from .validators import DataValidator, MemoryValidator

# Helper utilities
from .helpers import (
    StringUtils,
    DateTimeUtils,
    JsonUtils,
    FileUtils,
    RetryUtils,
    PerformanceUtils,
    AsyncUtils,
)

# Logging utilities
from .logging import LoggingManager, get_logger

__all__ = [
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
