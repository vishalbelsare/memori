"""
Basic functionality tests for Memoriai v1.0
"""

import pytest
import tempfile
import os

from memoriai import Memori, MemoryCategoryType, RetentionType
from memoriai.utils.pydantic_models import (
    ProcessedMemory,
    MemoryCategory,
    ExtractedEntities,
    MemoryImportance,
)


class TestMemori:
    """Test the main Memori class"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield f"sqlite:///{temp_path}"
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_memori_initialization(self, temp_db):
        """Test Memori initialization"""
        memori = Memori(database_connect=temp_db)
        assert memori.database_connect == temp_db
        assert memori.template == "basic"
        assert not memori.is_enabled
        assert memori.namespace == "default"

    def test_enable_disable(self, temp_db):
        """Test enable/disable functionality"""
        memori = Memori(database_connect=temp_db)

        # Initially disabled
        assert not memori.is_enabled

        # Enable
        memori.enable()
        assert memori.is_enabled
        assert memori.session_id is not None

        # Disable
        memori.disable()
        assert not memori.is_enabled

    def test_record_conversation(self, temp_db):
        """Test conversation recording"""
        memori = Memori(database_connect=temp_db)
        memori.enable()

        chat_id = memori.record_conversation(
            user_input="What is Python?",
            ai_output="Python is a programming language.",
            model="test-model",
        )

        assert chat_id is not None
        assert len(chat_id) > 0

        # Check conversation history
        history = memori.get_conversation_history(limit=1)
        assert len(history) == 1
        assert history[0]["user_input"] == "What is Python?"
        assert history[0]["ai_output"] == "Python is a programming language."

    def test_memory_stats(self, temp_db):
        """Test memory statistics"""
        memori = Memori(database_connect=temp_db)
        memori.enable()

        # Record a conversation
        memori.record_conversation(
            user_input="Test input", ai_output="Test output", model="test-model"
        )

        stats = memori.get_memory_stats()
        assert "chat_history_count" in stats
        assert stats["chat_history_count"] >= 1


class TestProcessedMemory:
    """Test ProcessedMemory Pydantic model"""

    def test_processed_memory_creation(self):
        """Test ProcessedMemory creation with proper v1.0 structure"""
        processed_memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=0.9,
                reasoning="This is factual information about Python",
            ),
            entities=ExtractedEntities(
                technologies=["Python"],
                topics=["programming language"],
                keywords=["Python", "programming", "language"],
            ),
            importance=MemoryImportance(
                importance_score=0.8,
                retention_type=RetentionType.long_term,
                reasoning="Important technical information",
            ),
            summary="Python is a programming language",
            searchable_content="Python programming language",
            should_store=True,
            storage_reasoning="Contains important technical information",
        )

        assert processed_memory.category.primary_category == MemoryCategoryType.fact
        assert processed_memory.category.confidence_score == 0.9
        assert processed_memory.importance.importance_score == 0.8
        assert processed_memory.importance.retention_type == RetentionType.long_term
        assert processed_memory.should_store is True
        assert "Python" in processed_memory.entities.technologies
        assert processed_memory.summary == "Python is a programming language"

    def test_memory_categories(self):
        """Test that all memory categories are available"""
        # Test all v1.0 categories
        categories = [
            MemoryCategoryType.fact,
            MemoryCategoryType.preference,
            MemoryCategoryType.skill,
            MemoryCategoryType.context,
            MemoryCategoryType.rule,
        ]

        for category in categories:
            memory_category = MemoryCategory(
                primary_category=category,
                confidence_score=0.8,
                reasoning=f"Testing {category} category",
            )
            assert memory_category.primary_category == category

    def test_retention_types(self):
        """Test that all retention types are available"""
        retention_types = [
            RetentionType.short_term,
            RetentionType.long_term,
            RetentionType.permanent,
        ]

        for retention_type in retention_types:
            importance = MemoryImportance(
                importance_score=0.5,
                retention_type=retention_type,
                reasoning=f"Testing {retention_type} retention",
            )
            assert importance.retention_type == retention_type


if __name__ == "__main__":
    pytest.main([__file__])
