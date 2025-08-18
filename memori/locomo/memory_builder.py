"""
Memory Builder for LOCOMO Benchmark

Converts LOCOMO conversation data into Memori's ProcessedMemory format
without requiring LLM API calls for faster benchmarking.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from ..utils.pydantic_models import (
    ExtractedEntities,
    ExtractedEntity,
    EntityType,
    MemoryCategory,
    MemoryCategoryType, 
    MemoryImportance,
    ProcessedMemory,
    RetentionType,
)
from .data_models import LocomoConversation, LocomoDialogueTurn, LocomoSession


class LocomoMemoryBuilder:
    """
    Builds ProcessedMemory objects from LOCOMO conversation data using rule-based processing.
    This avoids expensive LLM API calls during benchmarking while creating realistic memory objects.
    """
    
    def __init__(self):
        """Initialize the memory builder with extraction patterns and rules"""
        
        # Entity extraction patterns
        self.name_patterns = [
            r'\b[A-Z][a-z]+\b',  # Capitalized words (potential names)
        ]
        
        self.technology_keywords = {
            'programming', 'python', 'javascript', 'react', 'node', 'database', 'sql', 
            'machine learning', 'ai', 'api', 'web', 'mobile', 'app', 'software',
            'framework', 'library', 'tool', 'platform', 'service'
        }
        
        self.skill_keywords = {
            'learn', 'study', 'practice', 'good at', 'expert', 'skill', 'ability',
            'competent', 'proficient', 'experienced', 'training', 'course', 'certification'
        }
        
        self.preference_keywords = {
            'like', 'love', 'hate', 'dislike', 'prefer', 'favorite', 'enjoy', 'want',
            'wish', 'hope', 'interested', 'passionate', 'excited'
        }
        
        self.rule_keywords = {
            'should', 'must', 'need to', 'have to', 'required', 'policy', 'rule',
            'guideline', 'procedure', 'process', 'standard', 'requirement'
        }
        
        self.fact_keywords = {
            'is', 'was', 'will be', 'happened', 'occurred', 'fact', 'true',
            'actually', 'really', 'indeed', 'definitely', 'certainly'
        }
    
    def extract_entities_from_text(self, text: str) -> ExtractedEntities:
        """Extract entities from conversation text using pattern matching"""
        
        text_lower = text.lower()
        
        # Extract people (capitalized words)
        people = []
        for pattern in self.name_patterns:
            matches = re.findall(pattern, text)
            people.extend([match for match in matches if len(match) > 2])
        
        # Extract technologies
        technologies = []
        for tech in self.technology_keywords:
            if tech in text_lower:
                technologies.append(tech)
        
        # Extract skills
        skills = []
        for skill in self.skill_keywords:
            if skill in text_lower:
                skills.append(skill)
        
        # Extract topics (simple keyword extraction)
        topics = []
        
        # Extract projects (mentions of work, project, initiative)
        projects = []
        project_patterns = [r'project \w+', r'working on \w+', r'\w+ initiative']
        for pattern in project_patterns:
            matches = re.findall(pattern, text_lower)
            projects.extend(matches)
        
        # Extract keywords (important terms)
        keywords = []
        # Extract words that appear in multiple sentences or are emphasized
        words = re.findall(r'\b\w{4,}\b', text_lower)
        word_counts = {}
        for word in words:
            if word not in {'that', 'this', 'with', 'have', 'been', 'they', 'were', 'when', 'what', 'where'}:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        keywords = [word for word, count in word_counts.items() if count > 1][:5]
        
        return ExtractedEntities(
            people=list(set(people)),
            technologies=list(set(technologies)),
            topics=list(set(topics)),
            skills=list(set(skills)),
            projects=list(set(projects)),
            keywords=list(set(keywords))
        )
    
    def categorize_memory(self, text: str) -> MemoryCategory:
        """Categorize memory content based on keyword analysis"""
        
        text_lower = text.lower()
        
        # Score each category based on keyword presence
        category_scores = {
            MemoryCategoryType.preference: 0,
            MemoryCategoryType.skill: 0,
            MemoryCategoryType.fact: 0,
            MemoryCategoryType.context: 0,
            MemoryCategoryType.rule: 0,
        }
        
        # Check preference keywords
        for keyword in self.preference_keywords:
            if keyword in text_lower:
                category_scores[MemoryCategoryType.preference] += 1
        
        # Check skill keywords  
        for keyword in self.skill_keywords:
            if keyword in text_lower:
                category_scores[MemoryCategoryType.skill] += 1
        
        # Check fact keywords
        for keyword in self.fact_keywords:
            if keyword in text_lower:
                category_scores[MemoryCategoryType.fact] += 1
        
        # Check rule keywords
        for keyword in self.rule_keywords:
            if keyword in text_lower:
                category_scores[MemoryCategoryType.rule] += 1
        
        # Default to context for general conversation
        category_scores[MemoryCategoryType.context] += 1
        
        # Select category with highest score
        primary_category = max(category_scores.keys(), key=lambda k: category_scores[k])
        confidence_score = min(0.9, max(0.3, category_scores[primary_category] / 3))
        
        # Generate reasoning
        reasoning_map = {
            MemoryCategoryType.preference: "Contains preference or opinion indicators",
            MemoryCategoryType.skill: "Contains skill or learning related content",
            MemoryCategoryType.fact: "Contains factual information or statements",
            MemoryCategoryType.context: "General conversational context",
            MemoryCategoryType.rule: "Contains rules or procedural information"
        }
        
        return MemoryCategory(
            primary_category=primary_category,
            confidence_score=confidence_score,
            reasoning=reasoning_map[primary_category]
        )
    
    def assess_importance(self, text: str, turn_position: int, total_turns: int) -> MemoryImportance:
        """Assess memory importance based on content and position in conversation"""
        
        text_lower = text.lower()
        
        # Base importance score
        importance_score = 0.5
        
        # Increase importance for emotional content
        emotional_words = {'love', 'hate', 'excited', 'worried', 'happy', 'sad', 'angry', 'surprised'}
        for word in emotional_words:
            if word in text_lower:
                importance_score += 0.1
        
        # Increase importance for questions and answers
        if '?' in text or text_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who')):
            importance_score += 0.1
        
        # Increase importance for specific facts
        if any(word in text_lower for word in ['date', 'time', 'place', 'number']):
            importance_score += 0.15
        
        # Increase importance for first and last parts of conversation
        if turn_position < total_turns * 0.2 or turn_position > total_turns * 0.8:
            importance_score += 0.05
        
        # Cap at 1.0
        importance_score = min(1.0, importance_score)
        
        # Determine retention type
        if importance_score >= 0.8:
            retention_type = RetentionType.permanent
        elif importance_score >= 0.6:
            retention_type = RetentionType.long_term
        else:
            retention_type = RetentionType.short_term
        
        # Generate reasoning
        reasoning_parts = []
        if importance_score >= 0.8:
            reasoning_parts.append("high emotional or factual significance")
        if '?' in text:
            reasoning_parts.append("contains question/answer")
        if any(word in text_lower for word in ['date', 'time', 'place']):
            reasoning_parts.append("contains specific details")
        
        reasoning = "Memory rated for " + (", ".join(reasoning_parts) if reasoning_parts else "general conversation content")
        
        return MemoryImportance(
            importance_score=importance_score,
            retention_type=retention_type,
            reasoning=reasoning,
            novelty_score=min(0.9, max(0.3, len(set(text.lower().split())) / len(text.split()))),
            relevance_score=importance_score * 0.9,
            actionability_score=0.6 if '?' in text or any(word in text_lower for word in self.rule_keywords) else 0.4
        )
    
    def create_searchable_content(self, turns: List[LocomoDialogueTurn]) -> Tuple[str, str, List[str]]:
        """Create summary, searchable content, and key insights from dialogue turns"""
        
        # Combine all text
        full_text = " ".join(turn.text for turn in turns)
        
        # Create summary (first few sentences + key elements)
        sentences = re.split(r'[.!?]+', full_text)
        summary_sentences = [s.strip() for s in sentences[:3] if s.strip()]
        summary = ". ".join(summary_sentences) + "."
        
        # Create searchable content (add speaker names and key terms)
        speakers = list(set(turn.speaker for turn in turns))
        searchable_parts = [
            f"Conversation between {' and '.join(speakers)}",
            full_text,
        ]
        
        # Add extracted keywords for searchability
        entities = self.extract_entities_from_text(full_text)
        searchable_parts.extend(entities.keywords)
        searchable_parts.extend(entities.people)
        searchable_parts.extend(entities.technologies)
        
        searchable_content = " ".join(searchable_parts)
        
        # Extract key insights (questions, emotions, important statements)
        key_insights = []
        for turn in turns:
            if '?' in turn.text:
                key_insights.append(f"Question: {turn.text}")
            elif any(word in turn.text.lower() for word in ['important', 'remember', 'need to', 'should']):
                key_insights.append(f"Important: {turn.text}")
        
        return summary[:500], searchable_content[:1000], key_insights[:5]
    
    def build_memory_from_turns(self, turns: List[LocomoDialogueTurn], session_id: str, conversation_id: str) -> ProcessedMemory:
        """Build a ProcessedMemory object from a group of dialogue turns"""
        
        if not turns:
            raise ValueError("Cannot build memory from empty turns list")
        
        # Combine text from all turns
        combined_text = " ".join(turn.text for turn in turns)
        
        # Extract components
        category = self.categorize_memory(combined_text)
        entities = self.extract_entities_from_text(combined_text)
        importance = self.assess_importance(combined_text, len(turns), 100)  # Assume ~100 total turns
        summary, searchable_content, key_insights = self.create_searchable_content(turns)
        
        # Determine storage decision
        should_store = importance.importance_score >= 0.3
        storage_reasoning = (
            f"Memory scored {importance.importance_score:.2f} - "
            f"{'storing' if should_store else 'not storing'} based on importance threshold"
        )
        
        # Add conversation metadata
        processing_metadata = {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "turn_count": str(len(turns)),
            "speakers": ", ".join(set(turn.speaker for turn in turns)),
            "source": "locomo_benchmark"
        }
        
        return ProcessedMemory(
            category=category,
            entities=entities,
            importance=importance,
            summary=summary,
            searchable_content=searchable_content,
            key_insights=key_insights,
            should_store=should_store,
            storage_reasoning=storage_reasoning,
            timestamp=datetime.now(),
            processing_metadata=processing_metadata
        )
    
    def build_memories_from_session(self, session: LocomoSession, conversation_id: str, 
                                  chunk_size: int = 5) -> List[ProcessedMemory]:
        """
        Build multiple ProcessedMemory objects from a conversation session by chunking turns
        
        Args:
            session: The conversation session to process
            conversation_id: ID of the parent conversation
            chunk_size: Number of turns to group into each memory
            
        Returns:
            List of ProcessedMemory objects
        """
        
        memories = []
        
        # Chunk turns into groups
        for i in range(0, len(session.turns), chunk_size):
            chunk_turns = session.turns[i:i+chunk_size]
            
            if chunk_turns:  # Skip empty chunks
                try:
                    memory = self.build_memory_from_turns(
                        chunk_turns, 
                        session.session_id, 
                        conversation_id
                    )
                    memories.append(memory)
                except Exception as e:
                    # Log error but continue processing
                    print(f"Warning: Failed to build memory from turns {i}-{i+len(chunk_turns)}: {e}")
                    continue
        
        return memories
    
    def build_memories_from_conversation(self, conversation: LocomoConversation, 
                                       conversation_id: Optional[str] = None) -> List[ProcessedMemory]:
        """
        Build all ProcessedMemory objects from a complete LOCOMO conversation
        
        Args:
            conversation: The LOCOMO conversation to process
            conversation_id: Optional conversation identifier
            
        Returns:
            List of all ProcessedMemory objects for the conversation
        """
        
        if conversation_id is None:
            conversation_id = f"{conversation.speaker_a}_{conversation.speaker_b}"
        
        all_memories = []
        
        for session in conversation.sessions:
            session_memories = self.build_memories_from_session(session, conversation_id)
            all_memories.extend(session_memories)
        
        return all_memories


def build_locomo_memories(conversation: LocomoConversation, conversation_id: Optional[str] = None) -> List[ProcessedMemory]:
    """
    Convenience function to build ProcessedMemory objects from a LOCOMO conversation
    
    Args:
        conversation: LOCOMO conversation to process  
        conversation_id: Optional conversation identifier
        
    Returns:
        List of ProcessedMemory objects
    """
    builder = LocomoMemoryBuilder()
    return builder.build_memories_from_conversation(conversation, conversation_id)


if __name__ == "__main__":
    # Test the memory builder
    from .data_loader import load_locomo_dataset
    
    try:
        dataset = load_locomo_dataset()
        builder = LocomoMemoryBuilder()
        
        # Test with first conversation
        if dataset.conversations:
            conversation = dataset.conversations[0]
            memories = builder.build_memories_from_conversation(conversation, "test_conv_1")
            
            print(f"Built {len(memories)} memory objects from conversation")
            print(f"Speakers: {conversation.speaker_a} & {conversation.speaker_b}")
            print(f"Sessions: {len(conversation.sessions)}")
            print(f"Total turns: {conversation.total_turns}")
            
            # Show first memory as example
            if memories:
                memory = memories[0]
                print(f"\nExample memory:")
                print(f"Category: {memory.category.primary_category}")
                print(f"Importance: {memory.importance.importance_score:.2f}")
                print(f"Summary: {memory.summary[:100]}...")
                print(f"Should store: {memory.should_store}")
        else:
            print("No conversations found in dataset")
            
    except Exception as e:
        print(f"Failed to test memory builder: {e}")
        raise