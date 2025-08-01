"""
Retrieval Agent - Intelligent memory retrieval using the memory agent
"""

import json
import openai
from loguru import logger
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.enums import MemoryCategory, MemoryType
from ..utils.exceptions import AgentError


class RetrievalAgent:
    """
    OpenAI-powered retrieval agent that uses the memory agent to understand queries
    and find relevant memories using enum-driven function calling
    """
    
    SYSTEM_PROMPT = """You are a Retrieval Agent - an intelligent system for finding relevant memories based on user queries.

Your job is to:
1. Analyze user queries to understand what information they need
2. Determine which memory categories are most relevant
3. Extract key search terms and concepts
4. Suggest search strategies for finding relevant memories

MEMORY CATEGORIES AVAILABLE:
- fact: Factual information, definitions, technical details, specific data
- preference: User preferences, likes/dislikes, settings, personal choices  
- rule: Rules, policies, procedures, "should/must" statements
- context: Project context, current work, background information

SEARCH STRATEGY TYPES:
- keyword: Find memories containing specific keywords/phrases
- category: Find memories of specific categories
- temporal: Find memories from specific time periods
- importance: Find high-importance memories
- semantic: Find memories semantically related to concepts

Be precise and strategic in your search recommendations."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize Retrieval Agent with OpenAI configuration
        
        Args:
            api_key: OpenAI API key (if None, uses environment variable)
            model: OpenAI model to use for retrieval planning
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
        # Function schema for retrieval planning
        self.retrieval_functions = [{
            "name": "plan_memory_retrieval",
            "description": "Plan memory retrieval strategy for a user query",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_strategies": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "strategy_type": {
                                    "type": "string",
                                    "enum": ["keyword", "category", "temporal", "importance", "semantic"],
                                    "description": "Type of search strategy"
                                },
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "keywords": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Keywords to search for"
                                        },
                                        "categories": {
                                            "type": "array",
                                            "items": {"type": "string", "enum": ["fact", "preference", "rule", "context"]},
                                            "description": "Memory categories to search"
                                        },
                                        "min_importance": {
                                            "type": "number",
                                            "minimum": 0.0,
                                            "maximum": 1.0,
                                            "description": "Minimum importance score"
                                        },
                                        "time_range": {
                                            "type": "string",
                                            "description": "Time range for search (e.g., 'last_week', 'last_month')"
                                        }
                                    }
                                },
                                "priority": {
                                    "type": "number",
                                    "minimum": 1,
                                    "maximum": 10,
                                    "description": "Priority of this search strategy (1-10)"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Why this search strategy is relevant"
                                }
                            },
                            "required": ["strategy_type", "parameters", "priority", "reasoning"]
                        }
                    },
                    "query_intent": {
                        "type": "string",
                        "description": "The interpreted intent of the user's query"
                    }
                },
                "required": ["search_strategies", "query_intent"]
            }
        }]
    
    def plan_retrieval(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Plan retrieval strategy for a user query using OpenAI
        
        Args:
            query: User's query for memory retrieval
            context: Optional additional context
            
        Returns:
            Retrieval plan with search strategies
        """
        try:
            # Prepare the prompt
            prompt = f"User query: {query}"
            if context:
                prompt += f"\nAdditional context: {context}"
            
            # Call OpenAI for retrieval planning
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Plan memory retrieval for this query:\n\n{prompt}"}
                ],
                functions=self.retrieval_functions,
                function_call={"name": "plan_memory_retrieval"},
                temperature=0.1
            )
            
            # Parse function call response
            function_call = response.choices[0].message.function_call
            if not function_call:
                logger.warning(f"No function call in retrieval planning response")
                return {"search_strategies": [], "query_intent": query}
            
            retrieval_plan = json.loads(function_call.arguments)
            
            # Sort strategies by priority
            retrieval_plan["search_strategies"].sort(key=lambda x: x["priority"], reverse=True)
            
            logger.debug(f"Generated retrieval plan with {len(retrieval_plan['search_strategies'])} strategies")
            return retrieval_plan
            
        except Exception as e:
            logger.error(f"Retrieval planning failed: {e}")
            raise AgentError(f"Failed to plan retrieval: {e}")
    
    def build_search_query(self, strategy: Dict[str, Any]) -> str:
        """
        Build a search query string from a strategy
        
        Args:
            strategy: Search strategy from retrieval plan
            
        Returns:
            Search query string
        """
        strategy_type = strategy["strategy_type"]
        params = strategy["parameters"]
        
        if strategy_type == "keyword":
            keywords = params.get("keywords", [])
            return " ".join(keywords)
        
        elif strategy_type == "category":
            # For category searches, we'll need to modify the database search
            # For now, return empty string and handle in database layer
            return ""
        
        elif strategy_type == "semantic":
            keywords = params.get("keywords", [])
            return " ".join(keywords)
        
        else:
            # For other strategy types, combine available keywords
            keywords = params.get("keywords", [])
            return " ".join(keywords) if keywords else ""
    
    def execute_retrieval(
        self, 
        query: str, 
        db_manager, 
        namespace: str = "default",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Execute retrieval using the planned strategies
        
        Args:
            query: User's query
            db_manager: Database manager instance
            namespace: Memory namespace
            limit: Maximum results to return
            
        Returns:
            List of relevant memory items
        """
        try:
            # Plan retrieval
            retrieval_plan = self.plan_retrieval(query)
            
            all_results = []
            seen_memory_ids = set()
            
            # Execute each search strategy
            for strategy in retrieval_plan["search_strategies"]:
                if len(all_results) >= limit:
                    break
                
                strategy_type = strategy["strategy_type"]
                params = strategy["parameters"]
                
                # Build search parameters based on strategy
                search_results = []
                
                if strategy_type == "keyword":
                    search_query = self.build_search_query(strategy)
                    if search_query:
                        search_results = db_manager.search_memories(
                            query=search_query,
                            namespace=namespace,
                            limit=limit - len(all_results)
                        )
                
                elif strategy_type == "category":
                    # Filter by specific categories
                    categories = params.get("categories", [])
                    if categories:
                        # We'll need to modify the search_memories method to support category filtering
                        # For now, do a general search and filter results
                        search_results = db_manager.search_memories(
                            query="",
                            namespace=namespace,
                            limit=limit * 2  # Get more to filter
                        )
                        
                        # Filter by categories
                        search_results = [
                            result for result in search_results
                            if result.get("category") in categories
                        ][:limit - len(all_results)]
                
                elif strategy_type == "importance":
                    min_importance = params.get("min_importance", 0.7)
                    search_results = db_manager.search_memories(
                        query="",
                        namespace=namespace,
                        limit=limit * 2
                    )
                    
                    # Filter by importance
                    search_results = [
                        result for result in search_results
                        if result.get("importance_score", 0) >= min_importance
                    ][:limit - len(all_results)]
                
                # Add unique results
                for result in search_results:
                    memory_id = result.get("memory_id")
                    if memory_id not in seen_memory_ids:
                        seen_memory_ids.add(memory_id)
                        result["retrieval_strategy"] = strategy_type
                        result["strategy_reasoning"] = strategy["reasoning"]
                        all_results.append(result)
                        
                        if len(all_results) >= limit:
                            break
            
            # Sort by importance score
            all_results.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
            
            logger.debug(f"Retrieved {len(all_results)} memories for query: {query}")
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Retrieval execution failed: {e}")
            return []
