"""
Test helper functions and utilities.
"""

import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator
from unittest.mock import Mock, patch
from contextlib import contextmanager

from memoriai.config.settings import MemoriSettings, DatabaseSettings
from memoriai.core.database import DatabaseManager
from memoriai.core.memory import MemoryManager
from memoriai.utils.pydantic_models import ProcessedMemory


class TestHelpers:
    """Collection of helper functions for testing."""

    @staticmethod
    def create_test_database_manager(
        connection_string: Optional[str] = None,
        **kwargs
    ) -> DatabaseManager:
        """Create a test database manager with appropriate settings."""
        if connection_string is None:
            connection_string = "sqlite:///:memory:"
        
        settings = DatabaseSettings(
            connection_string=connection_string,
            echo=False,
            **kwargs
        )
        
        manager = DatabaseManager(settings)
        manager.initialize_database()
        return manager

    @staticmethod
    def create_test_memory_manager(
        db_manager: Optional[DatabaseManager] = None
    ) -> MemoryManager:
        """Create a test memory manager."""
        if db_manager is None:
            db_manager = TestHelpers.create_test_database_manager()
        
        return MemoryManager(db_manager)

    @staticmethod
    @contextmanager
    def temporary_database() -> Generator[str, None, None]:
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        
        try:
            yield temp_path
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @staticmethod
    def populate_test_database(
        memory_manager: MemoryManager,
        memories: List[ProcessedMemory],
        namespace: str = "test",
        session_id: str = "test_session"
    ) -> List[str]:
        """Populate test database with sample memories."""
        memory_ids = []
        
        for memory in memories:
            memory_id = memory_manager.store_memory(
                processed_memory=memory,
                session_id=session_id,
                namespace=namespace,
            )
            memory_ids.append(memory_id)
        
        return memory_ids

    @staticmethod
    def assert_memory_equals(
        actual: Dict[str, Any],
        expected: ProcessedMemory,
        check_id: bool = False
    ) -> None:
        """Assert that a retrieved memory matches the expected ProcessedMemory."""
        if not check_id:
            # Remove ID from comparison if not checking it
            actual = {k: v for k, v in actual.items() if k != "memory_id"}
        
        assert actual["summary"] == expected.summary
        assert actual["searchable_content"] == expected.searchable_content
        assert actual["should_store"] == expected.should_store
        
        # Check category
        assert actual["category"] == expected.category.primary_category.value
        
        # Check importance
        assert abs(actual["importance_score"] - expected.importance.importance_score) < 0.01
        assert actual["retention_type"] == expected.importance.retention_type.value

    @staticmethod
    def create_mock_llm_response(
        content: str,
        model: str = "test-model",
        tokens_used: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a mock LLM response for testing."""
        return {
            "id": "test_response_123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": tokens_used // 2,
                "completion_tokens": tokens_used // 2,
                "total_tokens": tokens_used
            },
            **kwargs
        }

    @staticmethod
    def create_mock_memory_manager() -> Mock:
        """Create a mock memory manager for testing."""
        mock_manager = Mock()
        
        # Setup common method returns
        mock_manager.store_memory.return_value = "test_memory_id_123"
        mock_manager.retrieve_memories.return_value = []
        mock_manager.get_memory_statistics.return_value = {
            "total_memories": 0,
            "memory_categories": {},
            "retention_types": {}
        }
        mock_manager.process_conversation.return_value = "test_memory_id_456"
        
        return mock_manager

    @staticmethod
    def create_test_config(
        temp_db_path: Optional[str] = None,
        **overrides
    ) -> MemoriSettings:
        """Create test configuration."""
        config = {
            "database": {
                "connection_string": f"sqlite:///{temp_db_path}" if temp_db_path else "sqlite:///:memory:",
                "echo": False,
            },
            "agents": {
                "default_model": "test-model",
                "default_temperature": 0.7,
                "max_tokens": 1000,
            },
            "memory": {
                "default_namespace": "test",
                "importance_threshold": 0.5,
            },
            "logging": {
                "level": "WARNING",  # Reduce noise in tests
            },
        }
        
        # Apply overrides
        config.update(overrides)
        
        return MemoriSettings(**config)

    @staticmethod
    def assert_valid_memory_id(memory_id: str) -> None:
        """Assert that a memory ID is valid."""
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0
        assert memory_id.strip() == memory_id  # No leading/trailing whitespace

    @staticmethod
    def assert_valid_statistics(stats: Dict[str, Any]) -> None:
        """Assert that memory statistics are valid."""
        assert isinstance(stats, dict)
        assert "total_memories" in stats
        assert "memory_categories" in stats
        assert "retention_types" in stats
        
        assert isinstance(stats["total_memories"], int)
        assert stats["total_memories"] >= 0
        assert isinstance(stats["memory_categories"], dict)
        assert isinstance(stats["retention_types"], dict)

    @staticmethod
    def create_test_session_context(
        session_id: str = "test_session",
        namespace: str = "test_namespace",
        user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Create test session context."""
        context = {
            "session_id": session_id,
            "namespace": namespace,
        }
        
        if user_id:
            context["user_id"] = user_id
        
        return context

    @staticmethod
    def wait_for_condition(
        condition_func,
        timeout: float = 5.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true."""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        
        return False

    @staticmethod
    def compare_memories_list(
        actual: List[Dict[str, Any]],
        expected: List[ProcessedMemory],
        ordered: bool = False
    ) -> None:
        """Compare a list of retrieved memories with expected ProcessedMemory objects."""
        assert len(actual) == len(expected), f"Expected {len(expected)} memories, got {len(actual)}"
        
        if ordered:
            # Compare in order
            for i, (actual_memory, expected_memory) in enumerate(zip(actual, expected)):
                TestHelpers.assert_memory_equals(actual_memory, expected_memory)
        else:
            # Compare without order consideration
            actual_summaries = {memory["summary"] for memory in actual}
            expected_summaries = {memory.summary for memory in expected}
            assert actual_summaries == expected_summaries

    @staticmethod
    def create_performance_dataset(size: int) -> List[ProcessedMemory]:
        """Create a dataset for performance testing."""
        from .sample_data import SampleData
        return SampleData.get_large_dataset(size)

    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> tuple:
        """Measure execution time of a function."""
        import time
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    def create_file_with_content(
        directory: str,
        filename: str,
        content: str
    ) -> str:
        """Create a file with specified content in a directory."""
        file_path = os.path.join(directory, filename)
        os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path

    @staticmethod
    def load_json_file(file_path: str) -> Dict[str, Any]:
        """Load JSON content from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_json_file(data: Dict[str, Any], file_path: str) -> None:
        """Save data to a JSON file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    @staticmethod
    def cleanup_test_files(*file_paths: str) -> None:
        """Clean up test files."""
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except OSError:
                    pass  # Ignore cleanup errors in tests


class MockHelpers:
    """Helper functions for creating mocks."""

    @staticmethod
    def create_mock_openai_client():
        """Create a mock OpenAI client."""
        mock_client = Mock()
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create = Mock()
        return mock_client

    @staticmethod
    def create_mock_anthropic_client():
        """Create a mock Anthropic client."""
        mock_client = Mock()
        mock_client.messages = Mock()
        mock_client.messages.create = Mock()
        return mock_client

    @staticmethod
    def patch_openai_integration():
        """Context manager to patch OpenAI integration."""
        return patch('memoriai.integrations.openai_integration.openai')

    @staticmethod
    def patch_anthropic_integration():
        """Context manager to patch Anthropic integration."""
        return patch('memoriai.integrations.anthropic_integration.anthropic')

    @staticmethod
    def patch_litellm_integration():
        """Context manager to patch LiteLLM integration."""
        return patch('memoriai.integrations.litellm_integration.litellm')


class AssertionHelpers:
    """Helper functions for custom assertions."""

    @staticmethod
    def assert_memory_stored_correctly(
        memory_manager: MemoryManager,
        memory_id: str,
        expected_memory: ProcessedMemory,
        namespace: str = "test"
    ) -> None:
        """Assert that a memory was stored correctly."""
        # Retrieve the memory
        memories = memory_manager.retrieve_memories(
            query=expected_memory.summary,
            namespace=namespace,
            limit=1
        )
        
        assert len(memories) > 0, "Memory was not found in storage"
        
        # Find the specific memory by ID
        stored_memory = next(
            (m for m in memories if m.get("memory_id") == memory_id),
            None
        )
        
        assert stored_memory is not None, f"Memory with ID {memory_id} not found"
        
        # Compare key fields
        TestHelpers.assert_memory_equals(stored_memory, expected_memory)

    @staticmethod
    def assert_entities_extracted(
        actual_entities: Dict[str, List[str]],
        expected_entities: Dict[str, List[str]]
    ) -> None:
        """Assert that entities were extracted correctly."""
        for entity_type, expected_values in expected_entities.items():
            assert entity_type in actual_entities, f"Entity type {entity_type} not found"
            
            actual_values = actual_entities[entity_type]
            for expected_value in expected_values:
                assert expected_value in actual_values, \
                    f"Expected {expected_value} in {entity_type}, got {actual_values}"

    @staticmethod
    def assert_performance_acceptable(
        execution_time: float,
        max_time: float,
        operation_name: str = "operation"
    ) -> None:
        """Assert that performance is within acceptable limits."""
        assert execution_time <= max_time, \
            f"{operation_name} took {execution_time:.3f}s, expected <= {max_time}s"