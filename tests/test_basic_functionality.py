"""
Basic functionality tests for Memori
"""

import pytest
import tempfile
import os
from pathlib import Path

from memoriai import Memori, MemoryCategory
from memoriai.core.database import MemoryItem
from memoriai.utils.enums import MemoryType


class TestMemori:
    """Test the main Memori class"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
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
            model="test-model"
        )
        
        assert chat_id is not None
        assert len(chat_id) > 0
        
        # Check conversation history
        history = memori.get_conversation_history(limit=1)
        assert len(history) == 1
        assert history[0]['user_input'] == "What is Python?"
        assert history[0]['ai_output'] == "Python is a programming language."
    
    def test_memory_stats(self, temp_db):
        """Test memory statistics"""
        memori = Memori(database_connect=temp_db)
        memori.enable()
        
        # Record a conversation
        memori.record_conversation(
            user_input="Test input",
            ai_output="Test output",
            model="test-model"
        )
        
        stats = memori.get_memory_stats()
        assert 'chat_history_count' in stats
        assert stats['chat_history_count'] >= 1


class TestMemoryItem:
    """Test MemoryItem class"""
    
    def test_memory_item_creation(self):
        """Test memory item creation"""
        item = MemoryItem(
            content="Test memory content",
            category=MemoryCategory.STORE_AS_FACT,
            memory_type=MemoryType.SHORT_TERM,
            importance_score=0.8
        )
        
        assert item.content == "Test memory content"
        assert item.category == MemoryCategory.STORE_AS_FACT
        assert item.memory_type == MemoryType.SHORT_TERM
        assert item.importance_score == 0.8
        assert item.memory_id is not None
        assert item.created_at is not None


if __name__ == "__main__":
    pytest.main([__file__])