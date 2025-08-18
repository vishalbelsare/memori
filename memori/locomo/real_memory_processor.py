"""
Real Memory Processor for LOCOMO Benchmark

Uses Memori's actual MemoryAgent with OpenAI Structured Outputs to process LOCOMO conversations.
This replaces rule-based processing with real AI-powered memory extraction and categorization.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger

from ..agents.memory_agent import MemoryAgent
from ..core.database import DatabaseManager
from ..utils.pydantic_models import ProcessedMemory, RetentionType
from .data_models import LocomoConversation, LocomoDialogueTurn, LocomoSession


class RealMemoryProcessor:
    """
    Processes LOCOMO conversations using Memori's real MemoryAgent with OpenAI Structured Outputs.
    This provides authentic memory processing for accurate benchmark results.
    """
    
    def __init__(self, database_manager: DatabaseManager, memory_agent: MemoryAgent, 
                 namespace: str = "locomo_benchmark"):
        """
        Initialize the real memory processor
        
        Args:
            database_manager: Memori database manager instance
            memory_agent: Real MemoryAgent with OpenAI integration
            namespace: Namespace for benchmark data isolation
        """
        self.db_manager = database_manager
        self.memory_agent = memory_agent
        self.namespace = namespace
        
        # Initialize database schema if needed
        try:
            self.db_manager.initialize_schema()
        except Exception as e:
            logger.warning(f"Failed to initialize schema: {e}")
    
    def store_chat_message(self, turn: LocomoDialogueTurn, session_id: str, model: str = "locomo_real") -> str:
        """
        Store a single chat message in chat_history table
        
        Args:
            turn: LOCOMO dialogue turn
            session_id: Session identifier
            model: Model name for tracking
            
        Returns:
            Chat ID for the stored message
        """
        chat_id = str(uuid.uuid4())
        
        # Store as user input (since LOCOMO doesn't distinguish AI responses)
        user_input = f"[{turn.speaker}]: {turn.text}"
        ai_output = ""  # No AI output in LOCOMO data
        
        try:
            with self.db_manager._get_connection() as conn:
                conn.execute("""
                    INSERT INTO chat_history 
                    (chat_id, user_input, ai_output, model, timestamp, session_id, namespace, tokens_used, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chat_id,
                    user_input,
                    ai_output,
                    model,
                    datetime.now(),
                    session_id,
                    self.namespace,
                    len(turn.text.split()) * 1.3,  # Rough token estimate
                    f'{{"dia_id": "{turn.dia_id}", "speaker": "{turn.speaker}"}}'
                ))
                
        except Exception as e:
            logger.error(f"Failed to store chat message: {e}")
            raise
        
        return chat_id
    
    def store_processed_memory(self, memory: ProcessedMemory, chat_id: Optional[str] = None) -> str:
        """
        Store a ProcessedMemory object in the appropriate memory table
        
        Args:
            memory: ProcessedMemory object to store
            chat_id: Associated chat ID (optional)
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        
        # Determine target table based on retention type
        if memory.importance.retention_type == RetentionType.short_term:
            table_name = "short_term_memory"
            expires_at = datetime.now() + timedelta(days=7)
        else:
            table_name = "long_term_memory"
            expires_at = None
        
        # Serialize the full ProcessedMemory object
        processed_data = memory.model_dump_json()
        
        try:
            # Ensure we have a proper timestamp
            created_timestamp = memory.timestamp if hasattr(memory, 'timestamp') and memory.timestamp else datetime.now()
            
            with self.db_manager._get_connection() as conn:
                if table_name == "short_term_memory":
                    conn.execute("""
                        INSERT INTO short_term_memory 
                        (memory_id, chat_id, processed_data, importance_score, category_primary, 
                         retention_type, namespace, created_at, expires_at, searchable_content, summary)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        memory_id,
                        chat_id,
                        processed_data,
                        memory.importance.importance_score,
                        memory.category.primary_category.value,
                        memory.importance.retention_type.value,
                        self.namespace,
                        created_timestamp,
                        expires_at,
                        memory.searchable_content,
                        memory.summary
                    ))
                else:
                    conn.execute("""
                        INSERT INTO long_term_memory 
                        (memory_id, original_chat_id, processed_data, importance_score, category_primary,
                         retention_type, namespace, created_at, searchable_content, summary,
                         novelty_score, relevance_score, actionability_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        memory_id,
                        chat_id,
                        processed_data,
                        memory.importance.importance_score,
                        memory.category.primary_category.value,
                        memory.importance.retention_type.value,
                        self.namespace,
                        created_timestamp,
                        memory.searchable_content,
                        memory.summary,
                        memory.importance.novelty_score,
                        memory.importance.relevance_score,
                        memory.importance.actionability_score
                    ))
                
                # Store entities
                self._store_memory_entities(conn, memory_id, memory, table_name)
                
        except Exception as e:
            logger.error(f"Failed to store processed memory: {e}")
            raise
        
        return memory_id
    
    def _store_memory_entities(self, conn, memory_id: str, memory: ProcessedMemory, memory_type: str):
        """Store entities associated with a memory"""
        
        entities_to_store = []
        
        # Add people entities
        for person in memory.entities.people:
            entities_to_store.append(("person", person, 0.8))
        
        # Add technology entities
        for tech in memory.entities.technologies:
            entities_to_store.append(("technology", tech, 0.7))
        
        # Add topic entities
        for topic in memory.entities.topics:
            entities_to_store.append(("topic", topic, 0.6))
        
        # Add skill entities
        for skill in memory.entities.skills:
            entities_to_store.append(("skill", skill, 0.7))
        
        # Add project entities  
        for project in memory.entities.projects:
            entities_to_store.append(("project", project, 0.6))
        
        # Add keyword entities
        for keyword in memory.entities.keywords:
            entities_to_store.append(("keyword", keyword, 0.5))
        
        # Store structured entities
        for entity in memory.entities.structured_entities:
            entities_to_store.append((
                entity.entity_type.value,
                entity.value,
                entity.relevance_score
            ))
        
        # Insert entities into database
        for entity_type, entity_value, relevance_score in entities_to_store:
            entity_id = str(uuid.uuid4())
            
            conn.execute("""
                INSERT INTO memory_entities
                (entity_id, memory_id, memory_type, entity_type, entity_value, 
                 relevance_score, namespace, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                memory_id,
                memory_type.replace("_memory", "_term"),  # Convert table name to type
                entity_type,
                entity_value,
                relevance_score,
                self.namespace,
                datetime.now()
            ))
    
    def process_conversation_chunk_with_ai(self, turns: List[LocomoDialogueTurn], 
                                          session_id: str, conversation_id: str) -> Optional[ProcessedMemory]:
        """
        Process a chunk of conversation turns using real MemoryAgent with OpenAI
        
        Args:
            turns: List of dialogue turns to process
            session_id: Session identifier
            conversation_id: Conversation identifier
            
        Returns:
            ProcessedMemory object if successful, None if failed
        """
        if not turns:
            return None
        
        # Create conversation text for the MemoryAgent
        conversation_text = []
        for turn in turns:
            conversation_text.append(f"{turn.speaker}: {turn.text}")
        
        combined_conversation = "\n".join(conversation_text)
        
        # Add context for the memory agent
        context = {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "turn_count": len(turns),
            "speakers": list(set(turn.speaker for turn in turns)),
            "source": "locomo_benchmark"
        }
        
        try:
            logger.debug(f"Processing {len(turns)} turns with real MemoryAgent...")
            
            # Generate a chat ID for this chunk
            chat_id = f"{conversation_id}_{session_id}_chunk_{len(turns)}"
            
            # Use real MemoryAgent to process the conversation
            # For LOCOMO, we treat the combined conversation as user input with no AI output
            processed_memory = self.memory_agent.process_conversation_sync(
                chat_id=chat_id,
                user_input=combined_conversation,
                ai_output="",  # LOCOMO doesn't have AI responses
                context=None,  # We'll add context through metadata instead
                mem_prompt=f"Process this LOCOMO benchmark conversation between {' and '.join(set(turn.speaker for turn in turns))}",
                filters=None
            )
            
            if processed_memory:
                # Add processing metadata
                processing_metadata = processed_memory.processing_metadata or {}
                processing_metadata.update({
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "turn_count": str(len(turns)),
                    "speakers": ", ".join(set(turn.speaker for turn in turns)),
                    "source": "locomo_benchmark_real_ai",
                    "dialogue_ids": [turn.dia_id for turn in turns]
                })
                
                # Update the processed memory with metadata
                processed_memory.processing_metadata = processing_metadata
                
                logger.debug(f"Successfully processed chunk: {processed_memory.category.primary_category.value} "
                           f"(importance: {processed_memory.importance.importance_score:.2f})")
                return processed_memory
            else:
                logger.warning("MemoryAgent returned None for conversation chunk")
                return None
                
        except Exception as e:
            logger.error(f"Real MemoryAgent processing failed: {e}")
            return None
    
    def process_session_with_real_ai(self, session: LocomoSession, conversation_id: str, 
                                   chunk_size: int = 5) -> Dict[str, List[str]]:
        """
        Process a session using real MemoryAgent with AI processing
        
        Args:
            session: LOCOMO session to process
            conversation_id: Parent conversation identifier
            chunk_size: Number of turns to process together
            
        Returns:
            Dictionary with chat_ids and memory_ids for tracking
        """
        
        session_id = f"{conversation_id}_{session.session_id}"
        chat_ids = []
        memory_ids = []
        
        logger.info(f"Processing session {session.session_id} with {len(session.turns)} turns using real AI")
        
        # Store individual chat messages
        for turn in session.turns:
            chat_id = self.store_chat_message(turn, session_id)
            chat_ids.append(chat_id)
        
        # Process conversation chunks with real AI
        for i in range(0, len(session.turns), chunk_size):
            chunk_turns = session.turns[i:i+chunk_size]
            
            try:
                # Process chunk with real MemoryAgent
                memory = self.process_conversation_chunk_with_ai(
                    chunk_turns, session.session_id, conversation_id
                )
                
                # Store memory if successfully processed and should be stored
                if memory and memory.should_store:
                    memory_id = self.store_processed_memory(memory, chat_ids[i] if chat_ids else None)
                    memory_ids.append(memory_id)
                elif memory:
                    logger.debug(f"Memory processed but not stored (should_store=False)")
                    
            except Exception as e:
                logger.warning(f"Failed to process chunk {i}-{i+len(chunk_turns)} with real AI: {e}")
                continue
        
        return {
            "chat_ids": chat_ids,
            "memory_ids": memory_ids,
            "session_id": session_id
        }
    
    def process_full_conversation_with_real_ai(self, conversation: LocomoConversation, 
                                             conversation_id: Optional[str] = None) -> Dict[str, any]:
        """
        Process a complete LOCOMO conversation using real MemoryAgent
        
        Args:
            conversation: LOCOMO conversation to process
            conversation_id: Optional conversation identifier
            
        Returns:
            Processing results and statistics
        """
        
        if conversation_id is None:
            conversation_id = f"locomo_real_{conversation.speaker_a}_{conversation.speaker_b}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Processing conversation with REAL AI: {conversation_id}")
        logger.info(f"Speakers: {conversation.speaker_a} & {conversation.speaker_b}")
        logger.info(f"Sessions: {len(conversation.sessions)}, Total turns: {conversation.total_turns}")
        
        results = {
            "conversation_id": conversation_id,
            "speakers": [conversation.speaker_a, conversation.speaker_b],
            "total_sessions": len(conversation.sessions),
            "total_turns": conversation.total_turns,
            "processing_start": datetime.now(),
            "session_results": [],
            "total_chat_ids": [],
            "total_memory_ids": [],
            "errors": [],
            "processing_type": "real_ai"
        }
        
        # Process each session with real AI
        for session in conversation.sessions:
            try:
                session_result = self.process_session_with_real_ai(session, conversation_id)
                results["session_results"].append(session_result)
                results["total_chat_ids"].extend(session_result["chat_ids"])
                results["total_memory_ids"].extend(session_result["memory_ids"])
                
            except Exception as e:
                error_msg = f"Failed to process session {session.session_id} with real AI: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                continue
        
        results["processing_end"] = datetime.now()
        results["processing_duration"] = (results["processing_end"] - results["processing_start"]).total_seconds()
        results["total_memories_stored"] = len(results["total_memory_ids"])
        results["total_chat_messages"] = len(results["total_chat_ids"])
        
        logger.info(f"REAL AI conversation processing complete:")
        logger.info(f"  - Total memories stored: {results['total_memories_stored']}")
        logger.info(f"  - Total chat messages: {results['total_chat_messages']}")
        logger.info(f"  - Processing time: {results['processing_duration']:.2f}s")
        logger.info(f"  - Errors: {len(results['errors'])}")
        
        return results
    
    def clean_benchmark_data(self):
        """Clean all benchmark data from the database"""
        
        logger.info(f"Cleaning real AI benchmark data for namespace: {self.namespace}")
        
        try:
            with self.db_manager._get_connection() as conn:
                # Delete from all tables for this namespace
                tables = ['chat_history', 'short_term_memory', 'long_term_memory', 'memory_entities']
                
                for table in tables:
                    result = conn.execute(f"DELETE FROM {table} WHERE namespace = ?", (self.namespace,))
                    logger.info(f"Deleted {result.rowcount} rows from {table}")
                
                # Clean FTS index
                conn.execute("DELETE FROM memory_search_fts WHERE namespace = ?", (self.namespace,))
                
        except Exception as e:
            logger.error(f"Failed to clean real AI benchmark data: {e}")
            raise
    
    def get_stored_memories_count(self) -> Dict[str, int]:
        """Get count of stored memories by type"""
        
        try:
            with self.db_manager._get_connection() as conn:
                # Count short-term memories
                short_term_count = conn.execute(
                    "SELECT COUNT(*) FROM short_term_memory WHERE namespace = ?", 
                    (self.namespace,)
                ).fetchone()[0]
                
                # Count long-term memories
                long_term_count = conn.execute(
                    "SELECT COUNT(*) FROM long_term_memory WHERE namespace = ?",
                    (self.namespace,)
                ).fetchone()[0]
                
                # Count chat messages
                chat_count = conn.execute(
                    "SELECT COUNT(*) FROM chat_history WHERE namespace = ?",
                    (self.namespace,)
                ).fetchone()[0]
                
                # Count entities
                entities_count = conn.execute(
                    "SELECT COUNT(*) FROM memory_entities WHERE namespace = ?",
                    (self.namespace,)
                ).fetchone()[0]
                
                return {
                    "short_term_memories": short_term_count,
                    "long_term_memories": long_term_count,
                    "total_memories": short_term_count + long_term_count,
                    "chat_messages": chat_count,
                    "entities": entities_count
                }
                
        except Exception as e:
            logger.error(f"Failed to get memory counts: {e}")
            return {}


if __name__ == "__main__":
    # Test the real memory processor
    import tempfile
    from pathlib import Path
    
    from .data_loader import load_locomo_dataset
    
    try:
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        db_manager = DatabaseManager(f"sqlite:///{temp_db.name}")
        memory_agent = MemoryAgent(api_key=None)  # Uses environment variable
        processor = RealMemoryProcessor(db_manager, memory_agent, namespace="test_real_ai")
        
        # Load test dataset
        dataset = load_locomo_dataset()
        
        if dataset.conversations:
            # Process first conversation with real AI
            conversation = dataset.conversations[0]
            
            logger.info("Testing REAL AI memory processing...")
            results = processor.process_full_conversation_with_real_ai(conversation)
            
            # Check results
            memory_counts = processor.get_stored_memories_count()
            
            print(f"REAL AI Processing Results:")
            print(f"  Conversation: {results['conversation_id']}")
            print(f"  Sessions processed: {len(results['session_results'])}")
            print(f"  Total turns: {results['total_turns']}")
            print(f"  Memories stored: {results['total_memories_stored']}")
            print(f"  Processing time: {results['processing_duration']:.2f}s")
            print(f"  Processing type: {results['processing_type']}")
            print(f"\nDatabase Counts:")
            print(f"  Short-term memories: {memory_counts['short_term_memories']}")
            print(f"  Long-term memories: {memory_counts['long_term_memories']}")
            print(f"  Chat messages: {memory_counts['chat_messages']}")
            print(f"  Entities: {memory_counts['entities']}")
            
        # Clean up
        Path(temp_db.name).unlink()
        
    except Exception as e:
        logger.error(f"Real AI memory processor test failed: {e}")
        raise