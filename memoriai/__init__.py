"""
Memori - The Open-Source Memory Layer for AI Agents & Multi-Agent Systems
"""

__version__ = "0.0.1"
__author__ = "Harshal More"
__email__ = "harshalmore2468@gmail.com"

from .core.memory import Memori
from .agents.memory_agent import MemoryAgent
from .agents.retrieval_agent import RetrievalAgent
from .tools.memory_tool import MemoryTool, create_memory_tool, memori_tool_function, record_conversation
from .utils.enums import MemoryCategory, MemoryType
from .utils.exceptions import MemoriError, DatabaseError, AgentError

__all__ = [
    "Memori",
    "MemoryAgent",
    "RetrievalAgent",
    "MemoryTool",
    "create_memory_tool",
    "memori_tool_function", 
    "record_conversation",
    "MemoryCategory", 
    "MemoryType",
    "MemoriError",
    "DatabaseError", 
    "AgentError"
]
