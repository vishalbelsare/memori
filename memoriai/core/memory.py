"""
Main Memori class - The primary interface for memory functionality
"""

from loguru import logger
import sqlite3
from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid
from datetime import datetime

from ..utils.enums import MemoryCategory, MemoryType
from ..utils.exceptions import MemoriError, DatabaseError
from .database import DatabaseManager
from ..agents.memory_agent import MemoryAgent
from ..agents.retrieval_agent import RetrievalAgent
from ..integrations import (
    install_all_hooks, 
    uninstall_all_hooks, 
    register_memori_instance, 
    unregister_memori_instance,
    get_integration_stats
)

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
        memory_filters: Optional[Dict[str, Any]] = None,
        openai_api_key: Optional[str] = None
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
            openai_api_key: OpenAI API key for memory agent
        """
        self.database_connect = database_connect
        self.template = template
        self.mem_prompt = mem_prompt
        self.conscious_ingest = conscious_ingest
        self.namespace = namespace or "default"
        self.shared_memory = shared_memory
        self.custom_categories = custom_categories or []
        self.memory_filters = memory_filters or {}
        self.openai_api_key = openai_api_key
        
        # Initialize components
        self.db_manager = DatabaseManager(database_connect, template)
        
        # Initialize agents (only if conscious_ingest is enabled and we have an API key)
        self.memory_agent = None
        self.retrieval_agent = None
        
        if conscious_ingest:
            try:
                self.memory_agent = MemoryAgent(api_key=openai_api_key)
                self.retrieval_agent = RetrievalAgent(api_key=openai_api_key)
                logger.info("OpenAI-powered memory and retrieval agents initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI agents: {e}. Falling back to keyword-based processing.")
                # Fallback to the original simple memory agent
                from .agent import MemoryAgent as SimpleMemoryAgent
                self.memory_agent = SimpleMemoryAgent(
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
        
        This activates the memory system to start recording conversations automatically
        by installing hooks into popular LLM libraries.
        """
        if self._enabled:
            logger.warning("Memori is already enabled")
            return
            
        self._enabled = True
        self._session_id = str(uuid.uuid4())
        
        # Setup conversation hooks for auto-recording
        self._setup_conversation_hooks()
        
        logger.info(f"Memori enabled for session: {self._session_id}")
    
    def disable(self):
        """Disable memory recording and uninstall hooks"""
        if not self._enabled:
            return
            
        self._enabled = False
        
        # Unregister from integrations
        unregister_memori_instance(self)
        
        logger.info("Memori disabled")
    
    def _setup_conversation_hooks(self):
        """Setup hooks to capture LLM conversations automatically"""
        try:
            # Install hooks for all available LLM libraries
            install_all_hooks()
            
            # Register this instance with all integrations
            register_memori_instance(self)
            
            logger.info("Auto-recording hooks installed for LLM libraries")
            
        except Exception as e:
            logger.error(f"Failed to setup conversation hooks: {e}")
            raise MemoriError(f"Failed to enable auto-recording: {e}")
    
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
        if not self.memory_agent:
            logger.warning("Memory agent not available, skipping memory ingestion")
            return
            
        try:
            # Use memory agent to categorize and process
            memory_items = self.memory_agent.process_conversation(
                chat_id=chat_id,
                user_input=user_input,
                ai_output=ai_output,
                mem_prompt=self.mem_prompt,
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
            # Use retrieval agent for intelligent retrieval if available
            if self.retrieval_agent:
                context_items = self.retrieval_agent.execute_retrieval(
                    query=query,
                    db_manager=self.db_manager,
                    namespace=self.namespace,
                    limit=limit
                )
            else:
                # Fallback to simple database search
                context_items = self.db_manager.search_memories(
                    query=query,
                    namespace=self.namespace,
                    limit=limit
                )
            
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
    
    def get_integration_stats(self) -> List[Dict[str, Any]]:
        """Get statistics from all integrations"""
        try:
            return get_integration_stats()
        except Exception as e:
            logger.error(f"Failed to get integration stats: {e}")
            return []
