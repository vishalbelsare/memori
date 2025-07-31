"""
Memori - The Open-Source Memory Layer for AI Agents & Multi-Agent Systems
"""

__version__ = "0.0.1"
__author__ = "Harshal More"
__email__ = "harshalmore2468@gmail.com"

from .core.memory import Memori
from .utils.enums import MemoryCategory, MemoryType
from .utils.exceptions import MemoriError, DatabaseError, AgentError

__all__ = [
    "Memori",
    "MemoryCategory", 
    "MemoryType",
    "MemoriError",
    "DatabaseError", 
    "AgentError"
]
