"""
Unit tests for memoriai.utils.pydantic_models module.
"""

import pytest
from datetime import datetime
from typing import List, Optional

from pydantic import ValidationError

from memoriai.utils.pydantic_models import (
    MemoryCategory,
    MemoryImportance,
    ExtractedEntities,
    ProcessedMemory,
    MemoryCategoryType,
    RetentionType,
    ConversationRecord,
    SearchQuery,
    MemoryRecord,
)


class TestMemoryCategory:
    """Test the MemoryCategory model."""

    def test_memory_category_valid(self):
        """Test creating a valid MemoryCategory."""
        category = MemoryCategory(
            primary_category=MemoryCategoryType.fact,
            confidence_score=0.85,
            reasoning="This contains factual information about programming",
        )
        
        assert category.primary_category == MemoryCategoryType.fact
        assert category.confidence_score == 0.85
        assert category.reasoning == "This contains factual information about programming"

    def test_memory_category_confidence_score_validation(self):
        """Test confidence score validation."""
        # Valid scores (0.0 to 1.0)
        valid_scores = [0.0, 0.5, 0.99, 1.0]
        for score in valid_scores:
            category = MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=score,
                reasoning="Test reasoning",
            )
            assert category.confidence_score == score
        
        # Invalid scores
        invalid_scores = [-0.1, 1.1, 2.0, -1.0]
        for score in invalid_scores:
            with pytest.raises(ValidationError):
                MemoryCategory(
                    primary_category=MemoryCategoryType.fact,
                    confidence_score=score,
                    reasoning="Test reasoning",
                )

    def test_memory_category_all_types(self):
        """Test all memory category types."""
        categories = [
            MemoryCategoryType.fact,
            MemoryCategoryType.preference,
            MemoryCategoryType.skill,
            MemoryCategoryType.context,
            MemoryCategoryType.rule,
        ]
        
        for cat_type in categories:
            category = MemoryCategory(
                primary_category=cat_type,
                confidence_score=0.8,
                reasoning=f"Testing {cat_type} category",
            )
            assert category.primary_category == cat_type


class TestMemoryImportance:
    """Test the MemoryImportance model."""

    def test_memory_importance_valid(self):
        """Test creating a valid MemoryImportance."""
        importance = MemoryImportance(
            importance_score=0.7,
            retention_type=RetentionType.long_term,
            reasoning="Important for future reference",
        )
        
        assert importance.importance_score == 0.7
        assert importance.retention_type == RetentionType.long_term
        assert importance.reasoning == "Important for future reference"

    def test_memory_importance_score_validation(self):
        """Test importance score validation."""
        # Valid scores
        valid_scores = [0.0, 0.5, 0.99, 1.0]
        for score in valid_scores:
            importance = MemoryImportance(
                importance_score=score,
                retention_type=RetentionType.short_term,
                reasoning="Test reasoning",
            )
            assert importance.importance_score == score
        
        # Invalid scores
        invalid_scores = [-0.1, 1.1, 2.0]
        for score in invalid_scores:
            with pytest.raises(ValidationError):
                MemoryImportance(
                    importance_score=score,
                    retention_type=RetentionType.short_term,
                    reasoning="Test reasoning",
                )

    def test_retention_types(self):
        """Test all retention types."""
        retention_types = [
            RetentionType.short_term,
            RetentionType.long_term,
            RetentionType.permanent,
        ]
        
        for ret_type in retention_types:
            importance = MemoryImportance(
                importance_score=0.5,
                retention_type=ret_type,
                reasoning=f"Testing {ret_type} retention",
            )
            assert importance.retention_type == ret_type


class TestExtractedEntities:
    """Test the ExtractedEntities model."""

    def test_extracted_entities_empty(self):
        """Test creating empty ExtractedEntities."""
        entities = ExtractedEntities()
        
        assert entities.people == []
        assert entities.technologies == []
        assert entities.topics == []
        assert entities.keywords == []
        assert entities.locations == []
        assert entities.organizations == []

    def test_extracted_entities_with_data(self):
        """Test creating ExtractedEntities with data."""
        entities = ExtractedEntities(
            people=["John Doe", "Jane Smith"],
            technologies=["Python", "Django", "PostgreSQL"],
            topics=["web development", "database design"],
            keywords=["programming", "framework", "ORM"],
            locations=["San Francisco", "New York"],
            organizations=["Google", "Microsoft"],
        )
        
        assert entities.people == ["John Doe", "Jane Smith"]
        assert entities.technologies == ["Python", "Django", "PostgreSQL"]
        assert entities.topics == ["web development", "database design"]
        assert entities.keywords == ["programming", "framework", "ORM"]
        assert entities.locations == ["San Francisco", "New York"]
        assert entities.organizations == ["Google", "Microsoft"]

    def test_extracted_entities_deduplication(self):
        """Test that duplicate entities are handled properly."""
        entities = ExtractedEntities(
            people=["John Doe", "John Doe", "Jane Smith"],
            technologies=["Python", "Python", "Django"],
        )
        
        # Note: Deduplication logic would be in the business logic, not the model
        # But we can test that duplicates are preserved in the model if needed
        assert len(entities.people) == 3
        assert len(entities.technologies) == 3


class TestProcessedMemory:
    """Test the ProcessedMemory model."""

    def test_processed_memory_complete(self):
        """Test creating a complete ProcessedMemory."""
        memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=0.9,
                reasoning="Factual programming information",
            ),
            entities=ExtractedEntities(
                technologies=["Python", "FastAPI"],
                topics=["API development"],
                keywords=["REST", "API", "Python"],
            ),
            importance=MemoryImportance(
                importance_score=0.8,
                retention_type=RetentionType.long_term,
                reasoning="Important for API development work",
            ),
            summary="Discussion about FastAPI Python framework",
            searchable_content="FastAPI Python web framework REST API development",
            should_store=True,
            storage_reasoning="Contains valuable technical information",
        )
        
        assert memory.category.primary_category == MemoryCategoryType.fact
        assert memory.entities.technologies == ["Python", "FastAPI"]
        assert memory.importance.importance_score == 0.8
        assert memory.summary == "Discussion about FastAPI Python framework"
        assert memory.should_store is True

    def test_processed_memory_minimal(self):
        """Test creating ProcessedMemory with minimal required fields."""
        memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.context,
                confidence_score=0.6,
                reasoning="Contextual information",
            ),
            entities=ExtractedEntities(),
            importance=MemoryImportance(
                importance_score=0.3,
                retention_type=RetentionType.short_term,
                reasoning="Low importance context",
            ),
            summary="Brief context",
            searchable_content="context information",
            should_store=False,
            storage_reasoning="Not important enough to store",
        )
        
        assert memory.should_store is False
        assert memory.importance.retention_type == RetentionType.short_term

    def test_processed_memory_validation(self):
        """Test ProcessedMemory validation."""
        # Test with invalid category confidence score
        with pytest.raises(ValidationError):
            ProcessedMemory(
                category=MemoryCategory(
                    primary_category=MemoryCategoryType.fact,
                    confidence_score=1.5,  # Invalid
                    reasoning="Test",
                ),
                entities=ExtractedEntities(),
                importance=MemoryImportance(
                    importance_score=0.5,
                    retention_type=RetentionType.short_term,
                    reasoning="Test",
                ),
                summary="Test",
                searchable_content="Test",
                should_store=True,
                storage_reasoning="Test",
            )


class TestConversationRecord:
    """Test the ConversationRecord model."""

    def test_conversation_record_basic(self):
        """Test creating a basic ConversationRecord."""
        record = ConversationRecord(
            chat_id="chat_123",
            user_input="What is Python?",
            ai_output="Python is a programming language.",
            model="gpt-3.5-turbo",
            session_id="session_456",
            namespace="default",
        )
        
        assert record.chat_id == "chat_123"
        assert record.user_input == "What is Python?"
        assert record.ai_output == "Python is a programming language."
        assert record.model == "gpt-3.5-turbo"
        assert record.session_id == "session_456"
        assert record.namespace == "default"
        assert record.timestamp is not None

    def test_conversation_record_with_metadata(self):
        """Test ConversationRecord with metadata."""
        metadata = {
            "tokens_used": 50,
            "response_time": 1.5,
            "temperature": 0.7,
        }
        
        record = ConversationRecord(
            chat_id="chat_123",
            user_input="Test input",
            ai_output="Test output",
            model="gpt-4",
            session_id="session_456",
            namespace="test",
            metadata=metadata,
        )
        
        assert record.metadata == metadata
        assert record.metadata["tokens_used"] == 50

    def test_conversation_record_timestamp_auto(self):
        """Test that timestamp is automatically set."""
        record = ConversationRecord(
            chat_id="chat_123",
            user_input="Test",
            ai_output="Test",
            model="test-model",
            session_id="session_456",
            namespace="default",
        )
        
        assert isinstance(record.timestamp, datetime)
        # Should be recent (within last few seconds)
        time_diff = datetime.utcnow() - record.timestamp
        assert time_diff.total_seconds() < 10


class TestSearchQuery:
    """Test the SearchQuery model."""

    def test_search_query_basic(self):
        """Test creating a basic SearchQuery."""
        query = SearchQuery(
            query_text="Python programming",
            namespace="default",
        )
        
        assert query.query_text == "Python programming"
        assert query.namespace == "default"
        assert query.limit == 10  # Default
        assert query.category_filter is None
        assert query.importance_threshold is None

    def test_search_query_with_filters(self):
        """Test SearchQuery with filters."""
        query = SearchQuery(
            query_text="Django web framework",
            namespace="development",
            limit=20,
            category_filter=[MemoryCategoryType.fact, MemoryCategoryType.skill],
            importance_threshold=0.7,
        )
        
        assert query.limit == 20
        assert query.category_filter == [MemoryCategoryType.fact, MemoryCategoryType.skill]
        assert query.importance_threshold == 0.7

    def test_search_query_validation(self):
        """Test SearchQuery validation."""
        # Test invalid limit
        with pytest.raises(ValidationError):
            SearchQuery(
                query_text="test",
                namespace="default",
                limit=0,  # Invalid
            )
        
        # Test invalid importance threshold
        with pytest.raises(ValidationError):
            SearchQuery(
                query_text="test",
                namespace="default",
                importance_threshold=1.5,  # Invalid
            )


class TestMemoryRecord:
    """Test the MemoryRecord model."""

    def test_memory_record_basic(self):
        """Test creating a basic MemoryRecord."""
        record = MemoryRecord(
            memory_id="mem_123",
            summary="Test memory summary",
            category=MemoryCategoryType.fact,
            importance_score=0.8,
            retention_type=RetentionType.long_term,
            session_id="session_456",
            namespace="default",
        )
        
        assert record.memory_id == "mem_123"
        assert record.summary == "Test memory summary"
        assert record.category == MemoryCategoryType.fact
        assert record.importance_score == 0.8
        assert record.retention_type == RetentionType.long_term
        assert record.created_at is not None

    def test_memory_record_with_entities(self):
        """Test MemoryRecord with extracted entities."""
        entities = ExtractedEntities(
            technologies=["Python"],
            topics=["programming"],
        )
        
        record = MemoryRecord(
            memory_id="mem_123",
            summary="Python programming discussion",
            category=MemoryCategoryType.fact,
            importance_score=0.8,
            retention_type=RetentionType.long_term,
            session_id="session_456",
            namespace="default",
            entities=entities,
        )
        
        assert record.entities == entities
        assert record.entities.technologies == ["Python"]

    def test_memory_record_validation(self):
        """Test MemoryRecord validation."""
        # Test invalid importance score
        with pytest.raises(ValidationError):
            MemoryRecord(
                memory_id="mem_123",
                summary="Test",
                category=MemoryCategoryType.fact,
                importance_score=1.5,  # Invalid
                retention_type=RetentionType.long_term,
                session_id="session_456",
                namespace="default",
            )


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_processed_memory_json_serialization(self):
        """Test ProcessedMemory JSON serialization."""
        memory = ProcessedMemory(
            category=MemoryCategory(
                primary_category=MemoryCategoryType.fact,
                confidence_score=0.9,
                reasoning="Test reasoning",
            ),
            entities=ExtractedEntities(
                technologies=["Python"],
                keywords=["test"],
            ),
            importance=MemoryImportance(
                importance_score=0.8,
                retention_type=RetentionType.long_term,
                reasoning="Test importance",
            ),
            summary="Test summary",
            searchable_content="Test content",
            should_store=True,
            storage_reasoning="Test storage",
        )
        
        # Serialize to JSON
        json_str = memory.model_dump_json()
        assert isinstance(json_str, str)
        assert "fact" in json_str
        assert "Python" in json_str
        
        # Deserialize from JSON
        memory_dict = memory.model_dump()
        restored_memory = ProcessedMemory(**memory_dict)
        
        assert restored_memory.category.primary_category == MemoryCategoryType.fact
        assert restored_memory.entities.technologies == ["Python"]
        assert restored_memory.importance.importance_score == 0.8

    def test_conversation_record_serialization(self):
        """Test ConversationRecord serialization."""
        record = ConversationRecord(
            chat_id="chat_123",
            user_input="Test input",
            ai_output="Test output",
            model="test-model",
            session_id="session_456",
            namespace="default",
        )
        
        # Serialize to dict
        record_dict = record.model_dump()
        assert isinstance(record_dict, dict)
        assert record_dict["chat_id"] == "chat_123"
        
        # Deserialize from dict
        restored_record = ConversationRecord(**record_dict)
        assert restored_record.chat_id == "chat_123"
        assert restored_record.user_input == "Test input"