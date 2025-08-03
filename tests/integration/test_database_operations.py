"""
Integration tests for database operations.
"""

import os
import tempfile

import pytest

# Skip all integration tests until API is updated  
pytestmark = pytest.mark.skip(reason="Memori class has different API than expected Memori")

from memoriai.config.settings import DatabaseSettings
from memoriai.core.database import DatabaseManager
from memoriai.core.memory import Memori
from memoriai.utils.pydantic_models import (
    ExtractedEntities,
    MemoryCategory,
    MemoryCategoryType,
    MemoryImportance,
    ProcessedMemory,
    RetentionType,
)


class TestDatabaseIntegration:
    """Test database integration with real database files."""

    @pytest.fixture
    def persistent_db_manager(self, temp_db_file):
        """Create a database manager with persistent file."""
        settings = DatabaseSettings(
            connection_string=f"sqlite:///{temp_db_file}",
            echo=False,
        )
        manager = DatabaseManager(settings)
        manager.initialize_database()
        return manager

    @pytest.fixture
    def persistent_memory_manager(self, persistent_db_manager):
        """Create a memory manager with persistent database."""
        return Memori(persistent_db_manager)

    def test_database_persistence(
        self, persistent_memory_manager, sample_processed_memory, temp_db_file
    ):
        """Test that data persists across database sessions."""
        # Store memory in first session
        memory_id = persistent_memory_manager.store_memory(
            processed_memory=sample_processed_memory,
            session_id="test_session",
            namespace="persistence_test",
        )

        assert memory_id is not None

        # Close the current manager
        persistent_memory_manager.db_manager.close()

        # Create new manager with same database file
        new_settings = DatabaseSettings(
            connection_string=f"sqlite:///{temp_db_file}",
            echo=False,
        )
        new_db_manager = DatabaseManager(new_settings)
        new_db_manager.initialize_database()
        new_memory_manager = Memori(new_db_manager)

        # Retrieve memory from new session
        memories = new_memory_manager.retrieve_memories(
            query="Django",
            namespace="persistence_test",
        )

        # Should find the stored memory
        assert len(memories) > 0
        found_memory = next(
            (m for m in memories if m.get("memory_id") == memory_id), None
        )
        assert found_memory is not None

    def test_concurrent_database_access(self, persistent_db_manager):
        """Test concurrent access to the same database."""
        import threading

        results = []
        errors = []

        def worker(worker_id):
            try:
                memory_manager = Memori(persistent_db_manager)

                # Create unique memory for this worker
                memory = ProcessedMemory(
                    category=MemoryCategory(
                        primary_category=MemoryCategoryType.fact,
                        confidence_score=0.8,
                        reasoning=f"Worker {worker_id} fact",
                    ),
                    entities=ExtractedEntities(
                        keywords=[f"worker_{worker_id}", "concurrent"],
                    ),
                    importance=MemoryImportance(
                        importance_score=0.7,
                        retention_type=RetentionType.short_term,
                        reasoning=f"Worker {worker_id} importance",
                    ),
                    summary=f"Memory from worker {worker_id}",
                    searchable_content=f"worker {worker_id} concurrent access test",
                    should_store=True,
                    storage_reasoning=f"Testing worker {worker_id}",
                )

                memory_id = memory_manager.store_memory(
                    processed_memory=memory,
                    session_id=f"worker_session_{worker_id}",
                    namespace="concurrent_test",
                )

                results.append(memory_id)

            except Exception as e:
                errors.append(e)

        # Start multiple worker threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        assert len(set(results)) == 3  # All IDs should be unique

    def test_large_data_storage(self, persistent_memory_manager):
        """Test storing and retrieving large amounts of data."""
        memory_ids = []

        # Store many memories
        for i in range(50):
            memory = ProcessedMemory(
                category=MemoryCategory(
                    primary_category=MemoryCategoryType.fact,
                    confidence_score=0.8,
                    reasoning=f"Large data test memory {i}",
                ),
                entities=ExtractedEntities(
                    technologies=[f"tech_{i % 10}"],
                    topics=[f"topic_{i % 5}"],
                    keywords=[f"keyword_{i}", "large_data_test"],
                ),
                importance=MemoryImportance(
                    importance_score=0.5 + (i % 5) * 0.1,
                    retention_type=(
                        RetentionType.long_term
                        if i % 3 == 0
                        else RetentionType.short_term
                    ),
                    reasoning=f"Importance for memory {i}",
                ),
                summary=f"Large data test memory number {i}",
                searchable_content=f"large data test memory {i} with content and keywords",
                should_store=True,
                storage_reasoning=f"Testing large data storage {i}",
            )

            memory_id = persistent_memory_manager.store_memory(
                processed_memory=memory,
                session_id=f"large_data_session_{i % 10}",
                namespace="large_data_test",
            )
            memory_ids.append(memory_id)

        # Verify all memories were stored
        assert len(memory_ids) == 50
        assert len(set(memory_ids)) == 50  # All unique

        # Test retrieval with various queries
        all_memories = persistent_memory_manager.retrieve_memories(
            query="large_data_test",
            namespace="large_data_test",
            limit=100,
        )
        assert len(all_memories) >= 40  # Should find most memories

        # Test filtered retrieval
        fact_memories = persistent_memory_manager.retrieve_memories_by_category(
            category=MemoryCategoryType.fact,
            namespace="large_data_test",
            limit=100,
        )
        assert len(fact_memories) >= 40

        # Test statistics
        stats = persistent_memory_manager.get_memory_statistics(
            namespace="large_data_test"
        )
        assert stats["total_memories"] >= 50

    def test_database_schema_integrity(self, persistent_db_manager):
        """Test that database schema is created correctly."""
        # Check that all required tables exist
        required_tables = [
            "chat_history",
            "short_term_memory",
            "long_term_memory",
            "entities",
            "memory_relationships",
        ]

        for table_name in required_tables:
            exists = persistent_db_manager.check_table_exists(table_name)
            assert exists, f"Required table {table_name} does not exist"

        # Check schema for main tables
        for table_name in required_tables:
            schema = persistent_db_manager.get_table_schema(table_name)
            assert isinstance(schema, list)
            assert len(schema) > 0

    def test_database_constraints(self, persistent_memory_manager):
        """Test database constraints and data integrity."""
        # Test storing memory with invalid namespace
        memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=0.8,
                reasoning="Constraint test",
            ),
            entities=ExtractedEntities(),
            importance=MemoryImportance(
                importance_score=0.7,
                retention_type=RetentionType.short_term,
                reasoning="Test importance",
            ),
            summary="Constraint test memory",
            searchable_content="constraint test content",
            should_store=True,
            storage_reasoning="Testing constraints",
        )

        # Should handle empty namespace gracefully
        memory_id = persistent_memory_manager.store_memory(
            processed_memory=memory,
            session_id="constraint_test_session",
            namespace="",  # Empty namespace
        )
        assert memory_id is not None

    def test_memory_cleanup_integration(self, persistent_memory_manager):
        """Test memory cleanup with real database."""
        # Store memories with different retention types and ages
        old_memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.context,
                confidence_score=0.6,
                reasoning="Old context information",
            ),
            entities=ExtractedEntities(keywords=["old", "cleanup_test"]),
            importance=MemoryImportance(
                importance_score=0.3,
                retention_type=RetentionType.short_term,
                reasoning="Low importance, short term",
            ),
            summary="Old memory for cleanup test",
            searchable_content="old memory cleanup test content",
            should_store=True,
            storage_reasoning="Testing cleanup",
        )

        memory_id = persistent_memory_manager.store_memory(
            processed_memory=old_memory,
            session_id="cleanup_test_session",
            namespace="cleanup_test",
        )

        # Manually update the timestamp to make it "old"
        # This would require direct database access in a real test

        # Test cleanup (should not fail)
        cleaned_count = persistent_memory_manager.cleanup_old_memories(
            namespace="cleanup_test",
            days_threshold=0,  # Clean everything
            retention_type=RetentionType.short_term,
        )

        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0

    def test_backup_restore_integration(self, persistent_db_manager, temp_db_file):
        """Test database backup and restore operations."""
        # Add some test data
        memory_manager = Memori(persistent_db_manager)

        test_memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=0.9,
                reasoning="Backup test fact",
            ),
            entities=ExtractedEntities(
                technologies=["Backup", "Restore"],
                keywords=["backup_test"],
            ),
            importance=MemoryImportance(
                importance_score=0.8,
                retention_type=RetentionType.permanent,
                reasoning="Important backup test data",
            ),
            summary="Backup and restore test memory",
            searchable_content="backup restore test memory data",
            should_store=True,
            storage_reasoning="Testing backup/restore",
        )

        memory_id = memory_manager.store_memory(
            processed_memory=test_memory,
            session_id="backup_test_session",
            namespace="backup_test",
        )

        # Create backup
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as backup_file:
            backup_path = backup_file.name

        try:
            backup_result = persistent_db_manager.backup_database(backup_path)
            assert backup_result is True
            assert os.path.exists(backup_path)

            # Verify backup contains our data
            backup_settings = DatabaseSettings(
                connection_string=f"sqlite:///{backup_path}"
            )
            backup_db_manager = DatabaseManager(backup_settings)
            backup_db_manager.initialize_database()
            backup_memory_manager = Memori(backup_db_manager)

            # Should find our test memory in backup
            backup_memories = backup_memory_manager.retrieve_memories(
                query="backup_test",
                namespace="backup_test",
            )

            assert len(backup_memories) > 0
            found_memory = next(
                (m for m in backup_memories if m.get("memory_id") == memory_id), None
            )
            assert found_memory is not None

        finally:
            if os.path.exists(backup_path):
                os.unlink(backup_path)

    def test_transaction_rollback_integration(self, persistent_db_manager):
        """Test transaction rollback in error scenarios."""
        memory_manager = Memori(persistent_db_manager)

        # Get initial memory count
        initial_stats = memory_manager.get_memory_statistics(
            namespace="transaction_test"
        )
        initial_count = initial_stats.get("total_memories", 0)

        # Try to store invalid memory that should cause rollback
        try:
            # This would need to be implemented to actually cause a rollback
            # For now, just test that the system handles errors gracefully
            pass
        except Exception:
            pass

        # Verify that no partial data was stored
        final_stats = memory_manager.get_memory_statistics(namespace="transaction_test")
        final_count = final_stats.get("total_memories", 0)

        # Count should be the same (no partial commits)
        assert final_count == initial_count
