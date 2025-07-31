"""
Main Memori class - The primary interface for memory functionality
"""

import logging
import sqlite3
from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid
from datetime import datetime

from ..utils.enums import MemoryCategory, MemoryType
from ..utils.exceptions import MemoriError, DatabaseError
from .database import DatabaseManager
from .agent import MemoryAgent

logger = logging.getLogger(__name__)

class Memori:
    """
    The main Memori memory layer for AI agents.
    
    Provides persistent memory storage, categorization, and retrieval
    for AI conversations and agent interactions.
    """
    
    def __init__(
        self,
        database_connect: str = "sqlite:///memori.db",
        template: str = "basic",
        mem_prompt: Optional[str] = None,
        conscious_ingest: bool = True,
        namespace: Optional[str] = None,
        shared_memory: bool = False,
        custom_categories: Optional[List[str]] = None,
        memory_filters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Memori memory system.
        
        Args:
            database_connect: Database connection string
            template: Memory template to use ('basic', 'advanced', 'research')
            mem_prompt: Optional prompt to guide memory recording
            conscious_ingest: Enable intelligent memory filtering
            namespace: Optional namespace for memory isolation
            shared_memory: Enable shared memory across agents
            custom_categories: Custom memory categories
            memory_filters: Filters for memory ingestion
        """
        self.database_connect = database_connect
        self.template = template
        self.mem_prompt = mem_prompt
        self.conscious_ingest = conscious_ingest
        self.namespace = namespace or "default"
        self.shared_memory = shared_memory
        self.custom_categories = custom_categories or []
        self.memory_filters = memory_filters or {}
        
        # Initialize components
        self.db_manager = DatabaseManager(database_connect, template)
        self.memory_agent = MemoryAgent(
            conscious_ingest=conscious_ingest,
            mem_prompt=mem_prompt,
            custom_categories=custom_categories
        )
        
        # State tracking
        self._enabled = False
        self._session_id = str(uuid.uuid4())
        
        # Initialize database
        self._setup_database()
        
        logger.info(f"Memori initialized with template: {template}, namespace: {namespace}")
    
    def _setup_database(self):
        """Setup database tables based on template"""
        try:
            self.db_manager.initialize_schema()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            raise DatabaseError(f"Failed to setup database: {e}")
    
    def enable(self):
        """
        Enable memory recording (similar to loguru.enable())
        
        This activates the memory system to start recording conversations
        """
        if self._enabled:
            logger.warning("Memori is already enabled")
            return
            
        self._enabled = True
        self._session_id = str(uuid.uuid4())
        
        # Setup conversation hooks (placeholder for now)
        self._setup_conversation_hooks()
        
        logger.info(f"Memori enabled for session: {self._session_id}")
    
    def disable(self):
        """Disable memory recording"""
        self._enabled = False
        logger.info("Memori disabled")
    
    def _setup_conversation_hooks(self):
        """Setup hooks to capture LLM conversations"""
        # This will be implemented to intercept LLM calls
        # For now, it's a placeholder for manual recording
        pass
    
    def record_conversation(
        self, 
        user_input: str, 
        ai_output: str, 
        model: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Manually record a conversation
        
        Args:
            user_input: The user's input message
            ai_output: The AI's response
            model: Model used for the response
            metadata: Additional metadata
            
        Returns:
            chat_id: Unique identifier for this conversation
        """
        if not self._enabled:
            raise MemoriError("Memori is not enabled. Call enable() first.")
        
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        try:
            # Store in chat history
            self.db_manager.store_chat_history(
                chat_id=chat_id,
                user_input=user_input,
                ai_output=ai_output,
                model=model,
                timestamp=timestamp,
                session_id=self._session_id,
                namespace=self.namespace,
                metadata=metadata or {}
            )
            
            # Process for memory categorization
            if self.conscious_ingest:
                self._process_memory_ingestion(chat_id, user_input, ai_output)
            
            logger.debug(f"Conversation recorded: {chat_id}")
            return chat_id
            
        except Exception as e:
            raise MemoriError(f"Failed to record conversation: {e}")
    
    def _process_memory_ingestion(self, chat_id: str, user_input: str, ai_output: str):
        """Process conversation for memory categorization"""
        try:
            # Use memory agent to categorize and process
            memory_items = self.memory_agent.process_conversation(
                chat_id=chat_id,
                user_input=user_input,
                ai_output=ai_output,
                filters=self.memory_filters
            )
            
            # Store categorized memories
            for item in memory_items:
                if item.category != MemoryCategory.DISCARD_TRIVIAL:
                    self.db_manager.store_memory_item(item, self.namespace)
                    
        except Exception as e:
            logger.error(f"Memory ingestion failed for {chat_id}: {e}")
    
    def retrieve_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query
        
        Args:
            query: The query to find context for
            limit: Maximum number of context items to return
            
        Returns:
            List of relevant memory items
        """
        try:
            # Use memory agent for intelligent retrieval
            relevant_memories = self.memory_agent.retrieve_relevant_context(
                query=query,
                namespace=self.namespace,
                limit=limit
            )
            
            # Get detailed memory items from database
            context_items = []
            for memory_id in relevant_memories:
                item = self.db_manager.get_memory_item(memory_id, self.namespace)
                if item:
                    context_items.append(item)
            
            logger.debug(f"Retrieved {len(context_items)} context items for query")
            return context_items
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            return self.db_manager.get_chat_history(
                namespace=self.namespace,
                session_id=self._session_id if not self.shared_memory else None,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def clear_memory(self, memory_type: Optional[str] = None):
        """
        Clear memory data
        
        Args:
            memory_type: Type of memory to clear ('short_term', 'long_term', 'all')
        """
        try:
            self.db_manager.clear_memory(self.namespace, memory_type)
            logger.info(f"Cleared {memory_type or 'all'} memory for namespace: {self.namespace}")
        except Exception as e:
            raise MemoriError(f"Failed to clear memory: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            return self.db_manager.get_memory_stats(self.namespace)
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    @property
    def is_enabled(self) -> bool:
        """Check if memory recording is enabled"""
        return self._enabled
    
    @property
    def session_id(self) -> str:
        """Get current session ID"""
        return self._session_id
