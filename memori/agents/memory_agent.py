"""
Memory Agent - Async Pydantic-based conversation processing

This agent processes conversations and extracts structured information with
enhanced classification and conscious context detection.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import openai
from loguru import logger

if TYPE_CHECKING:
    from ..core.providers import ProviderConfig

from ..utils.pydantic_models import (
    ConversationContext,
    MemoryClassification,
    MemoryImportanceLevel,
    ProcessedLongTermMemory,
)


class MemoryAgent:
    """
    Async Memory Agent for processing conversations with enhanced classification
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider_config: Optional["ProviderConfig"] = None,
    ):
        """
        Initialize Memory Agent with LLM provider configuration

        Args:
            api_key: API key (deprecated, use provider_config)
            model: Model to use for structured output (defaults to 'gpt-4o' if not specified)
            provider_config: Provider configuration for LLM client
        """
        if provider_config:
            # Use provider configuration to create clients
            self.client = provider_config.create_client()
            self.async_client = provider_config.create_async_client()
            # Use provided model, fallback to provider config model, then default to gpt-4o
            self.model = model or provider_config.model or "gpt-4o"
        else:
            # Backward compatibility: use api_key directly
            self.client = openai.OpenAI(api_key=api_key)
            self.async_client = openai.AsyncOpenAI(api_key=api_key)
            self.model = model or "gpt-4o"

    SYSTEM_PROMPT = """You are an advanced Memory Processing Agent responsible for analyzing conversations and extracting structured information with intelligent classification and conscious context detection.

Your primary functions:
1. **Intelligent Classification**: Categorize memories with enhanced classification system
2. **Conscious Context Detection**: Identify user context information for immediate promotion
3. **Entity Extraction**: Extract comprehensive entities and keywords
4. **Deduplication**: Identify and handle duplicate information
5. **Context Filtering**: Determine what should be stored vs filtered out

**ENHANCED CLASSIFICATION SYSTEM:**

**CONSCIOUS_INFO** (Auto-promote to short-term context):
- User's name, location, job, personal details
- Current projects, technologies they work with
- Preferences, work style, communication style
- Skills, expertise, learning goals
- Important personal context for AI interaction

**ESSENTIAL**:
- Core facts that define user's context
- Important preferences and opinions
- Key skills and knowledge areas
- Critical project information

**CONTEXTUAL**:
- Current work context
- Ongoing projects and goals
- Environmental setup and tools

**CONVERSATIONAL**:
- Regular discussions and questions
- Explanations and clarifications
- Problem-solving conversations

**REFERENCE**:
- Code examples and technical references
- Documentation and resources
- Learning materials

**PERSONAL**:
- Life events and personal information
- Relationships and social context
- Personal interests and hobbies

**IMPORTANCE LEVELS:**
- **CRITICAL**: Must never be lost
- **HIGH**: Very important for context
- **MEDIUM**: Useful to remember
- **LOW**: Nice to have context

**CONSCIOUS CONTEXT DETECTION:**
Mark is_user_context=True for:
- Personal identifiers (name, location, role)
- Work context (job, company, projects)
- Technical preferences (languages, tools, frameworks)
- Communication style and preferences
- Skills and expertise areas
- Learning goals and interests

Set promotion_eligible=True for memories that should be immediately available in short-term context for all future conversations.

**PROCESSING RULES:**
1. AVOID DUPLICATES: Check if similar information already exists
2. MERGE SIMILAR: Combine related information when appropriate
3. FILTER UNNECESSARY: Skip trivial greetings, acknowledgments
4. EXTRACT ENTITIES: Identify people, places, technologies, projects
5. ASSESS IMPORTANCE: Rate based on relevance to user context
6. FLAG USER CONTEXT: Mark information for conscious promotion

Focus on extracting information that would genuinely help provide better context and assistance in future conversations."""

    async def process_conversation_async(
        self,
        chat_id: str,
        user_input: str,
        ai_output: str,
        context: Optional[ConversationContext] = None,
        existing_memories: Optional[List[str]] = None,
    ) -> ProcessedLongTermMemory:
        """
        Async conversation processing with classification and conscious context detection

        Args:
            chat_id: Conversation ID
            user_input: User's input message
            ai_output: AI's response
            context: Additional conversation context
            existing_memories: List of existing memory summaries for deduplication

        Returns:
            Processed memory with classification and conscious flags
        """
        try:
            # Prepare conversation content
            conversation_text = f"User: {user_input}\nAssistant: {ai_output}"

            # Build system prompt
            system_prompt = self.SYSTEM_PROMPT

            # Add deduplication context
            if existing_memories:
                dedup_context = (
                    "\n\nEXISTING MEMORIES (for deduplication):\n"
                    + "\n".join(existing_memories[:10])
                )
                system_prompt += dedup_context

            # Prepare context information
            context_info = ""
            if context:
                context_info = f"""
CONVERSATION CONTEXT:
- Session: {context.session_id}
- Model: {context.model_used}
- User Projects: {', '.join(context.current_projects) if context.current_projects else 'None specified'}
- Relevant Skills: {', '.join(context.relevant_skills) if context.relevant_skills else 'None specified'}
- Topic Thread: {context.topic_thread or 'General conversation'}
"""

            # Call OpenAI Structured Outputs (async)
            completion = await self.async_client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Process this conversation for enhanced memory storage:\n\n{conversation_text}\n{context_info}",
                    },
                ],
                response_format=ProcessedLongTermMemory,
                temperature=0.1,  # Low temperature for consistent processing
            )

            # Handle potential refusal
            if completion.choices[0].message.refusal:
                logger.warning(
                    f"Memory processing refused for chat {chat_id}: {completion.choices[0].message.refusal}"
                )
                return self._create_empty_long_term_memory(
                    chat_id, "Processing refused for safety reasons"
                )

            processed_memory = completion.choices[0].message.parsed
            processed_memory.conversation_id = chat_id
            processed_memory.extraction_timestamp = datetime.now()

            logger.debug(
                f"Processed conversation {chat_id}: "
                f"classification={processed_memory.classification}, "
                f"importance={processed_memory.importance}, "
                f"conscious_context={processed_memory.is_user_context}, "
                f"promotion_eligible={processed_memory.promotion_eligible}"
            )

            return processed_memory

        except Exception as e:
            logger.error(f"Memory agent processing failed for {chat_id}: {e}")
            return self._create_empty_long_term_memory(
                chat_id, f"Processing failed: {str(e)}"
            )

    def _create_empty_long_term_memory(
        self, chat_id: str, reason: str
    ) -> ProcessedLongTermMemory:
        """Create an empty long-term memory object for error cases"""
        return ProcessedLongTermMemory(
            content="Processing failed",
            summary="Processing failed",
            classification=MemoryClassification.CONVERSATIONAL,
            importance=MemoryImportanceLevel.LOW,
            conversation_id=chat_id,
            classification_reason=reason,
            confidence_score=0.0,
            extraction_timestamp=datetime.now(),
        )

    # === DEDUPLICATION & FILTERING METHODS ===

    async def detect_duplicates(
        self,
        new_memory: ProcessedLongTermMemory,
        existing_memories: List[ProcessedLongTermMemory],
        similarity_threshold: float = 0.8,
    ) -> Optional[str]:
        """
        Detect if new memory is a duplicate of existing memories

        Args:
            new_memory: New memory to check
            existing_memories: List of existing memories to compare against
            similarity_threshold: Threshold for considering memories similar

        Returns:
            Memory ID of duplicate if found, None otherwise
        """
        # Simple text similarity check - could be enhanced with embeddings
        new_content = new_memory.content.lower().strip()
        new_summary = new_memory.summary.lower().strip()

        for existing in existing_memories:
            existing_content = existing.content.lower().strip()
            existing_summary = existing.summary.lower().strip()

            # Check content similarity
            content_similarity = self._calculate_similarity(
                new_content, existing_content
            )
            summary_similarity = self._calculate_similarity(
                new_summary, existing_summary
            )

            # Average similarity score
            avg_similarity = (content_similarity + summary_similarity) / 2

            if avg_similarity >= similarity_threshold:
                logger.info(
                    f"Duplicate detected: {avg_similarity:.2f} similarity with {existing.conversation_id}"
                )
                return existing.conversation_id

        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Simple text similarity calculation using word overlap
        Could be enhanced with more sophisticated methods
        """
        if not text1 or not text2:
            return 0.0

        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def should_filter_memory(
        self, memory: ProcessedLongTermMemory, filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if memory should be filtered out

        Args:
            memory: Memory to check
            filters: Optional filtering criteria

        Returns:
            True if memory should be filtered out, False otherwise
        """
        if not filters:
            return False

        # Classification filter
        if "exclude_classifications" in filters:
            if memory.classification in filters["exclude_classifications"]:
                return True

        # Importance filter
        if "min_importance" in filters:
            importance_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}

            min_level = importance_map.get(filters["min_importance"], 1)
            memory_level = importance_map.get(memory.importance, 1)

            if memory_level < min_level:
                return True

        # Confidence filter
        if "min_confidence" in filters:
            if memory.confidence_score < filters["min_confidence"]:
                return True

        # Content filters
        if "exclude_keywords" in filters:
            content_lower = memory.content.lower()
            if any(
                keyword.lower() in content_lower
                for keyword in filters["exclude_keywords"]
            ):
                return True

        # Length filter
        if "min_content_length" in filters:
            if len(memory.content.strip()) < filters["min_content_length"]:
                return True

        return False