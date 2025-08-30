"""
Search adapters for different database backends
"""

from .sqlite_search_adapter import SQLiteSearchAdapter
from .mysql_search_adapter import MySQLSearchAdapter

__all__ = ["SQLiteSearchAdapter", "MySQLSearchAdapter"]