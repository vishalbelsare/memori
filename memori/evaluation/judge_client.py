"""
LLM-as-a-Judge Client for LOCOMO Benchmark

Implements LLM-based evaluation of question-answering quality to compute J-scores.
This is the primary metric used in LOCOMO benchmarking for comprehensive assessment.
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Union

import openai
from loguru import logger

from ..locomo.data_models import LOCOMO_QUESTION_CATEGORIES, LocomoQAItem


class LLMJudgeClient:
    """
    LLM-based judge for evaluating QA response quality.
    Provides consistent, objective evaluation of generated answers against ground truth.
    """
    
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        """
        Initialize LLM Judge
        
        Args:
            model: OpenAI model to use as judge
            api_key: OpenAI API key (if None, uses environment variable)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
        # Performance tracking
        self.evaluation_times = []
        self.token_usage = []
        
        # Judge system prompt
        self.system_prompt = """You are an expert evaluator for question-answering systems. Your task is to assess the quality of generated answers compared to ground truth answers in conversational memory tasks.

EVALUATION CRITERIA:

1. **FACTUAL ACCURACY (40%)**: Does the generated answer contain the same factual information as the ground truth?
2. **COMPLETENESS (25%)**: Does the generated answer include all key elements from the ground truth?
3. **RELEVANCE (20%)**: Does the generated answer directly address the question asked?
4. **CLARITY (15%)**: Is the generated answer clear and understandable?

SCORING GUIDELINES:
- Score from 0.0 to 1.0 (where 1.0 = perfect match)
- 0.9-1.0: Excellent - Captures all key information accurately
- 0.7-0.9: Good - Most key information present with minor gaps
- 0.5-0.7: Fair - Some key information but notable omissions
- 0.3-0.5: Poor - Limited accuracy or major omissions  
- 0.0-0.3: Very Poor - Incorrect or completely missing information

SPECIAL CONSIDERATIONS:
- For temporal questions: Pay attention to dates, sequences, time relationships
- For multi-hop questions: Ensure answer synthesizes information from multiple sources
- For adversarial questions: Penalize if the system was misled by incorrect information
- "Information not found" responses: Score based on whether this is accurate given the context

Be objective, consistent, and provide brief reasoning for your scores."""

    def evaluate_single_answer(self, question: str, generated_answer: str, ground_truth_answer: Union[str, int, None],
                              question_category: int, adversarial_answer: Optional[str] = None,
                              evidence_context: Optional[str] = None) -> Dict:
        """
        Evaluate a single generated answer using LLM judge
        
        Args:
            question: The original question
            generated_answer: System's generated answer
            ground_truth_answer: Correct answer (None for adversarial questions)
            question_category: LOCOMO question category (1-5)
            adversarial_answer: Misleading answer for adversarial questions
            evidence_context: Optional context about evidence sources
            
        Returns:
            Evaluation results with score and reasoning
        """
        start_time = time.time()
        
        category_name = LOCOMO_QUESTION_CATEGORIES.get(question_category, "unknown")
        
        # Prepare evaluation prompt based on question type
        if question_category == 5:  # Adversarial questions
            evaluation_prompt = f"""ADVERSARIAL QUESTION EVALUATION:

Question: {question}
Category: {category_name}

Generated Answer: {generated_answer}

Ground Truth Answer: {ground_truth_answer if ground_truth_answer else "Not provided"}
Adversarial (Misleading) Answer: {adversarial_answer if adversarial_answer else "Not provided"}

SPECIAL INSTRUCTIONS FOR ADVERSARIAL QUESTIONS:
- The question is designed to potentially mislead the system
- If the system provided the adversarial (wrong) answer, score should be very low (0.0-0.3)
- If the system correctly identified the right answer or said "information not found", score higher
- If the system avoided the misleading information, this demonstrates good judgment

Provide your evaluation in JSON format:
{{
    "score": <float 0.0-1.0>,
    "reasoning": "<brief explanation of score>",
    "accuracy": <float 0.0-1.0>,
    "completeness": <float 0.0-1.0>,
    "relevance": <float 0.0-1.0>,
    "clarity": <float 0.0-1.0>,
    "avoided_adversarial": <boolean - true if system avoided wrong answer>
}}"""
        else:
            evaluation_prompt = f"""QUESTION-ANSWER EVALUATION:

Question: {question}
Category: {category_name}

Generated Answer: {generated_answer}
Ground Truth Answer: {ground_truth_answer}

{f"Evidence Context: {evidence_context}" if evidence_context else ""}

CATEGORY-SPECIFIC CONSIDERATIONS:
- Single-hop: Should find direct answer from single source
- Multi-hop: Should synthesize information from multiple sources  
- Temporal: Should correctly handle time relationships and dates
- Open-domain: May combine memory information with general knowledge

Evaluate the generated answer against the ground truth and provide your assessment in JSON format:
{{
    "score": <float 0.0-1.0>,
    "reasoning": "<brief explanation of score>",
    "accuracy": <float 0.0-1.0>,
    "completeness": <float 0.0-1.0>,
    "relevance": <float 0.0-1.0>,
    "clarity": <float 0.0-1.0>
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": evaluation_prompt}
                ],
                max_tokens=300,
                temperature=0.1  # Low temperature for consistency
            )
            
            evaluation_text = response.choices[0].message.content.strip()
            
            # Track token usage
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            self.token_usage.append(token_usage)
            
            # Parse JSON response
            try:
                evaluation_data = json.loads(evaluation_text)
                
                # Validate required fields
                required_fields = ['score', 'reasoning', 'accuracy', 'completeness', 'relevance', 'clarity']
                for field in required_fields:
                    if field not in evaluation_data:
                        evaluation_data[field] = 0.5  # Default moderate score
                
                # Ensure scores are in valid range
                for field in ['score', 'accuracy', 'completeness', 'relevance', 'clarity']:
                    evaluation_data[field] = max(0.0, min(1.0, float(evaluation_data[field])))
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse judge evaluation: {e}")
                # Fallback evaluation
                evaluation_data = {
                    "score": 0.3,  # Conservative fallback
                    "reasoning": f"Parse error: {str(e)}",
                    "accuracy": 0.3,
                    "completeness": 0.3,
                    "relevance": 0.3,
                    "clarity": 0.3
                }
            
            evaluation_time = time.time() - start_time
            self.evaluation_times.append(evaluation_time)
            
            # Add metadata
            evaluation_data.update({
                "question": question,
                "generated_answer": generated_answer,
                "ground_truth_answer": ground_truth_answer,
                "category": category_name,
                "category_id": question_category,
                "evaluation_time": evaluation_time,
                "token_usage": token_usage
            })
            
            return evaluation_data
            
        except Exception as e:
            logger.error(f"LLM judge evaluation failed: {e}")
            return {
                "score": 0.0,
                "reasoning": f"Evaluation failed: {str(e)}",
                "accuracy": 0.0,
                "completeness": 0.0,
                "relevance": 0.0,
                "clarity": 0.0,
                "error": str(e)
            }
    
    def evaluate_qa_batch(self, qa_results: List[Dict]) -> Dict:
        """
        Evaluate a batch of QA results using LLM judge
        
        Args:
            qa_results: List of QA evaluation results from qa_evaluator
            
        Returns:
            Batch evaluation results with J-scores
        """
        logger.info(f"LLM Judge evaluating batch of {len(qa_results)} QA results")
        
        judge_results = {
            "total_evaluations": len(qa_results),
            "evaluation_start": time.time(),
            "individual_judgments": [],
            "category_scores": {},
            "overall_scores": {}
        }
        
        # Process each QA result
        for i, qa_result in enumerate(qa_results):
            if i % 5 == 0:
                logger.info(f"Judge evaluating QA result {i+1}/{len(qa_results)}")
            
            try:
                judgment = self.evaluate_single_answer(
                    question=qa_result["question"],
                    generated_answer=qa_result["generated_answer"],
                    ground_truth_answer=qa_result["correct_answer"],
                    question_category=qa_result["category"],
                    adversarial_answer=qa_result.get("adversarial_answer"),
                    evidence_context=", ".join(qa_result.get("evidence_ids", []))
                )
                
                # Add original QA result data
                judgment["original_qa_result"] = qa_result
                judge_results["individual_judgments"].append(judgment)
                
            except Exception as e:
                logger.error(f"Failed to judge QA result {i}: {e}")
                continue
        
        judge_results["evaluation_end"] = time.time()
        judge_results["total_evaluation_time"] = judge_results["evaluation_end"] - judge_results["evaluation_start"]
        
        # Calculate overall performance metrics
        valid_judgments = [j for j in judge_results["individual_judgments"] if "error" not in j]
        
        if valid_judgments:
            # Overall J-score (mean of all scores)
            j_score = sum(j["score"] for j in valid_judgments) / len(valid_judgments)
            
            # Component scores
            accuracy_score = sum(j["accuracy"] for j in valid_judgments) / len(valid_judgments)
            completeness_score = sum(j["completeness"] for j in valid_judgments) / len(valid_judgments)
            relevance_score = sum(j["relevance"] for j in valid_judgments) / len(valid_judgments)
            clarity_score = sum(j["clarity"] for j in valid_judgments) / len(valid_judgments)
            
            # Token usage
            total_tokens = sum(j["token_usage"]["total_tokens"] for j in valid_judgments)
            avg_evaluation_time = sum(j["evaluation_time"] for j in valid_judgments) / len(valid_judgments)
            
            judge_results["overall_scores"] = {
                "j_score": j_score,
                "j_score_percentage": j_score * 100,  # Convert to percentage for benchmark comparison
                "accuracy": accuracy_score,
                "completeness": completeness_score,
                "relevance": relevance_score,
                "clarity": clarity_score,
                "total_evaluations": len(valid_judgments),
                "failed_evaluations": len(qa_results) - len(valid_judgments),
                "success_rate": len(valid_judgments) / len(qa_results) if qa_results else 0.0,
                "total_tokens": total_tokens,
                "avg_tokens_per_evaluation": total_tokens / len(valid_judgments) if valid_judgments else 0.0,
                "avg_evaluation_time": avg_evaluation_time
            }
            
            # Category-wise J-scores
            category_scores = {}
            for category_id in range(1, 6):
                category_judgments = [j for j in valid_judgments if j["category_id"] == category_id]
                if category_judgments:
                    category_name = LOCOMO_QUESTION_CATEGORIES.get(category_id, f"category_{category_id}")
                    category_j_score = sum(j["score"] for j in category_judgments) / len(category_judgments)
                    
                    category_scores[category_name] = {
                        "j_score": category_j_score,
                        "j_score_percentage": category_j_score * 100,
                        "count": len(category_judgments),
                        "accuracy": sum(j["accuracy"] for j in category_judgments) / len(category_judgments),
                        "completeness": sum(j["completeness"] for j in category_judgments) / len(category_judgments),
                        "relevance": sum(j["relevance"] for j in category_judgments) / len(category_judgments),
                        "clarity": sum(j["clarity"] for j in category_judgments) / len(category_judgments)
                    }
            
            judge_results["category_scores"] = category_scores
            
        else:
            judge_results["overall_scores"] = {
                "j_score": 0.0,
                "j_score_percentage": 0.0,
                "error": "No valid evaluations"
            }
        
        # Performance summary
        overall_score = judge_results["overall_scores"]["j_score_percentage"]
        logger.info(f"LLM Judge Evaluation Complete:")
        logger.info(f"  J-Score: {overall_score:.1f}% (Target: ≥70% for high performance)")
        logger.info(f"  Valid evaluations: {judge_results['overall_scores'].get('total_evaluations', 0)}")
        logger.info(f"  Average evaluation time: {judge_results['overall_scores'].get('avg_evaluation_time', 0.0):.2f}s")
        logger.info(f"  Total tokens used: {judge_results['overall_scores'].get('total_tokens', 0)}")
        
        # Performance assessment
        if overall_score >= 70.0:
            logger.info(f"  🎉 EXCELLENT performance - exceeds high performance threshold!")
        elif overall_score >= 60.0:
            logger.info(f"  📊 GOOD performance with room for optimization")
        else:
            logger.info(f"  🔧 Performance below target - areas for improvement identified")
        
        return judge_results
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary for the judge client"""
        
        if not self.evaluation_times:
            return {"error": "No evaluations performed yet"}
        
        total_tokens = sum(usage["total_tokens"] for usage in self.token_usage)
        avg_evaluation_time = sum(self.evaluation_times) / len(self.evaluation_times)
        
        return {
            "total_evaluations": len(self.evaluation_times),
            "avg_evaluation_time": avg_evaluation_time,
            "total_evaluation_time": sum(self.evaluation_times),
            "total_tokens_used": total_tokens,
            "avg_tokens_per_evaluation": total_tokens / len(self.evaluation_times) if self.evaluation_times else 0.0
        }


if __name__ == "__main__":
    # Test the LLM judge
    from ..locomo.data_models import LocomoQAItem
    
    try:
        judge = LLMJudgeClient()
        
        # Test with sample QA items
        test_qa_results = [
            {
                "question": "When did Caroline go to the LGBTQ support group?",
                "correct_answer": "7 May 2023",
                "adversarial_answer": None,
                "generated_answer": "Caroline attended the LGBTQ support group on May 7, 2023.",
                "category": 2,  # temporal
                "evidence_ids": ["D1:3"]
            },
            {
                "question": "What is Caroline's identity?",
                "correct_answer": "Transgender woman",
                "adversarial_answer": None,
                "generated_answer": "Caroline identifies as a transgender woman.",
                "category": 1,  # single-hop
                "evidence_ids": ["D1:5"]
            },
            {
                "question": "What did Caroline research?",
                "correct_answer": "Adoption agencies",
                "adversarial_answer": "self-care is important",
                "generated_answer": "Information not found in memories",
                "category": 5,  # adversarial
                "evidence_ids": ["D2:8"]
            }
        ]
        
        logger.info("Testing LLM Judge with sample QA results...")
        judge_results = judge.evaluate_qa_batch(test_qa_results)
        
        print(f"\nLLM Judge Results:")
        print(f"Overall J-Score: {judge_results['overall_scores']['j_score_percentage']:.1f}%")
        print(f"Target for high performance: ≥70%")
        
        j_score = judge_results['overall_scores']['j_score_percentage']
        if j_score >= 70.0:
            print(f"🎉 EXCELLENT: High performance achieved!")
        elif j_score >= 60.0:
            print(f"📊 GOOD: Performance with optimization potential")
        else:
            print(f"🔧 NEEDS IMPROVEMENT: Below performance targets")
        
        print(f"\nComponent Scores:")
        print(f"  Accuracy: {judge_results['overall_scores']['accuracy']:.3f}")
        print(f"  Completeness: {judge_results['overall_scores']['completeness']:.3f}")
        print(f"  Relevance: {judge_results['overall_scores']['relevance']:.3f}")
        print(f"  Clarity: {judge_results['overall_scores']['clarity']:.3f}")
        
        print(f"\nCategory Scores:")
        for category, scores in judge_results['category_scores'].items():
            print(f"  {category}: {scores['j_score_percentage']:.1f}% ({scores['count']} questions)")
        
    except Exception as e:
        logger.error(f"LLM judge test failed: {e}")
        raise