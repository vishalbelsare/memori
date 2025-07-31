"""
Memory agent for intelligent memory processing and categorization
"""

import logging
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from ..utils.enums import MemoryCategory, MemoryType, ImportanceLevel
from ..utils.exceptions import AgentError
from .database import MemoryItem

logger = logging.getLogger(__name__)

class MemoryAgent:
    """
    Intelligent agent for memory categorization and processing
    """
    
    def __init__(
        self,
        conscious_ingest: bool = True,
        mem_prompt: Optional[str] = None,
        custom_categories: Optional[List[str]] = None
    ):
        self.conscious_ingest = conscious_ingest
        self.mem_prompt = mem_prompt
        self.custom_categories = custom_categories or []
        
        # Keywords for different memory categories
        self.category_keywords = {
            MemoryCategory.STORE_AS_FACT: [
                "is", "are", "was", "were", "fact", "information", "data",
                "definition", "means", "called", "known as"
            ],
            MemoryCategory.UPDATE_PREFERENCE: [
                "prefer", "like", "dislike", "want", "need", "always", "never",
                "usually", "typically", "favorite", "settings", "configuration"
            ],
            MemoryCategory.STORE_AS_RULE: [
                "should", "must", "always", "never", "rule", "policy", "guideline",
                "procedure", "process", "workflow", "standard"
            ],
            MemoryCategory.STORE_AS_CONTEXT: [
                "project", "working on", "currently", "building", "developing",
                "context", "background", "situation", "environment"
            ],
            MemoryCategory.DISCARD_TRIVIAL: [
                "hello", "hi", "thanks", "thank you", "bye", "goodbye",
                "weather", "joke", "random", "small talk"
            ]
        }
    
    def process_conversation(
        self,
        chat_id: str,
        user_input: str,
        ai_output: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """
        Process a conversation and extract memory items
        
        Args:
            chat_id: Conversation ID
            user_input: User's input message
            ai_output: AI's response
            filters: Memory filters to apply
            
        Returns:
            List of memory items to store
        """
        memory_items = []
        
        try:
            # Process user input for memory extraction
            user_memories = self._extract_memories_from_text(
                user_input, chat_id, source="user", filters=filters
            )
            memory_items.extend(user_memories)
            
            # Process AI output for memory extraction (facts, rules, etc.)
            ai_memories = self._extract_memories_from_text(
                ai_output, chat_id, source="ai", filters=filters
            )
            memory_items.extend(ai_memories)
            
            logger.debug(f"Processed conversation {chat_id}: {len(memory_items)} memory items")
            return memory_items
            
        except Exception as e:
            logger.error(f"Failed to process conversation {chat_id}: {e}")
            return []
    
    def _extract_memories_from_text(
        self,
        text: str,
        chat_id: str,
        source: str = "user",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """Extract memory items from text"""
        if not text.strip():
            return []
        
        # Apply filters if provided
        if filters and not self._passes_filters(text, filters):
            return []
        
        # Categorize the text
        category = self._categorize_text(text)
        
        if category == MemoryCategory.DISCARD_TRIVIAL:
            return []
        
        # Calculate importance score
        importance = self._calculate_importance(text, category)
        
        # Determine memory type based on category and importance
        memory_type = self._determine_memory_type(category, importance)
        
        # Create memory item
        memory_item = MemoryItem(
            content=text.strip(),
            category=category,
            memory_type=memory_type,
            importance_score=importance,
            metadata={
                "source": source,
                "length": len(text),
                "word_count": len(text.split()),
                "extracted_at": datetime.now().isoformat()
            },
            chat_id=chat_id
        )
        
        return [memory_item]
    
    def _passes_filters(self, text: str, filters: Dict[str, Any]) -> bool:
        """Check if text passes memory filters"""
        text_lower = text.lower()
        
        # Include keywords filter
        if "include_keywords" in filters:
            include_keywords = filters["include_keywords"]
            if not any(keyword.lower() in text_lower for keyword in include_keywords):
                return False
        
        # Exclude keywords filter
        if "exclude_keywords" in filters:
            exclude_keywords = filters["exclude_keywords"]
            if any(keyword.lower() in text_lower for keyword in exclude_keywords):
                return False
        
        # Minimum importance filter
        if "min_importance" in filters:
            importance = self._calculate_importance(text, MemoryCategory.STORE_AS_FACT)
            if importance < filters["min_importance"]:
                return False
        
        return True
    
    def _categorize_text(self, text: str) -> MemoryCategory:
        """
        Categorize text using keyword-based approach
        (In production, this would use an LLM for better accuracy)
        """
        text_lower = text.lower()
        
        # Score each category based on keyword matches
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            category_scores[category] = score
        
        # Return category with highest score, default to STORE_AS_FACT
        if not category_scores or max(category_scores.values()) == 0:
            return MemoryCategory.STORE_AS_FACT
        
        return max(category_scores, key=category_scores.get)
    
    def _calculate_importance(self, text: str, category: MemoryCategory) -> float:
        """Calculate importance score for text"""
        base_score = 0.5
        
        # Length factor (longer text might be more important)
        length_factor = min(len(text) / 200, 0.3)  # Cap at 0.3
        
        # Category factor
        category_factors = {
            MemoryCategory.STORE_AS_FACT: 0.2,
            MemoryCategory.UPDATE_PREFERENCE: 0.3,
            MemoryCategory.STORE_AS_RULE: 0.4,
            MemoryCategory.STORE_AS_CONTEXT: 0.25,
            MemoryCategory.DISCARD_TRIVIAL: -0.5
        }
        
        category_factor = category_factors.get(category, 0.0)
        
        # Keyword importance boost
        important_keywords = [
            "important", "critical", "remember", "key", "essential",
            "never forget", "always", "must", "crucial"
        ]
        
        keyword_boost = 0.0
        text_lower = text.lower()
        for keyword in important_keywords:
            if keyword in text_lower:
                keyword_boost += 0.1
        
        # Calculate final score
        final_score = base_score + length_factor + category_factor + keyword_boost
        
        # Clamp between 0.0 and 1.0
        return max(0.0, min(1.0, final_score))
    
    def _determine_memory_type(self, category: MemoryCategory, importance: float) -> MemoryType:
        """Determine memory type based on category and importance"""
        
        # Rules always go to rules memory
        if category == MemoryCategory.STORE_AS_RULE:
            return MemoryType.RULES
        
        # High importance items go to long-term memory
        if importance >= 0.7:
            return MemoryType.LONG_TERM
        
        # Preferences typically go to long-term memory
        if category == MemoryCategory.UPDATE_PREFERENCE:
            return MemoryType.LONG_TERM
        
        # Everything else goes to short-term memory initially
        return MemoryType.SHORT_TERM
    
    def retrieve_relevant_context(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 5
    ) -> List[str]:
        """
        Retrieve relevant memory IDs for a query
        (Simplified version - in production would use embeddings/vector search)
        """
        # This is a placeholder implementation
        # In production, this would use:
        # 1. Text embeddings for semantic similarity
        # 2. Vector database for efficient retrieval
        # 3. More sophisticated ranking algorithms
        
        # For now, return empty list as database search handles basic keyword matching
        return []
    
    def promote_to_long_term(self, memory_id: str, namespace: str = "default"):
        """Promote a memory from short-term to long-term storage"""
        # This would be implemented to move memories based on access patterns
        pass
    
    def cleanup_expired_memories(self, namespace: str = "default"):
        """Clean up expired short-term memories"""
        # This would be implemented to remove expired memories
        pass