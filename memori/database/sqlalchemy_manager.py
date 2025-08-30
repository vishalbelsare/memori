"""
SQLAlchemy-based database manager for Memori v2.0
Replaces the existing database.py with cross-database compatibility
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ..utils.exceptions import DatabaseError
from ..utils.pydantic_models import (
    ProcessedLongTermMemory,
    ProcessedMemory,
    RetentionType,
)
from .models import Base, ChatHistory, ShortTermMemory, LongTermMemory, DatabaseManager as BaseDBManager
from .search_service import SearchService


class SQLAlchemyDatabaseManager:
    """SQLAlchemy-based database manager with cross-database support"""
    
    def __init__(self, database_connect: str, template: str = "basic"):
        self.database_connect = database_connect
        self.template = template
        
        # Parse connection string and create engine
        self.engine = self._create_engine(database_connect)
        self.database_type = self.engine.dialect.name
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize search service
        self._search_service = None
        
        logger.info(f"Initialized SQLAlchemy database manager for {self.database_type}")
    
    def _create_engine(self, database_connect: str):
        """Create SQLAlchemy engine with appropriate configuration"""
        try:
            # Parse connection string
            if database_connect.startswith("sqlite:"):
                # Ensure directory exists for SQLite
                if ":///" in database_connect:
                    db_path = database_connect.replace("sqlite:///", "")
                    db_dir = Path(db_path).parent
                    db_dir.mkdir(parents=True, exist_ok=True)
                
                # SQLite-specific configuration
                engine = create_engine(
                    database_connect,
                    json_serializer=json.dumps,
                    json_deserializer=json.loads,
                    echo=False,
                    # SQLite-specific options
                    connect_args={
                        "check_same_thread": False,  # Allow multiple threads
                    }
                )
                
            elif database_connect.startswith("mysql:") or database_connect.startswith("mysql+"):
                # MySQL-specific configuration
                engine = create_engine(
                    database_connect,
                    json_serializer=json.dumps,
                    json_deserializer=json.loads,
                    echo=False,
                    # MySQL-specific options
                    connect_args={
                        "charset": "utf8mb4",
                        "use_pure": True,
                    },
                    pool_pre_ping=True,  # Validate connections
                    pool_recycle=3600,   # Recycle connections every hour
                )
                
            elif database_connect.startswith("postgresql:") or database_connect.startswith("postgresql+"):
                # PostgreSQL-specific configuration
                engine = create_engine(
                    database_connect,
                    json_serializer=json.dumps,
                    json_deserializer=json.loads,
                    echo=False,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
                
            else:
                raise DatabaseError(f"Unsupported database type: {database_connect}")
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return engine
            
        except Exception as e:
            raise DatabaseError(f"Failed to create database engine: {e}")
    
    def initialize_schema(self):
        """Initialize database schema"""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Setup database-specific features
            self._setup_database_features()
            
            logger.info(f"Database schema initialized successfully for {self.database_type}")
            
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise DatabaseError(f"Failed to initialize schema: {e}")
    
    def _setup_database_features(self):
        """Setup database-specific features like full-text search"""
        try:
            with self.engine.connect() as conn:
                if self.database_type == 'sqlite':
                    self._setup_sqlite_fts(conn)
                elif self.database_type == 'mysql':
                    self._setup_mysql_fulltext(conn)
                elif self.database_type == 'postgresql':
                    self._setup_postgresql_fts(conn)
                
                conn.commit()
                
        except Exception as e:
            logger.warning(f"Failed to setup database-specific features: {e}")
    
    def _setup_sqlite_fts(self, conn):
        """Setup SQLite FTS5"""
        try:
            # Create FTS5 virtual table
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_search_fts USING fts5(
                    memory_id,
                    memory_type,
                    namespace,
                    searchable_content,
                    summary,
                    category_primary,
                    content='',
                    contentless_delete=1
                )
            """))
            
            # Create triggers
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS short_term_memory_fts_insert AFTER INSERT ON short_term_memory
                BEGIN
                    INSERT INTO memory_search_fts(memory_id, memory_type, namespace, searchable_content, summary, category_primary)
                    VALUES (NEW.memory_id, 'short_term', NEW.namespace, NEW.searchable_content, NEW.summary, NEW.category_primary);
                END
            """))
            
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS long_term_memory_fts_insert AFTER INSERT ON long_term_memory
                BEGIN
                    INSERT INTO memory_search_fts(memory_id, memory_type, namespace, searchable_content, summary, category_primary)
                    VALUES (NEW.memory_id, 'long_term', NEW.namespace, NEW.searchable_content, NEW.summary, NEW.category_primary);
                END
            """))
            
            logger.info("SQLite FTS5 setup completed")
            
        except Exception as e:
            logger.warning(f"SQLite FTS5 setup failed: {e}")
    
    def _setup_mysql_fulltext(self, conn):
        """Setup MySQL FULLTEXT indexes"""
        try:
            # Create FULLTEXT indexes
            conn.execute(text("ALTER TABLE short_term_memory ADD FULLTEXT INDEX ft_short_term_search (searchable_content, summary)"))
            conn.execute(text("ALTER TABLE long_term_memory ADD FULLTEXT INDEX ft_long_term_search (searchable_content, summary)"))
            
            logger.info("MySQL FULLTEXT indexes setup completed")
            
        except Exception as e:
            logger.warning(f"MySQL FULLTEXT setup failed (indexes may already exist): {e}")
    
    def _setup_postgresql_fts(self, conn):
        """Setup PostgreSQL full-text search"""
        try:
            # Add tsvector columns
            conn.execute(text("ALTER TABLE short_term_memory ADD COLUMN IF NOT EXISTS search_vector tsvector"))
            conn.execute(text("ALTER TABLE long_term_memory ADD COLUMN IF NOT EXISTS search_vector tsvector"))
            
            # Create GIN indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_short_term_search_vector ON short_term_memory USING GIN(search_vector)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_long_term_search_vector ON long_term_memory USING GIN(search_vector)"))
            
            # Create update functions and triggers
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_short_term_search_vector() RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector := to_tsvector('english', COALESCE(NEW.searchable_content, '') || ' ' || COALESCE(NEW.summary, ''));
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
            """))
            
            conn.execute(text("""
                DROP TRIGGER IF EXISTS update_short_term_search_vector_trigger ON short_term_memory;
                CREATE TRIGGER update_short_term_search_vector_trigger 
                BEFORE INSERT OR UPDATE ON short_term_memory 
                FOR EACH ROW EXECUTE FUNCTION update_short_term_search_vector();
            """))
            
            logger.info("PostgreSQL FTS setup completed")
            
        except Exception as e:
            logger.warning(f"PostgreSQL FTS setup failed: {e}")
    
    def _get_search_service(self) -> SearchService:
        """Get search service instance"""
        if not self._search_service:
            session = self.SessionLocal()
            self._search_service = SearchService(session, self.database_type)
        return self._search_service
    
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
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Store chat history"""
        with self.SessionLocal() as session:
            try:
                chat_history = ChatHistory(
                    chat_id=chat_id,
                    user_input=user_input,
                    ai_output=ai_output,
                    model=model,
                    timestamp=timestamp,
                    session_id=session_id,
                    namespace=namespace,
                    tokens_used=tokens_used,
                    metadata_json=metadata or {}
                )
                
                session.merge(chat_history)  # Use merge for INSERT OR REPLACE behavior
                session.commit()
                
            except SQLAlchemyError as e:
                session.rollback()
                raise DatabaseError(f"Failed to store chat history: {e}")
    
    def get_chat_history(
        self,
        namespace: str = "default",
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get chat history with optional session filtering"""
        with self.SessionLocal() as session:
            try:
                query = session.query(ChatHistory).filter(
                    ChatHistory.namespace == namespace
                )
                
                if session_id:
                    query = query.filter(ChatHistory.session_id == session_id)
                
                results = query.order_by(ChatHistory.timestamp.desc()).limit(limit).all()
                
                # Convert to dictionaries
                return [
                    {
                        'chat_id': result.chat_id,
                        'user_input': result.user_input,
                        'ai_output': result.ai_output,
                        'model': result.model,
                        'timestamp': result.timestamp,
                        'session_id': result.session_id,
                        'namespace': result.namespace,
                        'tokens_used': result.tokens_used,
                        'metadata': result.metadata_json or {}
                    }
                    for result in results
                ]
                
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to get chat history: {e}")
    
    def store_long_term_memory_enhanced(
        self, memory: ProcessedLongTermMemory, chat_id: str, namespace: str = "default"
    ) -> str:
        """Store a ProcessedLongTermMemory with enhanced schema"""
        memory_id = str(uuid.uuid4())
        
        with self.SessionLocal() as session:
            try:
                long_term_memory = LongTermMemory(
                    memory_id=memory_id,
                    original_chat_id=chat_id,
                    processed_data=memory.model_dump(mode="json"),
                    importance_score=memory.importance_score,
                    category_primary=memory.classification.value,
                    retention_type="long_term",
                    namespace=namespace,
                    created_at=datetime.now(),
                    searchable_content=memory.content,
                    summary=memory.summary,
                    novelty_score=0.5,
                    relevance_score=0.5,
                    actionability_score=0.5,
                    classification=memory.classification.value,
                    memory_importance=memory.importance.value,
                    topic=memory.topic,
                    entities_json=memory.entities,
                    keywords_json=memory.keywords,
                    is_user_context=memory.is_user_context,
                    is_preference=memory.is_preference,
                    is_skill_knowledge=memory.is_skill_knowledge,
                    is_current_project=memory.is_current_project,
                    promotion_eligible=memory.promotion_eligible,
                    duplicate_of=memory.duplicate_of,
                    supersedes_json=memory.supersedes,
                    related_memories_json=memory.related_memories,
                    confidence_score=memory.confidence_score,
                    extraction_timestamp=memory.extraction_timestamp,
                    classification_reason=memory.classification_reason,
                    processed_for_duplicates=False,
                    conscious_processed=False
                )
                
                session.add(long_term_memory)
                session.commit()
                
                logger.debug(f"Stored enhanced long-term memory {memory_id}")
                return memory_id
                
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to store enhanced long-term memory: {e}")
                raise DatabaseError(f"Failed to store enhanced long-term memory: {e}")
    
    def search_memories(
        self,
        query: str,
        namespace: str = "default",
        category_filter: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories using the cross-database search service"""
        try:
            search_service = self._get_search_service()
            return search_service.search_memories(query, namespace, category_filter, limit)
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise DatabaseError(f"Memory search failed: {e}")
    
    def get_memory_stats(self, namespace: str = "default") -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        with self.SessionLocal() as session:
            try:
                stats = {}
                
                # Basic counts
                stats["chat_history_count"] = session.query(ChatHistory).filter(
                    ChatHistory.namespace == namespace
                ).count()
                
                stats["short_term_count"] = session.query(ShortTermMemory).filter(
                    ShortTermMemory.namespace == namespace
                ).count()
                
                stats["long_term_count"] = session.query(LongTermMemory).filter(
                    LongTermMemory.namespace == namespace
                ).count()
                
                # Category breakdown
                categories = {}
                
                # Short-term categories
                short_categories = session.query(
                    ShortTermMemory.category_primary,
                    func.count(ShortTermMemory.memory_id).label('count')
                ).filter(ShortTermMemory.namespace == namespace).group_by(ShortTermMemory.category_primary).all()
                
                for cat, count in short_categories:
                    categories[cat] = categories.get(cat, 0) + count
                
                # Long-term categories
                long_categories = session.query(
                    LongTermMemory.category_primary,
                    func.count(LongTermMemory.memory_id).label('count')
                ).filter(LongTermMemory.namespace == namespace).group_by(LongTermMemory.category_primary).all()
                
                for cat, count in long_categories:
                    categories[cat] = categories.get(cat, 0) + count
                
                stats["memories_by_category"] = categories
                
                # Average importance
                short_avg = session.query(
                    func.avg(ShortTermMemory.importance_score)
                ).filter(ShortTermMemory.namespace == namespace).scalar() or 0
                
                long_avg = session.query(
                    func.avg(LongTermMemory.importance_score)
                ).filter(LongTermMemory.namespace == namespace).scalar() or 0
                
                total_memories = stats["short_term_count"] + stats["long_term_count"]
                if total_memories > 0:
                    # Weight averages by count
                    total_avg = (
                        (short_avg * stats["short_term_count"]) +
                        (long_avg * stats["long_term_count"])
                    ) / total_memories
                    stats["average_importance"] = float(total_avg) if total_avg else 0.0
                else:
                    stats["average_importance"] = 0.0
                
                # Database info
                stats["database_type"] = self.database_type
                stats["database_url"] = self.database_connect.split('@')[-1] if '@' in self.database_connect else self.database_connect
                
                return stats
                
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to get memory stats: {e}")
    
    def clear_memory(
        self, namespace: str = "default", memory_type: Optional[str] = None
    ):
        """Clear memory data"""
        with self.SessionLocal() as session:
            try:
                if memory_type == "short_term":
                    session.query(ShortTermMemory).filter(
                        ShortTermMemory.namespace == namespace
                    ).delete()
                elif memory_type == "long_term":
                    session.query(LongTermMemory).filter(
                        LongTermMemory.namespace == namespace
                    ).delete()
                elif memory_type == "chat_history":
                    session.query(ChatHistory).filter(
                        ChatHistory.namespace == namespace
                    ).delete()
                else:  # Clear all
                    session.query(ShortTermMemory).filter(
                        ShortTermMemory.namespace == namespace
                    ).delete()
                    session.query(LongTermMemory).filter(
                        LongTermMemory.namespace == namespace
                    ).delete()
                    session.query(ChatHistory).filter(
                        ChatHistory.namespace == namespace
                    ).delete()
                
                session.commit()
                
            except SQLAlchemyError as e:
                session.rollback()
                raise DatabaseError(f"Failed to clear memory: {e}")
    
    def close(self):
        """Close database connections"""
        if self._search_service and hasattr(self._search_service, 'session'):
            self._search_service.session.close()
        
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and capabilities"""
        return {
            'database_type': self.database_type,
            'database_url': self.database_connect.split('@')[-1] if '@' in self.database_connect else self.database_connect,
            'driver': self.engine.dialect.driver,
            'server_version': getattr(self.engine.dialect, 'server_version_info', None),
            'supports_fulltext': True,  # Assume true for SQLAlchemy managed connections
        }