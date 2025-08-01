"""
Memory Tool - A tool/function for manual integration with any LLM library
"""

import json
from typing import Dict, Any, List, Optional, Callable
from loguru import logger
from datetime import datetime

from ..core.memory import Memori


class MemoryTool:
    """
    A tool that can be attached to any LLM library for using Memori functionality.
    
    This provides a standardized interface for:
    1. Recording conversations manually
    2. Retrieving relevant context
    3. Getting memory statistics
    """
    
    def __init__(self, memori_instance: Memori):
        """
        Initialize MemoryTool with a Memori instance
        
        Args:
            memori_instance: The Memori instance to use for memory operations
        """
        self.memori = memori_instance
        self.tool_name = "memori_memory"
        self.description = "Access and manage AI conversation memory"
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for function calling in LLMs
        
        Returns:
            Tool schema compatible with OpenAI function calling format
        """
        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["record", "retrieve", "stats", "search"],
                        "description": "Action to perform with memory"
                    },
                    "user_input": {
                        "type": "string",
                        "description": "User's input message (for record action)"
                    },
                    "ai_output": {
                        "type": "string", 
                        "description": "AI's response (for record action)"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model used (for record action)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (for retrieve/search actions)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (for retrieve/search actions)",
                        "default": 5
                    }
                },
                "required": ["action"]
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute a memory tool action
        
        Args:
            action: The action to perform
            **kwargs: Additional parameters based on action
            
        Returns:
            Result of the action
        """
        action = kwargs.get("action")
        
        if action == "record":
            return self._record_conversation(**kwargs)
        elif action == "retrieve":
            return self._retrieve_context(**kwargs)
        elif action == "search":
            return self._search_memories(**kwargs)
        elif action == "stats":
            return self._get_stats(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _record_conversation(self, **kwargs) -> Dict[str, Any]:
        """Record a conversation"""
        try:
            user_input = kwargs.get("user_input", "")
            ai_output = kwargs.get("ai_output", "")
            model = kwargs.get("model", "unknown")
            
            if not user_input or not ai_output:
                return {"error": "Both user_input and ai_output are required for recording"}
            
            chat_id = self.memori.record_conversation(
                user_input=user_input,
                ai_output=ai_output,
                model=model,
                metadata={"tool": "memory_tool", "manual_record": True}
            )
            
            return {
                "success": True,
                "chat_id": chat_id,
                "message": "Conversation recorded successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to record conversation: {e}")
            return {"error": f"Failed to record conversation: {str(e)}"}
    
    def _retrieve_context(self, **kwargs) -> Dict[str, Any]:
        """Retrieve relevant context for a query"""
        try:
            query = kwargs.get("query", "")
            limit = kwargs.get("limit", 5)
            
            if not query:
                return {"error": "Query is required for retrieval"}
            
            context_items = self.memori.retrieve_context(query, limit)
            
            # Format context items for easier consumption
            formatted_context = []
            for item in context_items:
                formatted_context.append({
                    "content": item.get("content", ""),
                    "category": item.get("category", ""),
                    "importance": item.get("importance_score", 0),
                    "created_at": item.get("created_at", ""),
                    "memory_type": item.get("memory_type", "")
                })
            
            return {
                "success": True,
                "query": query,
                "context_count": len(formatted_context),
                "context": formatted_context,
                "message": f"Retrieved {len(formatted_context)} relevant memories"
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return {"error": f"Failed to retrieve context: {str(e)}"}
    
    def _search_memories(self, **kwargs) -> Dict[str, Any]:
        """Search memories by content"""
        try:
            query = kwargs.get("query", "")
            limit = kwargs.get("limit", 10)
            
            if not query:
                return {"error": "Query is required for search"}
            
            search_results = self.memori.db_manager.search_memories(
                query=query,
                namespace=self.memori.namespace,
                limit=limit
            )
            
            return {
                "success": True,
                "query": query,
                "results_count": len(search_results),
                "results": search_results,
                "message": f"Found {len(search_results)} matching memories"
            }
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return {"error": f"Failed to search memories: {str(e)}"}
    
    def _get_stats(self, **kwargs) -> Dict[str, Any]:
        """Get memory and integration statistics"""
        try:
            memory_stats = self.memori.get_memory_stats()
            integration_stats = self.memori.get_integration_stats()
            
            return {
                "success": True,
                "memory_stats": memory_stats,
                "integration_stats": integration_stats,
                "namespace": self.memori.namespace,
                "session_id": self.memori.session_id,
                "enabled": self.memori.is_enabled
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": f"Failed to get stats: {str(e)}"}


# Helper function to create a tool instance
def create_memory_tool(memori_instance: Memori) -> MemoryTool:
    """
    Create a MemoryTool instance
    
    Args:
        memori_instance: The Memori instance to use
        
    Returns:
        MemoryTool instance
    """
    return MemoryTool(memori_instance)


# Function calling interface
def memori_tool_function(memori_instance: Memori, **kwargs) -> Dict[str, Any]:
    """
    Direct function interface for memory operations
    
    This can be used as a function call in LLM libraries that support function calling.
    
    Args:
        memori_instance: The Memori instance to use
        **kwargs: Parameters for the tool action
        
    Returns:
        Result of the memory operation
    """
    tool = MemoryTool(memori_instance)
    return tool.execute(**kwargs)


# Decorator for automatic conversation recording
def record_conversation(memori_instance: Memori):
    """
    Decorator to automatically record LLM conversations
    
    Args:
        memori_instance: The Memori instance to use for recording
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Call the original function
            result = func(*args, **kwargs)
            
            try:
                # Try to extract conversation details from common patterns
                if hasattr(result, 'choices') and result.choices:
                    # OpenAI-style response
                    ai_output = result.choices[0].message.content
                    
                    # Try to find user input in kwargs
                    user_input = ""
                    if 'messages' in kwargs:
                        for msg in reversed(kwargs['messages']):
                            if msg.get('role') == 'user':
                                user_input = msg.get('content', '')
                                break
                    
                    model = kwargs.get('model', 'unknown')
                    
                    if user_input and ai_output:
                        memori_instance.record_conversation(
                            user_input=user_input,
                            ai_output=ai_output,
                            model=model,
                            metadata={"decorator": "record_conversation", "auto_recorded": True}
                        )
                        
            except Exception as e:
                logger.error(f"Failed to auto-record conversation: {e}")
            
            return result
        return wrapper
    return decorator


def create_memory_search_tool(memori_instance: Memori):
    """
    Create memory search tool for LLM function calling (v1.0 architecture)
    
    This creates a search function compatible with OpenAI function calling
    that uses SQL-based memory retrieval.
    
    Args:
        memori_instance: The Memori instance to search
        
    Returns:
        Memory search function for LLM tool use
    """
    
    def memory_search(query: str, max_results: int = 5) -> str:
        """
        Search through stored memories for relevant information
        
        Args:
            query: Search query for memories
            max_results: Maximum number of results to return
            
        Returns:
            JSON string with search results
        """
        try:
            # Use the SQL-based search from the database manager
            results = memori_instance.db_manager.search_memories(
                query=query,
                namespace=memori_instance.namespace,
                limit=max_results
            )
            
            if not results:
                return json.dumps({
                    "found": 0,
                    "message": "No relevant memories found for the query.",
                    "query": query
                })
            
            # Format results according to v1.0 structure
            formatted_results = []
            for result in results:
                try:
                    # Parse the ProcessedMemory JSON
                    memory_data = json.loads(result['processed_data'])
                    
                    formatted_result = {
                        "summary": memory_data.get('summary', ''),
                        "category": memory_data.get('category', {}).get('primary_category', ''),
                        "importance_score": result.get('importance_score', 0.0),
                        "created_at": result.get('created_at', ''),
                        "entities": memory_data.get('entities', {}),
                        "confidence": memory_data.get('category', {}).get('confidence_score', 0.0),
                        "searchable_content": result.get('searchable_content', ''),
                        "retention_type": memory_data.get('importance', {}).get('retention_type', 'short_term')
                    }
                    formatted_results.append(formatted_result)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error parsing memory data: {e}")
                    # Fallback to basic result structure
                    formatted_results.append({
                        "summary": result.get('summary', 'Memory content available'),
                        "category": result.get('category_primary', 'unknown'),
                        "importance_score": result.get('importance_score', 0.0),
                        "created_at": result.get('created_at', '')
                    })
            
            return json.dumps({
                "found": len(formatted_results),
                "query": query,
                "memories": formatted_results,
                "message": f"Found {len(formatted_results)} relevant memories"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return json.dumps({
                "error": f"Memory search failed: {str(e)}",
                "query": query,
                "found": 0
            })
    
    return memory_search