"""
Database manager for handling memory storage operations
"""

import sqlite3
import json
from loguru import logger
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from ..utils.enums import MemoryCategory, MemoryType
from ..utils.exceptions import DatabaseError

class MemoryItem:
    """Represents a memory item"""
    def __init__(
        self,
        content: str,
        category: MemoryCategory,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance_score: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None
    ):
        self.memory_id = str(uuid.uuid4())
        self.content = content
        self.category = category
        self.memory_type = memory_type
        self.importance_score = importance_score
        self.metadata = metadata or {}
        self.chat_id = chat_id
        self.created_at = datetime.now()
        self.access_count = 0
        self.last_accessed = None

class DatabaseManager:
    """Manages database operations for memory storage"""
    
    def __init__(self, database_connect: str, template: str = "basic"):
        self.database_connect = database_connect
        self.template = template
        self.db_path = self._parse_connection_string(database_connect)
        
    def _parse_connection_string(self, connect_str: str) -> str:
        """Parse database connection string"""
        if connect_str.startswith("sqlite:///"):
            return connect_str.replace("sqlite:///", "")
        elif connect_str.startswith("sqlite://"):
            return connect_str.replace("sqlite://", "")
        else:
            # For now, only SQLite is implemented
            raise DatabaseError(f"Unsupported database type: {connect_str}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def initialize_schema(self):
        """Initialize database schema based on template"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Chat history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    chat_id TEXT PRIMARY KEY,
                    user_input TEXT NOT NULL,
                    ai_output TEXT NOT NULL,
                    model TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    session_id TEXT NOT NULL,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    tokens_used INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Short-term memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS short_term_memory (
                    memory_id TEXT PRIMARY KEY,
                    chat_id TEXT,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    importance_score REAL NOT NULL DEFAULT 0.5,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (chat_id) REFERENCES chat_history (chat_id)
                )
            """)
            
            # Long-term memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    memory_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    importance_score REAL NOT NULL DEFAULT 0.5,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMP NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Rules memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rules_memory (
                    rule_id TEXT PRIMARY KEY,
                    rule_type TEXT NOT NULL,
                    condition_text TEXT NOT NULL,
                    action_text TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    active BOOLEAN DEFAULT 1,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMP NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_namespace_session ON chat_history(namespace, session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_short_term_namespace ON short_term_memory(namespace)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_long_term_namespace ON long_term_memory(namespace)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_namespace ON rules_memory(namespace)")
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    
    def store_chat_history(
        self,
        chat_id: str,
        user_input: str,
        ai_output: str,
        model: str,
        timestamp: datetime,
        session_id: str,
        namespace: str = "default",
        tokens_used: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """Store chat history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history 
                (chat_id, user_input, ai_output, model, timestamp, session_id, namespace, tokens_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_id, user_input, ai_output, model, timestamp, 
                session_id, namespace, tokens_used, json.dumps(metadata or {})
            ))
            conn.commit()
    
    def store_memory_item(self, item: MemoryItem, namespace: str = "default"):
        """Store a memory item in appropriate table"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if item.memory_type == MemoryType.SHORT_TERM:
                # Calculate expiration (default: 7 days for short-term)
                expires_at = item.created_at + timedelta(days=7)
                
                cursor.execute("""
                    INSERT INTO short_term_memory
                    (memory_id, chat_id, content, category, importance_score, namespace, 
                     created_at, expires_at, access_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.memory_id, item.chat_id, item.content, item.category.value,
                    item.importance_score, namespace, item.created_at, expires_at,
                    item.access_count, json.dumps(item.metadata)
                ))
                
            elif item.memory_type == MemoryType.LONG_TERM:
                cursor.execute("""
                    INSERT INTO long_term_memory
                    (memory_id, content, category, importance_score, namespace,
                     created_at, access_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.memory_id, item.content, item.category.value,
                    item.importance_score, namespace, item.created_at,
                    item.access_count, json.dumps(item.metadata)
                ))
            
            conn.commit()
    
    def get_memory_item(self, memory_id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get a specific memory item"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Try short-term memory first
            cursor.execute("""
                SELECT * FROM short_term_memory 
                WHERE memory_id = ? AND namespace = ?
            """, (memory_id, namespace))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            # Try long-term memory
            cursor.execute("""
                SELECT * FROM long_term_memory 
                WHERE memory_id = ? AND namespace = ?
            """, (memory_id, namespace))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            return None
    
    def get_chat_history(
        self,
        namespace: str = "default",
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get chat history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if session_id:
                cursor.execute("""
                    SELECT * FROM chat_history 
                    WHERE namespace = ? AND session_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (namespace, session_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM chat_history 
                    WHERE namespace = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (namespace, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_memories(
        self,
        query: str,
        namespace: str = "default",
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by content"""
        results = []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Search short-term memory
            if not memory_types or MemoryType.SHORT_TERM in memory_types:
                cursor.execute("""
                    SELECT *, 'short_term' as memory_type FROM short_term_memory
                    WHERE namespace = ? AND content LIKE ?
                    AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY importance_score DESC, created_at DESC
                    LIMIT ?
                """, (namespace, f"%{query}%", datetime.now(), limit))
                
                results.extend([dict(row) for row in cursor.fetchall()])
            
            # Search long-term memory
            if not memory_types or MemoryType.LONG_TERM in memory_types:
                cursor.execute("""
                    SELECT *, 'long_term' as memory_type FROM long_term_memory
                    WHERE namespace = ? AND content LIKE ?
                    ORDER BY importance_score DESC, access_count DESC, created_at DESC
                    LIMIT ?
                """, (namespace, f"%{query}%", limit))
                
                results.extend([dict(row) for row in cursor.fetchall()])
        
        # Sort by importance and limit
        results.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
        return results[:limit]
    
    def clear_memory(self, namespace: str = "default", memory_type: Optional[str] = None):
        """Clear memory data"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if memory_type == "short_term":
                cursor.execute("DELETE FROM short_term_memory WHERE namespace = ?", (namespace,))
            elif memory_type == "long_term":
                cursor.execute("DELETE FROM long_term_memory WHERE namespace = ?", (namespace,))
            elif memory_type == "chat_history":
                cursor.execute("DELETE FROM chat_history WHERE namespace = ?", (namespace,))
            else:  # Clear all
                cursor.execute("DELETE FROM short_term_memory WHERE namespace = ?", (namespace,))
                cursor.execute("DELETE FROM long_term_memory WHERE namespace = ?", (namespace,))
                cursor.execute("DELETE FROM chat_history WHERE namespace = ?", (namespace,))
            
            conn.commit()
    
    def get_memory_stats(self, namespace: str = "default") -> Dict[str, Any]:
        """Get memory statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Chat history count
            cursor.execute("SELECT COUNT(*) FROM chat_history WHERE namespace = ?", (namespace,))
            stats['chat_history_count'] = cursor.fetchone()[0]
            
            # Short-term memory count
            cursor.execute("SELECT COUNT(*) FROM short_term_memory WHERE namespace = ?", (namespace,))
            stats['short_term_count'] = cursor.fetchone()[0]
            
            # Long-term memory count
            cursor.execute("SELECT COUNT(*) FROM long_term_memory WHERE namespace = ?", (namespace,))
            stats['long_term_count'] = cursor.fetchone()[0]
            
            # Rules count
            cursor.execute("SELECT COUNT(*) FROM rules_memory WHERE namespace = ?", (namespace,))
            stats['rules_count'] = cursor.fetchone()[0]
            
            return stats

