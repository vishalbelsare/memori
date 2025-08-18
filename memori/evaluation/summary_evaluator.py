"""
Event Summarization Evaluator for LOCOMO Benchmark

Evaluates Memori's ability to generate coherent event summaries from stored conversational memories.
This tests the system's capacity for high-level understanding and temporal reasoning.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import openai
from loguru import logger

from ..core.database import DatabaseManager
from ..locomo.data_models import LocomoConversation
from ..utils.pydantic_models import MemoryCategoryType


class LocomoSummaryEvaluator:
    """
    Evaluates event summarization performance using stored memories.
    Tests ability to extract and summarize key events from conversational data.
    """
    
    def __init__(self, database_manager: DatabaseManager, namespace: str = "locomo_benchmark"):
        """
        Initialize summary evaluator
        
        Args:
            database_manager: Memori database manager
            namespace: Namespace for benchmark data
        """
        self.db_manager = database_manager
        self.namespace = namespace
        self.openai_client = openai.OpenAI()
        
        # Performance tracking
        self.generation_times = []
        self.token_usage = []
    
    def retrieve_conversation_memories(self, conversation_id: str, max_memories: int = 50) -> List[Dict]:
        """
        Retrieve all memories related to a specific conversation
        
        Args:
            conversation_id: Conversation identifier
            max_memories: Maximum number of memories to retrieve
            
        Returns:
            List of memory records
        """
        try:
            with self.db_manager._get_connection() as conn:
                # Get memories from both tables
                short_term_memories = conn.execute("""
                    SELECT memory_id, searchable_content, summary, processed_data, 
                           importance_score, category_primary, created_at, 'short_term' as memory_type
                    FROM short_term_memory 
                    WHERE namespace = ? AND processed_data LIKE ?
                    ORDER BY importance_score DESC, created_at ASC
                    LIMIT ?
                """, (self.namespace, f'%{conversation_id}%', max_memories // 2)).fetchall()
                
                long_term_memories = conn.execute("""
                    SELECT memory_id, searchable_content, summary, processed_data,
                           importance_score, category_primary, created_at, 'long_term' as memory_type
                    FROM long_term_memory
                    WHERE namespace = ? AND processed_data LIKE ?
                    ORDER BY importance_score DESC, created_at ASC
                    LIMIT ?
                """, (self.namespace, f'%{conversation_id}%', max_memories // 2)).fetchall()
                
                memories = [dict(row) for row in short_term_memories] + [dict(row) for row in long_term_memories]
                
                # Sort by creation time to maintain temporal order
                memories.sort(key=lambda x: x['created_at'])
                
                logger.debug(f"Retrieved {len(memories)} memories for conversation {conversation_id}")
                return memories
                
        except Exception as e:
            logger.error(f"Failed to retrieve memories for conversation {conversation_id}: {e}")
            return []
    
    def generate_event_summary(self, memories: List[Dict], conversation_info: Dict) -> Tuple[str, Dict]:
        """
        Generate event summary from conversation memories
        
        Args:
            memories: List of memory records
            conversation_info: Information about the conversation (speakers, sessions, etc.)
            
        Returns:
            Tuple of (summary, metadata)
        """
        start_time = time.time()
        
        if not memories:
            return "No memories available for summarization.", {"error": "No memories found"}
        
        # Prepare context from memories
        context_parts = []
        for i, memory in enumerate(memories[:20]):  # Limit to prevent token overflow
            summary = memory.get('summary', '')
            category = memory.get('category_primary', 'unknown')
            importance = memory.get('importance_score', 0.5)
            
            context_parts.append(f"Memory {i+1} ({category}, importance: {importance:.2f}): {summary}")
        
        context = "\n".join(context_parts)
        
        # Extract conversation metadata
        speakers = conversation_info.get('speakers', ['Speaker A', 'Speaker B'])
        total_sessions = conversation_info.get('total_sessions', 0)
        total_turns = conversation_info.get('total_turns', 0)
        
        prompt = f"""Based on the conversation memories provided below, generate a comprehensive event summary that captures the key events, developments, and outcomes from this conversation.

Conversation Details:
- Participants: {' and '.join(speakers)}
- Total Sessions: {total_sessions}
- Total Dialogue Turns: {total_turns}

Instructions:
1. Identify the main events and developments in chronological order
2. Highlight significant moments, decisions, or changes
3. Include temporal information where available (dates, sequences)
4. Focus on actionable events and meaningful interactions
5. Maintain coherence across multiple conversation sessions
6. Length: Approximately 200-300 words

Conversation Memories:
{context}

Generate a well-structured event summary that demonstrates understanding of the conversation flow and key developments:

Event Summary:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at generating coherent event summaries from conversational data. Focus on capturing the key developments, timeline, and significant moments."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.2  # Slightly creative but consistent
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Track token usage
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            self.token_usage.append(token_usage)
            
            generation_time = time.time() - start_time
            self.generation_times.append(generation_time)
            
            metadata = {
                "memories_used": len(memories),
                "generation_time": generation_time,
                "token_usage": token_usage,
                "context_length": len(context),
                "speakers": speakers,
                "total_sessions": total_sessions
            }
            
            return summary, metadata
            
        except Exception as e:
            logger.error(f"Event summary generation failed: {e}")
            return f"Error generating summary: {str(e)}", {"error": str(e)}
    
    def evaluate_summary_quality(self, generated_summary: str, conversation: LocomoConversation) -> Dict:
        """
        Evaluate the quality of generated summary using various metrics
        
        Args:
            generated_summary: Generated event summary
            conversation: Original LOCOMO conversation
            
        Returns:
            Quality evaluation metrics
        """
        try:
            # Extract ground truth information from conversation
            speakers = [conversation.speaker_a, conversation.speaker_b]
            total_sessions = len(conversation.sessions)
            total_turns = conversation.total_turns
            
            # Create reference content from original conversation
            reference_content = []
            for session in conversation.sessions:
                for turn in session.turns:
                    reference_content.append(turn.text)
            
            reference_text = " ".join(reference_content)
            
            # Use LLM to evaluate summary quality
            evaluation_prompt = f"""Evaluate the quality of the following event summary based on the original conversation content.

Generated Summary:
{generated_summary}

Original Conversation Overview:
- Speakers: {' and '.join(speakers)}
- Sessions: {total_sessions}
- Total turns: {total_turns}
- Sample content: {reference_text[:1000]}...

Evaluation Criteria:
1. Accuracy: How well does the summary capture factual information?
2. Completeness: Are major events and developments included?
3. Coherence: Is the summary logically structured and easy to follow?
4. Temporal Understanding: Does it correctly sequence events over time?
5. Relevance: Does it focus on important events rather than trivial details?

Provide scores from 1-5 for each criterion and overall assessment.

Evaluation (JSON format):
{{
    "accuracy": <score 1-5>,
    "completeness": <score 1-5>,
    "coherence": <score 1-5>,
    "temporal_understanding": <score 1-5>,
    "relevance": <score 1-5>,
    "overall_score": <average score>,
    "reasoning": "<brief explanation>"
}}"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of text summarization quality. Provide objective assessments based on the given criteria."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            evaluation_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            import json
            try:
                evaluation_scores = json.loads(evaluation_text)
            except json.JSONDecodeError:
                # Fallback to basic scoring
                evaluation_scores = {
                    "accuracy": 3.0,
                    "completeness": 3.0,
                    "coherence": 3.0,
                    "temporal_understanding": 3.0,
                    "relevance": 3.0,
                    "overall_score": 3.0,
                    "reasoning": "Could not parse detailed evaluation"
                }
            
            return evaluation_scores
            
        except Exception as e:
            logger.error(f"Summary quality evaluation failed: {e}")
            return {
                "accuracy": 0.0,
                "completeness": 0.0,
                "coherence": 0.0,
                "temporal_understanding": 0.0,
                "relevance": 0.0,
                "overall_score": 0.0,
                "reasoning": f"Evaluation failed: {str(e)}"
            }
    
    def evaluate_single_conversation(self, conversation: LocomoConversation, conversation_id: str) -> Dict:
        """
        Evaluate event summarization for a single conversation
        
        Args:
            conversation: LOCOMO conversation
            conversation_id: Conversation identifier
            
        Returns:
            Evaluation results
        """
        start_time = time.time()
        
        # Retrieve memories
        memories = self.retrieve_conversation_memories(conversation_id)
        
        if not memories:
            logger.warning(f"No memories found for conversation {conversation_id}")
            return {
                "conversation_id": conversation_id,
                "error": "No memories found",
                "summary": "",
                "evaluation_scores": {},
                "metadata": {}
            }
        
        # Generate summary
        conversation_info = {
            "speakers": [conversation.speaker_a, conversation.speaker_b],
            "total_sessions": len(conversation.sessions),
            "total_turns": conversation.total_turns
        }
        
        summary, metadata = self.generate_event_summary(memories, conversation_info)
        
        # Evaluate summary quality
        evaluation_scores = self.evaluate_summary_quality(summary, conversation)
        
        total_time = time.time() - start_time
        
        result = {
            "conversation_id": conversation_id,
            "speakers": conversation_info["speakers"],
            "total_sessions": conversation_info["total_sessions"],
            "total_turns": conversation_info["total_turns"],
            "memories_found": len(memories),
            "generated_summary": summary,
            "evaluation_scores": evaluation_scores,
            "total_evaluation_time": total_time,
            "metadata": metadata
        }
        
        logger.info(f"Completed event summarization for conversation {conversation_id}")
        logger.info(f"  Overall score: {evaluation_scores.get('overall_score', 0.0):.2f}/5.0")
        logger.info(f"  Processing time: {total_time:.2f}s")
        
        return result
    
    def evaluate_summary_batch(self, conversations: List[Tuple[LocomoConversation, str]]) -> Dict:
        """
        Evaluate event summarization for a batch of conversations
        
        Args:
            conversations: List of (conversation, conversation_id) tuples
            
        Returns:
            Batch evaluation results
        """
        logger.info(f"Evaluating event summarization for {len(conversations)} conversations")
        
        results = {
            "total_conversations": len(conversations),
            "evaluation_start": datetime.now(),
            "individual_results": [],
            "overall_performance": {}
        }
        
        # Process each conversation
        for i, (conversation, conversation_id) in enumerate(conversations):
            logger.info(f"Processing conversation {i+1}/{len(conversations)}: {conversation_id}")
            
            try:
                conv_result = self.evaluate_single_conversation(conversation, conversation_id)
                results["individual_results"].append(conv_result)
            except Exception as e:
                logger.error(f"Failed to evaluate conversation {conversation_id}: {e}")
                continue
        
        results["evaluation_end"] = datetime.now()
        results["total_evaluation_time"] = (results["evaluation_end"] - results["evaluation_start"]).total_seconds()
        
        # Calculate overall performance metrics
        valid_results = [r for r in results["individual_results"] if "error" not in r]
        
        if valid_results:
            # Average evaluation scores
            score_keys = ['accuracy', 'completeness', 'coherence', 'temporal_understanding', 'relevance', 'overall_score']
            avg_scores = {}
            
            for key in score_keys:
                scores = [r['evaluation_scores'].get(key, 0.0) for r in valid_results]
                avg_scores[f"avg_{key}"] = sum(scores) / len(scores) if scores else 0.0
            
            # Performance metrics
            total_tokens = sum(r['metadata'].get('token_usage', {}).get('total_tokens', 0) for r in valid_results)
            avg_generation_time = sum(r['metadata'].get('generation_time', 0.0) for r in valid_results) / len(valid_results)
            avg_memories_used = sum(r['memories_found'] for r in valid_results) / len(valid_results)
            
            results["overall_performance"] = {
                "successful_evaluations": len(valid_results),
                "failed_evaluations": len(conversations) - len(valid_results),
                "success_rate": len(valid_results) / len(conversations) if conversations else 0.0,
                "avg_generation_time": avg_generation_time,
                "total_tokens": total_tokens,
                "avg_tokens_per_summary": total_tokens / len(valid_results) if valid_results else 0.0,
                "avg_memories_used": avg_memories_used,
                **avg_scores
            }
        else:
            results["overall_performance"] = {
                "successful_evaluations": 0,
                "failed_evaluations": len(conversations),
                "success_rate": 0.0
            }
        
        # Performance summary
        logger.info(f"Event Summarization Evaluation Complete:")
        logger.info(f"  Successful evaluations: {results['overall_performance']['successful_evaluations']}")
        logger.info(f"  Average overall score: {results['overall_performance'].get('avg_overall_score', 0.0):.2f}/5.0")
        logger.info(f"  Average generation time: {results['overall_performance'].get('avg_generation_time', 0.0):.2f}s")
        logger.info(f"  Total tokens used: {results['overall_performance'].get('total_tokens', 0)}")
        
        return results


if __name__ == "__main__":
    # Test the summary evaluator
    import tempfile
    from pathlib import Path
    
    from ..locomo.conversation_processor import LocomoConversationProcessor
    from ..locomo.data_loader import load_locomo_dataset
    
    try:
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        db_manager = DatabaseManager(f"sqlite:///{temp_db.name}")
        processor = LocomoConversationProcessor(db_manager, namespace="test_summary")
        
        # Load and process test conversation
        dataset = load_locomo_dataset()
        
        if dataset.conversations:
            logger.info("Processing first conversation for summary testing...")
            conversation = dataset.conversations[0]
            processing_results = processor.process_full_conversation(conversation, "test_conv_1")
            
            # Initialize summary evaluator
            summary_evaluator = LocomoSummaryEvaluator(db_manager, namespace="test_summary")
            
            # Test event summarization
            logger.info("Testing event summarization...")
            evaluation_result = summary_evaluator.evaluate_single_conversation(conversation, "test_conv_1")
            
            print(f"\nEvent Summarization Results:")
            print(f"Conversation: {evaluation_result['conversation_id']}")
            print(f"Speakers: {' and '.join(evaluation_result['speakers'])}")
            print(f"Memories used: {evaluation_result['memories_found']}")
            print(f"Overall score: {evaluation_result['evaluation_scores'].get('overall_score', 0.0):.2f}/5.0")
            print(f"Processing time: {evaluation_result['total_evaluation_time']:.2f}s")
            print(f"\nGenerated Summary:")
            print(evaluation_result['generated_summary'])
        
        # Clean up
        Path(temp_db.name).unlink()
        
    except Exception as e:
        logger.error(f"Summary evaluator test failed: {e}")
        raise