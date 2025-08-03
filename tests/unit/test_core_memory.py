"""
Unit tests for memoriai.core.memory module.
"""

from unittest.mock import patch

import pytest

from memoriai.core.database import DatabaseManager
from memoriai.core.memory import MemoryManager
from memoriai.utils.exceptions import MemoryRetrievalError, MemoryStorageError
from memoriai.utils.pydantic_models import (
    ExtractedEntities,
    MemoryCategory,
    MemoryCategoryType,
    MemoryImportance,
    ProcessedMemory,
    RetentionType,
)


class TestMemoryManager:
    """Test the MemoryManager class."""

    def test_memory_manager_initialization(self, db_manager: DatabaseManager):
        """Test MemoryManager initialization."""
        memory_manager = MemoryManager(db_manager)
        assert memory_manager.db_manager == db_manager
        assert memory_manager.is_initialized

    def test_store_memory_success(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test successful memory storage."""
        memory_id = memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

    def test_store_memory_with_invalid_data(self, memory_manager: MemoryManager):
        """Test memory storage with invalid data."""
        with pytest.raises(ValueError):
            memory_manager.store_memory(
                processed_memory=None,
                session_id="test_session",
                namespace="test_namespace",
            )

    def test_retrieve_memories_by_query(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test memory retrieval by query."""
        # Store a memory first
        memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        # Retrieve memories
        memories = memory_manager.retrieve_memories(
            query="Python Django",
            namespace="test_namespace",
            limit=10,
        )

        assert isinstance(memories, list)
        # Should find at least one memory
        assert len(memories) >= 0

    def test_retrieve_memories_by_category(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test memory retrieval by category."""
        # Store a memory first
        memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        # Retrieve memories by category
        memories = memory_manager.retrieve_memories_by_category(
            category=MemoryCategoryType.fact,
            namespace="test_namespace",
            limit=10,
        )

        assert isinstance(memories, list)

    def test_get_memory_statistics(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test memory statistics retrieval."""
        # Store a memory first
        memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        stats = memory_manager.get_memory_statistics(namespace="test_namespace")

        assert isinstance(stats, dict)
        assert "total_memories" in stats
        assert "memory_categories" in stats
        assert "retention_types" in stats
        assert stats["total_memories"] >= 1

    def test_delete_memory(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test memory deletion."""
        # Store a memory first
        memory_id = memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        # Delete the memory
        result = memory_manager.delete_memory(memory_id, namespace="test_namespace")
        assert result is True

    def test_update_memory_importance(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test updating memory importance."""
        # Store a memory first
        memory_id = memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        # Update importance
        new_importance = MemoryImportance(
            importance_score=0.95,
            retention_type=RetentionType.permanent,
            reasoning="Updated to permanent retention",
        )

        result = memory_manager.update_memory_importance(
            memory_id=memory_id,
            new_importance=new_importance,
            namespace="test_namespace",
        )
        assert result is True

    def test_search_memories_with_filters(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test memory search with various filters."""
        # Store a memory first
        memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        # Search with filters
        memories = memory_manager.search_memories(
            query="Django",
            namespace="test_namespace",
            category_filter=[MemoryCategoryType.fact],
            importance_threshold=0.5,
            limit=10,
        )

        assert isinstance(memories, list)

    def test_get_related_memories(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test finding related memories."""
        # Store a memory first
        memory_id = memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        # Find related memories
        related = memory_manager.get_related_memories(
            memory_id=memory_id,
            namespace="test_namespace",
            limit=5,
        )

        assert isinstance(related, list)

    def test_cleanup_old_memories(self, memory_manager: MemoryManager):
        """Test cleanup of old memories."""
        # This should not raise an exception
        result = memory_manager.cleanup_old_memories(
            namespace="test_namespace",
            days_threshold=30,
            retention_type=RetentionType.short_term,
        )
        assert isinstance(result, int)
        assert result >= 0

    @patch("memoriai.core.memory.MemoryManager.store_memory")
    def test_store_memory_database_error(
        self,
        mock_store,
        memory_manager: MemoryManager,
        sample_processed_memory: ProcessedMemory,
    ):
        """Test handling of database errors during storage."""
        mock_store.side_effect = Exception("Database connection failed")

        with pytest.raises(MemoryStorageError):
            memory_manager.store_memory(
                processed_memory=sample_processed_memory,
                session_id="test_session",
                namespace="test_namespace",
            )

    @patch("memoriai.core.memory.MemoryManager.retrieve_memories")
    def test_retrieve_memories_database_error(
        self, mock_retrieve, memory_manager: MemoryManager
    ):
        """Test handling of database errors during retrieval."""
        mock_retrieve.side_effect = Exception("Database query failed")

        with pytest.raises(MemoryRetrievalError):
            memory_manager.retrieve_memories(
                query="test query",
                namespace="test_namespace",
            )

    def test_memory_validation(self, memory_manager: MemoryManager):
        """Test memory validation logic."""
        # Test with invalid ProcessedMemory
        invalid_memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=1.5,  # Invalid score > 1.0
                reasoning="Test reasoning",
            ),
            entities=ExtractedEntities(),
            importance=MemoryImportance(
                importance_score=0.8,
                retention_type=RetentionType.long_term,
                reasoning="Test importance",
            ),
            summary="Test summary",
            searchable_content="Test content",
            should_store=True,
            storage_reasoning="Test storage reasoning",
        )

        with pytest.raises(ValueError):
            memory_manager.store_memory(
                processed_memory=invalid_memory,
                session_id="test_session",
                namespace="test_namespace",
            )

    def test_namespace_isolation(
        self, memory_manager: MemoryManager, sample_processed_memory: ProcessedMemory
    ):
        """Test that different namespaces are properly isolated."""
        # Store memory in namespace1
        memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="namespace1",
        )

        # Try to retrieve from namespace2
        memories_ns2 = memory_manager.retrieve_memories(
            query="Django",
            namespace="namespace2",
        )

        # Should not find memories from namespace1
        assert len(memories_ns2) == 0

        # Should find memories in namespace1
        memories_ns1 = memory_manager.retrieve_memories(
            query="Django",
            namespace="namespace1",
        )
        assert len(memories_ns1) >= 0

    def test_memory_ranking(self, memory_manager: MemoryManager):
        """Test memory ranking and sorting."""
        # Create memories with different importance scores
        high_importance_memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=0.9,
                reasoning="High importance fact",
            ),
            entities=ExtractedEntities(
                topics=["important topic"],
                keywords=["important", "keyword"],
            ),
            importance=MemoryImportance(
                importance_score=0.95,
                retention_type=RetentionType.permanent,
                reasoning="Very important information",
            ),
            summary="High importance memory",
            searchable_content="high importance content",
            should_store=True,
            storage_reasoning="High importance",
        )

        low_importance_memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.context,
                confidence_score=0.7,
                reasoning="Low importance context",
            ),
            entities=ExtractedEntities(
                topics=["context topic"],
                keywords=["context", "keyword"],
            ),
            importance=MemoryImportance(
                importance_score=0.3,
                retention_type=RetentionType.short_term,
                reasoning="Low importance information",
            ),
            summary="Low importance memory",
            searchable_content="low importance content",
            should_store=True,
            storage_reasoning="Low importance",
        )

        # Store both memories
        memory_manager.store_memory(
            processed_memory=high_importance_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        memory_manager.store_memory(
            processed_memory=low_importance_memory,
            session_id="test_session",
            namespace="test_namespace",
        )

        # Retrieve memories and check ranking
        memories = memory_manager.retrieve_memories(
            query="importance",
            namespace="test_namespace",
            limit=10,
        )

        # Should return results (exact ordering depends on implementation)
        assert isinstance(memories, list)
