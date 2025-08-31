"""
Database adapters for different database backends
Provides database-specific implementations with proper security measures
"""

from .sqlite_adapter import SQLiteSearchAdapter
from .postgresql_adapter import PostgreSQLSearchAdapter  
from .mysql_adapter import MySQLSearchAdapter

__all__ = [
    'SQLiteSearchAdapter',
    'PostgreSQLSearchAdapter', 
    'MySQLSearchAdapter'
]