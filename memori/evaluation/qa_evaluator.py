"""
Question-Answering Evaluator for LOCOMO Benchmark

Evaluates Memori's ability to answer questions from stored conversational memories
across all 5 LOCOMO question types: Single-hop, Multi-hop, Temporal, Open-domain, Adversarial.
"""

import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import openai
from loguru import logger

from ..agents.retrieval_agent import MemorySearchEngine
from ..core.database import DatabaseManager
from ..locomo.data_models import LOCOMO_QUESTION_CATEGORIES, LocomoQAItem
from ..utils.pydantic_models import MemoryCategoryType


class LocomoQAEvaluator:
    """
    Evaluates question-answering performance using Memori's stored memories.
    Tests all 5 LOCOMO question types with proper retrieval strategies.
    """
    
    def __init__(self, database_manager: DatabaseManager, search_engine: MemorySearchEngine, 
                 namespace: str = "locomo_benchmark"):
        """
        Initialize QA evaluator
        
        Args:
            database_manager: Memori database manager
            search_engine: Memory search engine for retrieval
            namespace: Namespace for benchmark data
        """
        self.db_manager = database_manager
        self.search_engine = search_engine
        self.namespace = namespace
        
        # OpenAI client for answer generation and evaluation
        self.openai_client = openai.OpenAI()
        
        # Performance tracking
        self.query_times = []
        self.token_usage = []
        
    def search_memories(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for relevant memories using multiple strategies
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant memory records
        """
        start_time = time.time()
        
        try:
            # Get search plan from the search engine
            search_plan = self.search_engine.plan_search(query)
            
            with self.db_manager._get_connection() as conn:
                memories = []
                
                # Strategy 1: FTS search
                if "keyword_search" in search_plan.search_strategy or "semantic_search" in search_plan.search_strategy:
                    # Create FTS5-compatible query by extracting keywords
                    fts_words = re.findall(r'\w+', query.lower())
                    fts_query = ' '.join(fts_words[:5])  # Limit to first 5 words to avoid syntax issues
                    
                    if fts_query:  # Only search if we have valid words
                        fts_results = conn.execute("""
                            SELECT m.*, s.searchable_content, s.summary, s.processed_data, 'short_term' as memory_type
                            FROM memory_search_fts m
                            JOIN short_term_memory s ON m.memory_id = s.memory_id
                            WHERE m.namespace = ? AND memory_search_fts MATCH ?
                            ORDER BY rank
                            LIMIT ?
                        """, (self.namespace, fts_query, max_results // 2)).fetchall()
                    else:
                        fts_results = []
                    
                    memories.extend([dict(row) for row in fts_results])
                    
                    # Also search long-term memories
                    if fts_query:  # Only search if we have valid words
                        fts_lt_results = conn.execute("""
                            SELECT m.*, l.searchable_content, l.summary, l.processed_data, 'long_term' as memory_type
                            FROM memory_search_fts m
                            JOIN long_term_memory l ON m.memory_id = l.memory_id  
                            WHERE m.namespace = ? AND memory_search_fts MATCH ?
                            ORDER BY rank
                            LIMIT ?
                        """, (self.namespace, fts_query, max_results // 2)).fetchall()
                        
                        memories.extend([dict(row) for row in fts_lt_results])
                
                # Strategy 2: Entity-based search
                if "entity_search" in search_plan.search_strategy:
                    for entity_filter in search_plan.entity_filters:
                        entity_results = conn.execute("""
                            SELECT m.memory_id, m.memory_type, m.searchable_content, m.summary, m.processed_data,
                                   e.entity_value, e.entity_type, e.relevance_score
                            FROM memory_entities e
                            JOIN (
                                SELECT memory_id, searchable_content, summary, processed_data, 'short_term' as memory_type
                                FROM short_term_memory WHERE namespace = ?
                                UNION ALL
                                SELECT memory_id, searchable_content, summary, processed_data, 'long_term' as memory_type  
                                FROM long_term_memory WHERE namespace = ?
                            ) m ON e.memory_id = m.memory_id
                            WHERE e.namespace = ? AND e.entity_value LIKE ?
                            ORDER BY e.relevance_score DESC
                            LIMIT ?
                        """, (self.namespace, self.namespace, self.namespace, f"%{entity_filter}%", max_results // 3)).fetchall()
                        
                        memories.extend([dict(row) for row in entity_results])
                
                # Strategy 3: Category-based search  
                if search_plan.category_filters:
                    for category in search_plan.category_filters:
                        category_results = conn.execute("""
                            SELECT memory_id, searchable_content, summary, processed_data, 
                                   'short_term' as memory_type, importance_score
                            FROM short_term_memory 
                            WHERE namespace = ? AND category_primary = ?
                            ORDER BY importance_score DESC
                            LIMIT ?
                        """, (self.namespace, category.value, max_results // 4)).fetchall()
                        
                        memories.extend([dict(row) for row in category_results])
                        
                        # Also search long-term
                        category_lt_results = conn.execute("""
                            SELECT memory_id, searchable_content, summary, processed_data,
                                   'long_term' as memory_type, importance_score
                            FROM long_term_memory
                            WHERE namespace = ? AND category_primary = ?  
                            ORDER BY importance_score DESC
                            LIMIT ?
                        """, (self.namespace, category.value, max_results // 4)).fetchall()
                        
                        memories.extend([dict(row) for row in category_lt_results])
                
                # Fallback: High-importance memories
                if not memories:
                    fallback_results = conn.execute("""
                        SELECT memory_id, searchable_content, summary, processed_data, 
                               'short_term' as memory_type, importance_score
                        FROM short_term_memory
                        WHERE namespace = ? AND importance_score >= ?
                        ORDER BY importance_score DESC
                        LIMIT ?
                    """, (self.namespace, search_plan.min_importance, max_results)).fetchall()
                    
                    memories.extend([dict(row) for row in fallback_results])
                
                # Remove duplicates and sort by relevance
                unique_memories = {}
                for memory in memories:
                    memory_id = memory['memory_id']
                    if memory_id not in unique_memories:
                        unique_memories[memory_id] = memory
                
                sorted_memories = sorted(
                    unique_memories.values(),
                    key=lambda x: x.get('importance_score', 0.5),
                    reverse=True
                )[:max_results]
                
                search_time = time.time() - start_time
                self.query_times.append(search_time)
                
                logger.debug(f"Found {len(sorted_memories)} memories for query: {query[:50]}...")
                return sorted_memories
                
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []
    
    def generate_answer(self, question: str, retrieved_memories: List[Dict], 
                       question_category: int) -> Tuple[str, Dict]:
        """
        Generate answer using retrieved memories and OpenAI
        
        Args:
            question: Question to answer
            retrieved_memories: Retrieved memory contexts
            question_category: LOCOMO question category (1-5)
            
        Returns:
            Tuple of (answer, metadata)
        """
        start_time = time.time()
        
        # Prepare context from memories
        context_parts = []
        for i, memory in enumerate(retrieved_memories[:5]):  # Limit context size
            summary = memory.get('summary', '')
            searchable_content = memory.get('searchable_content', '')
            
            context_parts.append(f"Memory {i+1}: {summary}\nDetails: {searchable_content[:200]}...")
        
        context = "\n\n".join(context_parts)
        
        # Category-specific prompting
        category_name = LOCOMO_QUESTION_CATEGORIES.get(question_category, "unknown")
        
        if category_name == "single_hop":
            instruction = "Answer based on information from a single memory or conversation session."
        elif category_name == "multi_hop":
            instruction = "Answer by synthesizing information from multiple memories/sessions."
        elif category_name == "temporal":
            instruction = "Answer with attention to time, dates, and temporal relationships."
        elif category_name == "open_domain":
            instruction = "Answer using both the provided memories and your general knowledge."
        elif category_name == "adversarial":
            instruction = "Be very careful - this question may be designed to mislead. Answer accurately based on the evidence."
        else:
            instruction = "Answer the question based on the provided memory context."
        
        prompt = f"""Based on the conversation memories provided below, answer the following question.

Question Type: {category_name}
Instructions: {instruction}

Question: {question}

Relevant Memories:
{context}

Important: 
- Only answer based on information present in the memories
- If the information is not available, say "Information not found in memories"
- Be precise and cite specific details when possible
- For temporal questions, pay attention to dates and time references
- For adversarial questions, double-check the evidence carefully

Answer:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise question-answering assistant that answers based strictly on provided memory context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1  # Low temperature for consistency
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Track token usage
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            self.token_usage.append(token_usage)
            
            generation_time = time.time() - start_time
            
            metadata = {
                "category": category_name,
                "memories_used": len(retrieved_memories),
                "generation_time": generation_time,
                "token_usage": token_usage,
                "context_length": len(context)
            }
            
            return answer, metadata
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return "Error generating answer", {"error": str(e)}
    
    def evaluate_single_qa(self, qa_item: LocomoQAItem) -> Dict:
        """
        Evaluate a single QA item
        
        Args:
            qa_item: LOCOMO QA item to evaluate
            
        Returns:
            Evaluation results
        """
        start_time = time.time()
        
        # Search for relevant memories
        retrieved_memories = self.search_memories(qa_item.question, max_results=10)
        
        # Generate answer
        generated_answer, metadata = self.generate_answer(
            qa_item.question, retrieved_memories, qa_item.category
        )
        
        # Compare with ground truth
        correct_answer = qa_item.answer
        adversarial_answer = qa_item.adversarial_answer
        
        # Simple exact match evaluation
        exact_match = False
        if correct_answer and generated_answer:
            # Normalize for comparison
            correct_normalized = str(correct_answer).lower().strip()
            generated_normalized = generated_answer.lower().strip()
            exact_match = correct_normalized in generated_normalized or generated_normalized in correct_normalized
        
        # Partial match evaluation
        partial_match = False
        if correct_answer and generated_answer:
            correct_tokens = set(re.findall(r'\w+', str(correct_answer).lower()))
            generated_tokens = set(re.findall(r'\w+', generated_answer.lower()))
            
            if correct_tokens and generated_tokens:
                overlap = len(correct_tokens.intersection(generated_tokens))
                partial_match = overlap / len(correct_tokens) >= 0.5
        
        # Check if answer is adversarial (wrong answer)
        adversarial_match = False
        if adversarial_answer and generated_answer:
            adv_normalized = adversarial_answer.lower().strip()
            generated_normalized = generated_answer.lower().strip()
            adversarial_match = adv_normalized in generated_normalized or generated_normalized in adv_normalized
        
        total_time = time.time() - start_time
        
        result = {
            "question": qa_item.question,
            "correct_answer": correct_answer,
            "adversarial_answer": adversarial_answer,
            "generated_answer": generated_answer,
            "category": qa_item.category,
            "category_name": LOCOMO_QUESTION_CATEGORIES.get(qa_item.category, "unknown"),
            "exact_match": exact_match,
            "partial_match": partial_match,
            "adversarial_match": adversarial_match,
            "evidence_ids": qa_item.evidence,
            "memories_retrieved": len(retrieved_memories),
            "total_evaluation_time": total_time,
            "metadata": metadata
        }
        
        return result
    
    def evaluate_qa_batch(self, qa_items: List[LocomoQAItem]) -> Dict:
        """
        Evaluate a batch of QA items
        
        Args:
            qa_items: List of QA items to evaluate
            
        Returns:
            Batch evaluation results
        """
        logger.info(f"Evaluating batch of {len(qa_items)} QA items")
        
        results = {
            "total_questions": len(qa_items),
            "evaluation_start": datetime.now(),
            "individual_results": [],
            "category_performance": {},
            "overall_performance": {}
        }
        
        # Process each QA item
        for i, qa_item in enumerate(qa_items):
            if i % 10 == 0:
                logger.info(f"Processing QA item {i+1}/{len(qa_items)}")
            
            try:
                qa_result = self.evaluate_single_qa(qa_item)
                results["individual_results"].append(qa_result)
            except Exception as e:
                logger.error(f"Failed to evaluate QA item {i}: {e}")
                continue
        
        results["evaluation_end"] = datetime.now()
        results["total_evaluation_time"] = (results["evaluation_end"] - results["evaluation_start"]).total_seconds()
        
        # Calculate performance metrics
        results["overall_performance"] = self._calculate_performance_metrics(results["individual_results"])
        
        # Calculate category-wise performance
        category_results = {}
        for category_id in range(1, 6):
            category_items = [r for r in results["individual_results"] if r["category"] == category_id]
            if category_items:
                category_name = LOCOMO_QUESTION_CATEGORIES.get(category_id, f"category_{category_id}")
                category_results[category_name] = self._calculate_performance_metrics(category_items)
        
        results["category_performance"] = category_results
        
        # Performance summary
        logger.info(f"QA Evaluation Complete:")
        logger.info(f"  Total questions: {results['total_questions']}")
        logger.info(f"  Exact match accuracy: {results['overall_performance']['exact_match_accuracy']:.3f}")
        logger.info(f"  Partial match accuracy: {results['overall_performance']['partial_match_accuracy']:.3f}")
        logger.info(f"  Average response time: {results['overall_performance']['avg_response_time']:.3f}s")
        logger.info(f"  Total tokens used: {results['overall_performance']['total_tokens']}")
        
        return results
    
    def _calculate_performance_metrics(self, individual_results: List[Dict]) -> Dict:
        """Calculate performance metrics from individual results"""
        if not individual_results:
            return {}
        
        total_questions = len(individual_results)
        exact_matches = sum(1 for r in individual_results if r["exact_match"])
        partial_matches = sum(1 for r in individual_results if r["partial_match"])
        adversarial_matches = sum(1 for r in individual_results if r["adversarial_match"])
        
        total_time = sum(r["total_evaluation_time"] for r in individual_results)
        total_tokens = sum(r["metadata"].get("token_usage", {}).get("total_tokens", 0) for r in individual_results)
        memories_retrieved = sum(r["memories_retrieved"] for r in individual_results)
        
        return {
            "total_questions": total_questions,
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "adversarial_matches": adversarial_matches,
            "exact_match_accuracy": exact_matches / total_questions if total_questions > 0 else 0.0,
            "partial_match_accuracy": partial_matches / total_questions if total_questions > 0 else 0.0,
            "adversarial_match_rate": adversarial_matches / total_questions if total_questions > 0 else 0.0,
            "avg_response_time": total_time / total_questions if total_questions > 0 else 0.0,
            "total_tokens": total_tokens,
            "avg_tokens_per_question": total_tokens / total_questions if total_questions > 0 else 0.0,
            "avg_memories_retrieved": memories_retrieved / total_questions if total_questions > 0 else 0.0
        }


if __name__ == "__main__":
    # Test the QA evaluator
    import tempfile
    from pathlib import Path
    
    from ..locomo.conversation_processor import LocomoConversationProcessor
    from ..locomo.data_loader import load_locomo_dataset
    
    try:
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        db_manager = DatabaseManager(f"sqlite:///{temp_db.name}")
        search_engine = MemorySearchEngine()
        processor = LocomoConversationProcessor(db_manager, namespace="test_qa")
        
        # Load and process test conversation
        dataset = load_locomo_dataset()
        
        if dataset.conversations:
            logger.info("Processing first conversation for QA testing...")
            conversation = dataset.conversations[0]
            processing_results = processor.process_full_conversation(conversation)
            
            # Initialize QA evaluator
            qa_evaluator = LocomoQAEvaluator(db_manager, search_engine, namespace="test_qa")
            
            # Test with first 5 QA items
            test_qa_items = conversation.qa_pairs[:5]
            logger.info(f"Testing QA evaluator with {len(test_qa_items)} questions...")
            
            evaluation_results = qa_evaluator.evaluate_qa_batch(test_qa_items)
            
            print(f"\nQA Evaluation Results:")
            print(f"Questions evaluated: {evaluation_results['overall_performance']['total_questions']}")
            print(f"Exact match accuracy: {evaluation_results['overall_performance']['exact_match_accuracy']:.3f}")
            print(f"Partial match accuracy: {evaluation_results['overall_performance']['partial_match_accuracy']:.3f}")
            print(f"Average response time: {evaluation_results['overall_performance']['avg_response_time']:.3f}s")
            print(f"Total tokens used: {evaluation_results['overall_performance']['total_tokens']}")
        
        # Clean up
        Path(temp_db.name).unlink()
        
    except Exception as e:
        logger.error(f"QA evaluator test failed: {e}")
        raise