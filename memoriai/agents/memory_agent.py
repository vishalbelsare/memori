"""
Memory Agent - The heart of Memori
OpenAI-powered agent for intelligent memory categorization using enum-driven approach
"""

import json
import openai
from loguru import logger
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.enums import MemoryCategory, MemoryType
from ..utils.exceptions import AgentError
from ..core.database import MemoryItem


class MemoryAgent:
    """
    OpenAI-powered memory agent for intelligent conversation processing and categorization.
    Uses enum-driven function calling for fast, reliable, and cost-effective memory triage.
    """
    
    SYSTEM_PROMPT = """You are a Memory Agent - an intelligent system responsible for analyzing conversations and deciding how to store them in memory.

Your job is to:
1. Analyze user-AI conversations
2. Extract meaningful information 
3. Categorize memories using enum-driven decisions
4. Determine importance and storage type

CATEGORIZATION RULES:
- STORE_AS_FACT: Factual information, definitions, technical details, specific data
- UPDATE_PREFERENCE: User preferences, likes/dislikes, settings, personal choices  
- STORE_AS_RULE: Rules, policies, procedures, "should/must" statements
- STORE_AS_CONTEXT: Project context, current work, background information
- DISCARD_TRIVIAL: Greetings, small talk, jokes, weather, trivial exchanges

IMPORTANCE SCORING (0.0-1.0):
- 0.8-1.0: Critical information that should never be forgotten
- 0.6-0.8: Important information for future reference
- 0.4-0.6: Useful information that might be referenced
- 0.2-0.4: Minor information with limited utility
- 0.0-0.2: Trivial information (usually discarded)

Be decisive, efficient, and consistent. Make single enum decisions without lengthy explanations."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize Memory Agent with OpenAI configuration
        
        Args:
            api_key: OpenAI API key (if None, uses environment variable)
            model: OpenAI model to use for categorization
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
        # Function schema for enum-driven categorization
        self.categorization_functions = [{
            "name": "categorize_memory",
            "description": "Categorize conversation content for memory storage",
            "parameters": {
                "type": "object",
                "properties": {
                    "memories": {
                        "type": "array",
                        "items": {
                            "type": "object", 
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "The memory content to store"
                                },
                                "category": {
                                    "type": "string",
                                    "enum": ["STORE_AS_FACT", "UPDATE_PREFERENCE", "STORE_AS_RULE", 
                                            "STORE_AS_CONTEXT", "DISCARD_TRIVIAL"],
                                    "description": "Memory category classification"
                                },
                                "importance_score": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                    "description": "Importance score from 0.0 to 1.0"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Brief reasoning for categorization"
                                }
                            },
                            "required": ["content", "category", "importance_score", "reasoning"]
                        }
                    }
                },
                "required": ["memories"]
            }
        }]
    
    def process_conversation(
        self,
        chat_id: str,
        user_input: str,
        ai_output: str,
        mem_prompt: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """
        Process a conversation using OpenAI for intelligent categorization
        
        Args:
            chat_id: Conversation ID
            user_input: User's input message
            ai_output: AI's response
            mem_prompt: Optional memory filtering prompt
            filters: Memory filters to apply
            
        Returns:
            List of categorized memory items
        """
        try:
            # Prepare conversation content
            conversation_text = f"User: {user_input}\nAI: {ai_output}"
            
            # Add memory prompt if provided
            system_prompt = self.SYSTEM_PROMPT
            if mem_prompt:
                system_prompt += f"\n\nSPECIAL INSTRUCTIONS: {mem_prompt}"
            
            # Call OpenAI for categorization
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this conversation and categorize memories:\n\n{conversation_text}"}
                ],
                functions=self.categorization_functions,
                function_call={"name": "categorize_memory"},
                temperature=0.1  # Low temperature for consistent categorization
            )
            
            # Parse function call response
            function_call = response.choices[0].message.function_call
            if not function_call:
                logger.warning(f"No function call in response for chat {chat_id}")
                return []
            
            categorization_result = json.loads(function_call.arguments)
            memory_items = []
            
            # Process each categorized memory
            for memory_data in categorization_result.get("memories", []):
                # Apply filters if provided
                if filters and not self._passes_filters(memory_data["content"], filters):
                    continue
                
                # Skip trivial memories
                if memory_data["category"] == "DISCARD_TRIVIAL":
                    continue
                
                # Convert category string to enum
                try:
                    category = MemoryCategory(memory_data["category"].lower().replace("store_as_", "").replace("update_", ""))
                except ValueError:
                    logger.warning(f"Unknown category: {memory_data['category']}")
                    continue
                
                # Determine memory type
                memory_type = self._determine_memory_type(category, memory_data["importance_score"])
                
                # Create memory item
                memory_item = MemoryItem(
                    content=memory_data["content"],
                    category=category,
                    memory_type=memory_type,
                    importance_score=memory_data["importance_score"],
                    metadata={
                        "reasoning": memory_data["reasoning"],
                        "source": "memory_agent",
                        "model": self.model,
                        "processed_at": datetime.now().isoformat()
                    },
                    chat_id=chat_id
                )
                
                memory_items.append(memory_item)
            
            logger.debug(f"Processed conversation {chat_id}: {len(memory_items)} memory items")
            return memory_items
            
        except Exception as e:
            logger.error(f"Memory agent processing failed for {chat_id}: {e}")
            raise AgentError(f"Failed to process conversation: {e}")
    
    def _passes_filters(self, content: str, filters: Dict[str, Any]) -> bool:
        """Check if content passes memory filters"""
        content_lower = content.lower()
        
        # Include keywords filter
        if "include_keywords" in filters:
            include_keywords = filters["include_keywords"]
            if not any(keyword.lower() in content_lower for keyword in include_keywords):
                return False
        
        # Exclude keywords filter
        if "exclude_keywords" in filters:
            exclude_keywords = filters["exclude_keywords"]
            if any(keyword.lower() in content_lower for keyword in exclude_keywords):
                return False
        
        return True
    
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
