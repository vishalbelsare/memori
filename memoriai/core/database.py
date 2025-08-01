"""
Database Manager - Pydantic-based memory storage with entity indexing
"""

import sqlite3
import json
import uuid
from loguru import logger
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.pydantic_models import (
    ProcessedMemory, 
    MemoryCategoryType, 
    RetentionType,
    ExtractedEntity,
    UserRule,
    MemoryStats
)
from ..utils.exceptions import DatabaseError


class DatabaseManager:
    """Manages Pydantic-based memory storage with entity indexing and FTS search"""
    
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
        """Get database connection with FTS5 support"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Enable FTS5 for full-text search
            conn.execute("PRAGMA enable_fts3_tokenizer=1")
            
            return conn
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def initialize_schema(self):
        """Initialize database schema based on template"""
        try:
            # Read and execute schema from file
            schema_path = Path(__file__).parent.parent / "database" / "templates" / "schemas" / f"{self.template}.sql"
            
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                with self._get_connection() as conn:
                    # Execute schema in chunks (SQLite doesn't like multiple statements)
                    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                    for statement in statements:
                        try:
                            conn.execute(statement)
                        except sqlite3.Error as e:
                            # Log but continue for CREATE IF NOT EXISTS statements
                            logger.debug(f"Schema statement warning: {e}")
                    
                    conn.commit()
                    logger.info("Database schema initialized successfully")
            else:
                # Fallback to basic schema
                self._create_basic_schema()
                
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            # Fallback to basic schema
            self._create_basic_schema()
    
    def _create_basic_schema(self):
        """Create basic schema if SQL file is not available"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Basic tables for fallback
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS short_term_memory (
                    memory_id TEXT PRIMARY KEY,
                    chat_id TEXT,
                    processed_data TEXT NOT NULL,
                    importance_score REAL NOT NULL DEFAULT 0.5,
                    category_primary TEXT NOT NULL,
                    retention_type TEXT NOT NULL DEFAULT 'short_term',
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    searchable_content TEXT NOT NULL,
                    summary TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    memory_id TEXT PRIMARY KEY,
                    original_chat_id TEXT,
                    processed_data TEXT NOT NULL,
                    importance_score REAL NOT NULL DEFAULT 0.5,
                    category_primary TEXT NOT NULL,
                    retention_type TEXT NOT NULL DEFAULT 'long_term',
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMP NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    searchable_content TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    novelty_score REAL DEFAULT 0.5,
                    relevance_score REAL DEFAULT 0.5,
                    actionability_score REAL DEFAULT 0.5
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_entities (
                    entity_id TEXT PRIMARY KEY,
                    memory_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_value TEXT NOT NULL,
                    relevance_score REAL NOT NULL DEFAULT 0.5,
                    entity_context TEXT,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at TIMESTAMP NOT NULL
                )
            """)
            
            conn.commit()
            logger.info("Basic database schema created")
    
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
                INSERT OR REPLACE INTO chat_history 
                (chat_id, user_input, ai_output, model, timestamp, session_id, namespace, tokens_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_id, user_input, ai_output, model, timestamp, 
                session_id, namespace, tokens_used, json.dumps(metadata or {})
            ))
            conn.commit()
    
    def store_processed_memory(
        self, 
        memory: ProcessedMemory, 
        chat_id: str,
        namespace: str = "default"
    ) -> str:
        """Store a processed memory with entity indexing"""
        
        if not memory.should_store:
            logger.debug(f"Memory not stored: {memory.storage_reasoning}")
            return ""
        
        memory_id = str(uuid.uuid4())
        storage_location = self._determine_storage_location(memory)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                if storage_location == "short_term_memory":
                    self._store_short_term_memory(cursor, memory_id, memory, chat_id, namespace)
                elif storage_location == "long_term_memory":
                    self._store_long_term_memory(cursor, memory_id, memory, chat_id, namespace)
                elif storage_location == "rules_memory":
                    self._store_rules_memory(cursor, memory_id, memory, namespace)
                
                # Store entities for indexing
                self._store_entities(cursor, memory_id, memory, storage_location, namespace)
                
                conn.commit()
                logger.debug(f"Stored memory {memory_id} in {storage_location}")
                return memory_id
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to store memory: {e}")
                raise DatabaseError(f"Failed to store memory: {e}")
    
    def _store_short_term_memory(
        self, 
        cursor: sqlite3.Cursor, 
        memory_id: str, 
        memory: ProcessedMemory, 
        chat_id: str, 
        namespace: str
    ):
        """Store memory in short-term table"""
        expires_at = datetime.now() + timedelta(days=7)  # 7-day expiration
        
        cursor.execute("""
            INSERT INTO short_term_memory
            (memory_id, chat_id, processed_data, importance_score, category_primary, 
             retention_type, namespace, created_at, expires_at, access_count, 
             searchable_content, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, chat_id, memory.model_dump_json(), memory.importance.importance_score,
            memory.category.primary_category.value, memory.importance.retention_type.value,
            namespace, memory.timestamp, expires_at, 0,
            memory.searchable_content, memory.summary
        ))
    
    def _store_long_term_memory(
        self, 
        cursor: sqlite3.Cursor, 
        memory_id: str, 
        memory: ProcessedMemory, 
        chat_id: str, 
        namespace: str
    ):
        """Store memory in long-term table"""
        cursor.execute("""
            INSERT INTO long_term_memory
            (memory_id, original_chat_id, processed_data, importance_score, category_primary,
             retention_type, namespace, created_at, access_count, searchable_content, summary,
             novelty_score, relevance_score, actionability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, chat_id, memory.model_dump_json(), memory.importance.importance_score,
            memory.category.primary_category.value, memory.importance.retention_type.value,
            namespace, memory.timestamp, 0, memory.searchable_content, memory.summary,
            memory.importance.novelty_score, memory.importance.relevance_score,
            memory.importance.actionability_score
        ))
    
    def _store_rules_memory(
        self, 
        cursor: sqlite3.Cursor, 
        memory_id: str, 
        memory: ProcessedMemory, 
        namespace: str
    ):
        """Store rule-type memory in rules table"""
        cursor.execute("""
            INSERT INTO rules_memory
            (rule_id, rule_text, rule_type, priority, active, namespace, 
             created_at, updated_at, processed_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, memory.summary, "rule", 5, True, namespace,
            memory.timestamp, memory.timestamp, memory.model_dump_json()
        ))
    
    def _store_entities(
        self, 
        cursor: sqlite3.Cursor, 
        memory_id: str, 
        memory: ProcessedMemory, 
        memory_type: str, 
        namespace: str
    ):
        """Store extracted entities for indexing"""
        
        # Simple entities (lists)
        entity_mappings = [
            (memory.entities.people, "person"),
            (memory.entities.technologies, "technology"),
            (memory.entities.topics, "topic"),
            (memory.entities.skills, "skill"),
            (memory.entities.projects, "project"),
            (memory.entities.keywords, "keyword")
        ]
        
        for entity_list, entity_type in entity_mappings:
            for entity_value in entity_list:
                entity_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO memory_entities
                    (entity_id, memory_id, memory_type, entity_type, entity_value,
                     relevance_score, namespace, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id, memory_id, memory_type.replace("_memory", ""), entity_type,
                    entity_value, 0.8, namespace, datetime.now()
                ))
        
        # Structured entities (with metadata)
        for structured_entity in memory.entities.structured_entities:
            entity_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO memory_entities
                (entity_id, memory_id, memory_type, entity_type, entity_value,
                 relevance_score, entity_context, namespace, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id, memory_id, memory_type.replace("_memory", ""), 
                structured_entity.entity_type.value, structured_entity.value,
                structured_entity.relevance_score, structured_entity.context,
                namespace, datetime.now()
            ))
    
    def search_memories(
        self,
        query: str,
        namespace: str = "default",
        category_filter: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Advanced memory search with FTS and entity matching"""
        results = []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Try FTS search first if available
            try:
                fts_query = f'"{query}"' if query else "*"
                cursor.execute("""
                    SELECT 
                        fts.memory_id, fts.memory_type, fts.category_primary,
                        CASE 
                            WHEN fts.memory_type = 'short_term' THEN st.processed_data
                            WHEN fts.memory_type = 'long_term' THEN lt.processed_data
                        END as processed_data,
                        CASE 
                            WHEN fts.memory_type = 'short_term' THEN st.importance_score
                            WHEN fts.memory_type = 'long_term' THEN lt.importance_score
                        END as importance_score,
                        CASE 
                            WHEN fts.memory_type = 'short_term' THEN st.created_at
                            WHEN fts.memory_type = 'long_term' THEN lt.created_at
                        END as created_at,
                        rank
                    FROM memory_search_fts fts
                    LEFT JOIN short_term_memory st ON fts.memory_id = st.memory_id AND fts.memory_type = 'short_term'
                    LEFT JOIN long_term_memory lt ON fts.memory_id = lt.memory_id AND fts.memory_type = 'long_term'
                    WHERE memory_search_fts MATCH ? AND namespace = ?
                    ORDER BY rank, importance_score DESC
                    LIMIT ?
                """, (fts_query, namespace, limit))
                
                results.extend([dict(row) for row in cursor.fetchall()])
                
            except sqlite3.OperationalError:
                # FTS not available, fall back to LIKE search
                logger.debug("FTS not available, using LIKE search")
                
                # Search short-term memory
                cursor.execute("""
                    SELECT *, 'short_term' as memory_type FROM short_term_memory
                    WHERE namespace = ? AND (searchable_content LIKE ? OR summary LIKE ?)
                    AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY importance_score DESC, created_at DESC
                    LIMIT ?
                """, (namespace, f"%{query}%", f"%{query}%", datetime.now(), limit))
                
                results.extend([dict(row) for row in cursor.fetchall()])
                
                # Search long-term memory
                if len(results) < limit:
                    cursor.execute("""
                        SELECT *, 'long_term' as memory_type FROM long_term_memory
                        WHERE namespace = ? AND (searchable_content LIKE ? OR summary LIKE ?)
                        ORDER BY importance_score DESC, access_count DESC, created_at DESC
                        LIMIT ?
                    """, (namespace, f"%{query}%", f"%{query}%", limit - len(results)))
                    
                    results.extend([dict(row) for row in cursor.fetchall()])
            
            # Entity-based search for additional results
            if len(results) < limit and query:
                entity_results = self._search_by_entities(cursor, query, namespace, limit - len(results))
                
                # Add unique results
                existing_ids = {r.get('memory_id') for r in results}
                for result in entity_results:
                    if result.get('memory_id') not in existing_ids:
                        results.append(result)
        
        # Apply category filter if specified
        if category_filter:
            results = [r for r in results if r.get('category_primary') in category_filter]
        
        # Sort by relevance
        results.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
        return results[:limit]
    
    def _search_by_entities(
        self, 
        cursor: sqlite3.Cursor, 
        query: str, 
        namespace: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search memories by entity matching"""
        cursor.execute("""
            SELECT 
                e.memory_id, e.memory_type, e.relevance_score,
                CASE 
                    WHEN e.memory_type = 'short_term' THEN st.processed_data
                    WHEN e.memory_type = 'long_term' THEN lt.processed_data
                END as processed_data,
                CASE 
                    WHEN e.memory_type = 'short_term' THEN st.importance_score
                    WHEN e.memory_type = 'long_term' THEN lt.importance_score
                END as importance_score,
                CASE 
                    WHEN e.memory_type = 'short_term' THEN st.category_primary
                    WHEN e.memory_type = 'long_term' THEN lt.category_primary
                END as category_primary,
                CASE 
                    WHEN e.memory_type = 'short_term' THEN st.created_at
                    WHEN e.memory_type = 'long_term' THEN lt.created_at
                END as created_at
            FROM memory_entities e
            LEFT JOIN short_term_memory st ON e.memory_id = st.memory_id AND e.memory_type = 'short_term'
            LEFT JOIN long_term_memory lt ON e.memory_id = lt.memory_id AND e.memory_type = 'long_term'
            WHERE e.namespace = ? AND e.entity_value LIKE ?
            ORDER BY e.relevance_score DESC, importance_score DESC
            LIMIT ?
        """, (namespace, f"%{query}%", limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _determine_storage_location(self, memory: ProcessedMemory) -> str:
        """Determine where to store the memory based on its properties"""
        if memory.category.primary_category == MemoryCategoryType.rule:
            return "rules_memory"
        elif memory.importance.retention_type in [RetentionType.long_term, RetentionType.permanent]:
            return "long_term_memory"
        else:
            return "short_term_memory"
    
    def get_memory_stats(self, namespace: str = "default") -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM chat_history WHERE namespace = ?", (namespace,))
            stats['chat_history_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM short_term_memory WHERE namespace = ?", (namespace,))
            stats['short_term_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM long_term_memory WHERE namespace = ?", (namespace,))
            stats['long_term_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM rules_memory WHERE namespace = ?", (namespace,))
            stats['rules_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memory_entities WHERE namespace = ?", (namespace,))
            stats['total_entities'] = cursor.fetchone()[0]
            
            # Category breakdown
            cursor.execute("""
                SELECT category_primary, COUNT(*) as count
                FROM (
                    SELECT category_primary FROM short_term_memory WHERE namespace = ?
                    UNION ALL
                    SELECT category_primary FROM long_term_memory WHERE namespace = ?
                ) 
                GROUP BY category_primary
            """, (namespace, namespace))
            
            stats['memories_by_category'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average importance
            cursor.execute("""
                SELECT AVG(importance_score) FROM (
                    SELECT importance_score FROM short_term_memory WHERE namespace = ?
                    UNION ALL
                    SELECT importance_score FROM long_term_memory WHERE namespace = ?
                )
            """, (namespace, namespace))
            
            avg_importance = cursor.fetchone()[0]
            stats['average_importance'] = avg_importance if avg_importance else 0.0
            
            return stats
    
    def clear_memory(self, namespace: str = "default", memory_type: Optional[str] = None):
        """Clear memory data with entity cleanup"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if memory_type == "short_term":
                cursor.execute("DELETE FROM memory_entities WHERE namespace = ? AND memory_type = 'short_term'", (namespace,))
                cursor.execute("DELETE FROM short_term_memory WHERE namespace = ?", (namespace,))
            elif memory_type == "long_term":
                cursor.execute("DELETE FROM memory_entities WHERE namespace = ? AND memory_type = 'long_term'", (namespace,))
                cursor.execute("DELETE FROM long_term_memory WHERE namespace = ?", (namespace,))
            elif memory_type == "chat_history":
                cursor.execute("DELETE FROM chat_history WHERE namespace = ?", (namespace,))
            else:  # Clear all
                cursor.execute("DELETE FROM memory_entities WHERE namespace = ?", (namespace,))
                cursor.execute("DELETE FROM short_term_memory WHERE namespace = ?", (namespace,))
                cursor.execute("DELETE FROM long_term_memory WHERE namespace = ?", (namespace,))
                cursor.execute("DELETE FROM rules_memory WHERE namespace = ?", (namespace,))
                cursor.execute("DELETE FROM chat_history WHERE namespace = ?", (namespace,))
            
            conn.commit()

