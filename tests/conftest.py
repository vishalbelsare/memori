"""
Pytest configuration and shared fixtures for Memoriai tests.
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, Mock

import pytest

from memoriai.config.settings import DatabaseSettings, MemoriSettings
from memoriai.core.database import DatabaseManager
from memoriai.core.memory import MemoryManager
from memoriai.utils.pydantic_models import (
    ExtractedEntities,
    MemoryCategory,
    MemoryCategoryType,
    MemoryImportance,
    ProcessedMemory,
    RetentionType,
)


@pytest.fixture(scope="session")
def test_settings() -> MemoriSettings:
    """Create test settings configuration."""
    return MemoriSettings(
        database=DatabaseSettings(
            connection_string="sqlite:///:memory:",
            echo=False,
            pool_size=1,
            max_overflow=0,
        )
    )


@pytest.fixture
def temp_db_file() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_db_settings(temp_db_file: str) -> MemoriSettings:
    """Create test settings with temporary database file."""
    return MemoriSettings(
        database=DatabaseSettings(
            connection_string=f"sqlite:///{temp_db_file}",
            echo=False,
        )
    )


@pytest.fixture
def memory_db_settings() -> MemoriSettings:
    """Create test settings with in-memory database."""
    return MemoriSettings(
        database=DatabaseSettings(
            connection_string="sqlite:///:memory:",
            echo=False,
        )
    )


@pytest.fixture
def db_manager(memory_db_settings: MemoriSettings) -> DatabaseManager:
    """Create a database manager with in-memory database."""
    manager = DatabaseManager(memory_db_settings.database)
    manager.initialize_database()
    return manager


@pytest.fixture
def memory_manager(db_manager: DatabaseManager) -> MemoryManager:
    """Create a memory manager with initialized database."""
    return MemoryManager(db_manager)


@pytest.fixture
def session_id() -> str:
    """Generate a unique session ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def namespace() -> str:
    """Default test namespace."""
    return "test_namespace"


@pytest.fixture
def sample_processed_memory() -> ProcessedMemory:
    """Create a sample processed memory object for testing."""
    return ProcessedMemory(
        category=MemoryCategory(
            primary_category=MemoryCategoryType.fact,
            confidence_score=0.9,
            reasoning="This is factual information about Python programming",
        ),
        entities=ExtractedEntities(
            technologies=["Python", "Django"],
            topics=["web development", "programming"],
            people=["John Doe"],
            keywords=["Python", "Django", "web", "framework"],
        ),
        importance=MemoryImportance(
            importance_score=0.8,
            retention_type=RetentionType.long_term,
            reasoning="Important technical knowledge for development",
        ),
        summary="Python Django web framework discussion",
        searchable_content="Python Django web development framework tutorial",
        should_store=True,
        storage_reasoning="Contains valuable technical information",
    )


@pytest.fixture
def sample_conversation_data() -> Dict[str, Any]:
    """Create sample conversation data for testing."""
    return {
        "user_input": "How do I create a Django model?",
        "ai_output": "To create a Django model, you need to define a class that inherits from models.Model...",
        "model": "gpt-4",
        "timestamp": "2025-01-01T12:00:00Z",
        "metadata": {
            "tokens_used": 150,
            "response_time": 1.2,
            "temperature": 0.7,
        },
    }


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = Mock()
    return mock_client


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for testing."""
    mock_client = Mock()
    mock_client.messages = Mock()
    mock_client.messages.create = Mock()
    return mock_client


@pytest.fixture
def mock_litellm():
    """Create a mock LiteLLM for testing."""
    mock_completion = AsyncMock()
    return mock_completion


@pytest.fixture(autouse=True)
def clean_test_environment():
    """Clean up test environment before and after each test."""
    # Setup
    yield
    # Teardown - can add cleanup logic here if needed
    pass


@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory path."""
    return Path(__file__).parent / "fixtures" / "data"


@pytest.fixture
def sample_memory_categories():
    """Sample memory categories for testing."""
    return [
        MemoryCategoryType.fact,
        MemoryCategoryType.preference,
        MemoryCategoryType.skill,
        MemoryCategoryType.context,
        MemoryCategoryType.rule,
    ]


@pytest.fixture
def sample_retention_types():
    """Sample retention types for testing."""
    return [
        RetentionType.short_term,
        RetentionType.long_term,
        RetentionType.permanent,
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark tests in integration directory as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        # Mark tests in unit directory as unit tests
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Mark tests in performance directory as performance tests
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
