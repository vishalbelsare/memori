"""
Conscious Agent for User Context Management

This agent copies conscious-info labeled memories from long-term memory
directly to short-term memory for immediate context availability.
"""

from datetime import datetime
from typing import List

from loguru import logger


class ConsciouscAgent:
    """
    Agent that copies conscious-info labeled memories from long-term memory
    directly to short-term memory for immediate context availability.

    Runs once at program startup when conscious_ingest=True.
    """

    def __init__(self):
        """Initialize the conscious agent"""
        self.context_initialized = False

    async def run_conscious_ingest(
        self, db_manager, namespace: str = "default"
    ) -> bool:
        """
        Run conscious context ingestion once at program startup

        Copies all conscious-info labeled memories from long-term memory
        directly to short-term memory as permanent context

        Args:
            db_manager: Database manager instance
            namespace: Memory namespace

        Returns:
            True if memories were copied, False otherwise
        """
        try:
            # Get all conscious-info labeled memories
            conscious_memories = await self._get_conscious_memories(
                db_manager, namespace
            )

            if not conscious_memories:
                logger.info("ConsciouscAgent: No conscious-info memories found")
                return False

            # Copy each conscious-info memory directly to short-term memory
            copied_count = 0
            for memory_row in conscious_memories:
                success = await self._copy_memory_to_short_term(
                    db_manager, namespace, memory_row
                )
                if success:
                    copied_count += 1

            # Mark memories as processed
            memory_ids = [
                row[0] for row in conscious_memories
            ]  # memory_id is first column
            await self._mark_memories_processed(db_manager, memory_ids, namespace)

            self.context_initialized = True
            logger.info(
                f"ConsciouscAgent: Copied {copied_count} conscious-info memories to short-term memory"
            )

            return copied_count > 0

        except Exception as e:
            logger.error(f"ConsciouscAgent: Conscious ingest failed: {e}")
            return False

    async def check_for_context_updates(
        self, db_manager, namespace: str = "default"
    ) -> bool:
        """
        Check for new conscious-info memories and copy them to short-term memory

        Args:
            db_manager: Database manager instance
            namespace: Memory namespace

        Returns:
            True if new memories were copied, False otherwise
        """
        try:
            # Get unprocessed conscious memories
            new_memories = await self._get_unprocessed_conscious_memories(
                db_manager, namespace
            )

            if not new_memories:
                return False

            # Copy each new memory directly to short-term memory
            copied_count = 0
            for memory_row in new_memories:
                success = await self._copy_memory_to_short_term(
                    db_manager, namespace, memory_row
                )
                if success:
                    copied_count += 1

            # Mark new memories as processed
            memory_ids = [row[0] for row in new_memories]  # memory_id is first column
            await self._mark_memories_processed(db_manager, memory_ids, namespace)

            logger.info(
                f"ConsciouscAgent: Copied {copied_count} new conscious-info memories to short-term memory"
            )
            return copied_count > 0

        except Exception as e:
            logger.error(f"ConsciouscAgent: Context update failed: {e}")
            return False

    async def _get_conscious_memories(self, db_manager, namespace: str) -> List[tuple]:
        """Get all conscious-info labeled memories from long-term memory"""
        try:
            from sqlalchemy import text
            
            with db_manager._get_connection() as connection:
                cursor = connection.execute(
                    text("""SELECT memory_id, processed_data, summary, searchable_content, 
                              importance_score, created_at
                       FROM long_term_memory 
                       WHERE namespace = :namespace AND classification = 'conscious-info'
                       ORDER BY importance_score DESC, created_at DESC"""),
                    {"namespace": namespace},
                )
                return cursor.fetchall()

        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to get conscious memories: {e}")
            return []

    async def _get_unprocessed_conscious_memories(
        self, db_manager, namespace: str
    ) -> List[tuple]:
        """Get unprocessed conscious-info labeled memories from long-term memory"""
        try:
            from sqlalchemy import text
            
            with db_manager._get_connection() as connection:
                cursor = connection.execute(
                    text("""SELECT memory_id, processed_data, summary, searchable_content, 
                              importance_score, created_at
                       FROM long_term_memory 
                       WHERE namespace = :namespace AND classification = 'conscious-info' 
                       AND conscious_processed = 0
                       ORDER BY importance_score DESC, created_at DESC"""),
                    {"namespace": namespace},
                )
                return cursor.fetchall()

        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to get unprocessed memories: {e}")
            return []

    async def _copy_memory_to_short_term(
        self, db_manager, namespace: str, memory_row: tuple
    ) -> bool:
        """Copy a conscious memory directly to short-term memory"""
        try:
            (
                memory_id,
                processed_data,
                summary,
                searchable_content,
                importance_score,
                _,
            ) = memory_row

            # Create short-term memory ID
            short_term_id = f"conscious_{memory_id}_{int(datetime.now().timestamp())}"

            from sqlalchemy import text
            
            with db_manager._get_connection() as connection:
                # Insert directly into short-term memory with conscious_context category
                connection.execute(
                    text("""INSERT INTO short_term_memory (
                        memory_id, processed_data, importance_score, category_primary,
                        retention_type, namespace, created_at, expires_at, 
                        searchable_content, summary, is_permanent_context
                    ) VALUES (:memory_id, :processed_data, :importance_score, :category_primary,
                        :retention_type, :namespace, :created_at, :expires_at,
                        :searchable_content, :summary, :is_permanent_context)"""),
                    {
                        "memory_id": short_term_id,
                        "processed_data": processed_data,  # Copy exact processed_data from long-term memory
                        "importance_score": importance_score,
                        "category_primary": "conscious_context",  # Use conscious_context category
                        "retention_type": "permanent",
                        "namespace": namespace,
                        "created_at": datetime.now().isoformat(),
                        "expires_at": None,  # No expiration (permanent)
                        "searchable_content": searchable_content,  # Copy exact searchable_content
                        "summary": summary,  # Copy exact summary
                        "is_permanent_context": 1,  # is_permanent_context = True
                    },
                )
                connection.commit()

            logger.debug(
                f"ConsciouscAgent: Copied memory {memory_id} to short-term as {short_term_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"ConsciouscAgent: Failed to copy memory {memory_row[0]} to short-term: {e}"
            )
            return False

    async def _mark_memories_processed(
        self, db_manager, memory_ids: List[str], namespace: str
    ):
        """Mark memories as processed for conscious context"""
        try:
            from sqlalchemy import text
            
            with db_manager._get_connection() as connection:
                for memory_id in memory_ids:
                    connection.execute(
                        text("""UPDATE long_term_memory 
                           SET conscious_processed = 1
                           WHERE memory_id = :memory_id AND namespace = :namespace"""),
                        {"memory_id": memory_id, "namespace": namespace},
                    )
                connection.commit()

        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to mark memories processed: {e}")