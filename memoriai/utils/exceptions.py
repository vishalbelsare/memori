"""
Custom exceptions for Memori
"""

class MemoriError(Exception):
    """Base exception for Memori"""
    pass

class DatabaseError(MemoriError):
    """Database-related errors"""
    pass

class AgentError(MemoriError):
    """Memory agent-related errors"""
    pass

class ConfigurationError(MemoriError):
    """Configuration-related errors"""
    pass