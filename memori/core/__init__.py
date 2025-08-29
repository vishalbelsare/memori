"""
Memori Core Module

Provides the modular core components for memory management.
Clean, maintainable architecture with proper separation of concerns.
"""

# Main memory manager (modular architecture)
from ..config.memory_manager import MemoryManager

# Legacy components (for backward compatibility)
from .memory import Memori
from .database import DatabaseManager

# Interceptors
from ..interceptors import InterceptorManager

__all__ = [
    # Main classes
    "MemoryManager",
    "Memori",
    "DatabaseManager",
    
    # Interceptors
    "InterceptorManager",
]