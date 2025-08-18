"""
Score Calculator for LOCOMO Benchmark

Calculates F1 scores, accuracy metrics, and comprehensive evaluation scores
for LOCOMO benchmark results following research standards.
"""

import re
from collections import Counter
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from loguru import logger

from ..locomo.data_models import LOCOMO_QUESTION_CATEGORIES


class LocomoScoreCalculator:
    """
    Calculates comprehensive scores for LOCOMO benchmark evaluation.
    Implements F1 scores, exact match, partial match, and aggregate metrics.
    """
    
    def __init__(self):
        """Initialize score calculator"""
        self.precision_recall_cache = {}
        
    def normalize_answer(self, answer: Union[str, int, None]) -> str:
        """
        Normalize answer for consistent comparison
        
        Args:
            answer: Answer to normalize
            
        Returns:
            Normalized answer string
        """
        if answer is None:
            return ""
        
        # Convert to string and lowercase
        normalized = str(answer).lower().strip()
        
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def extract_tokens(self, text: str) -> List[str]:
        """Extract tokens from text for F1 calculation"""
        normalized = self.normalize_answer(text)
        tokens = re.findall(r'\b\w+\b', normalized)
        return [token for token in tokens if len(token) > 1]  # Filter out single characters
    
    def calculate_f1_score(self, predicted: str, ground_truth: str) -> Tuple[float, float, float]:
        """
        Calculate F1 score between predicted and ground truth answers
        
        Args:
            predicted: Predicted answer
            ground_truth: Ground truth answer
            
        Returns:
            Tuple of (precision, recall, f1_score)
        """
        predicted_tokens = self.extract_tokens(predicted)
        ground_truth_tokens = self.extract_tokens(ground_truth)
        
        if not ground_truth_tokens:
            return 1.0 if not predicted_tokens else 0.0, 0.0, 0.0
        
        if not predicted_tokens:
            return 0.0, 0.0, 0.0
        
        # Convert to sets for overlap calculation
        pred_set = set(predicted_tokens)
        truth_set = set(ground_truth_tokens)
        
        # Calculate overlap
        overlap = len(pred_set.intersection(truth_set))
        
        # Calculate precision and recall
        precision = overlap / len(pred_set) if pred_set else 0.0
        recall = overlap / len(truth_set) if truth_set else 0.0
        
        # Calculate F1 score
        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
        
        return precision, recall, f1_score
    
    def calculate_exact_match(self, predicted: str, ground_truth: str) -> bool:
        """
        Calculate exact match score
        
        Args:
            predicted: Predicted answer
            ground_truth: Ground truth answer
            
        Returns:
            True if exact match, False otherwise
        """
        pred_normalized = self.normalize_answer(predicted)
        truth_normalized = self.normalize_answer(ground_truth)
        
        return pred_normalized == truth_normalized
    
    def calculate_partial_match(self, predicted: str, ground_truth: str, threshold: float = 0.5) -> bool:
        """
        Calculate partial match based on token overlap
        
        Args:
            predicted: Predicted answer
            ground_truth: Ground truth answer
            threshold: Minimum overlap threshold for partial match
            
        Returns:
            True if partial match above threshold, False otherwise
        """
        _, recall, _ = self.calculate_f1_score(predicted, ground_truth)
        return recall >= threshold
    
    def calculate_semantic_similarity(self, predicted: str, ground_truth: str) -> float:
        """
        Calculate semantic similarity (simplified version using token overlap)
        
        Args:
            predicted: Predicted answer
            ground_truth: Ground truth answer
            
        Returns:
            Similarity score between 0 and 1
        """
        _, _, f1_score = self.calculate_f1_score(predicted, ground_truth)
        return f1_score
    
    def evaluate_single_qa(self, predicted: str, ground_truth: Union[str, int, None], 
                          adversarial_answer: Optional[str] = None) -> Dict:
        """
        Evaluate a single QA pair with comprehensive metrics
        
        Args:
            predicted: Predicted answer
            ground_truth: Ground truth answer
            adversarial_answer: Adversarial (wrong) answer if applicable
            
        Returns:
            Dictionary with evaluation metrics
        """
        if ground_truth is None:
            # Handle adversarial questions where ground truth may not be provided
            if adversarial_answer:
                # For adversarial questions, penalize if the answer matches the wrong answer
                adv_exact_match = self.calculate_exact_match(predicted, adversarial_answer)
                adv_f1 = self.calculate_f1_score(predicted, adversarial_answer)[2]
                
                # Good performance means avoiding the adversarial answer
                return {
                    "exact_match": not adv_exact_match,
                    "partial_match": adv_f1 < 0.5,
                    "f1_score": 1.0 - adv_f1,
                    "precision": 1.0 - adv_f1,
                    "recall": 1.0 - adv_f1,
                    "semantic_similarity": 1.0 - adv_f1,
                    "avoided_adversarial": not adv_exact_match,
                    "is_adversarial": True
                }
            else:
                # No ground truth and no adversarial answer
                return {
                    "exact_match": False,
                    "partial_match": False,
                    "f1_score": 0.0,
                    "precision": 0.0,
                    "recall": 0.0,
                    "semantic_similarity": 0.0,
                    "is_adversarial": False,
                    "error": "No ground truth provided"
                }
        
        # Standard evaluation with ground truth
        ground_truth_str = str(ground_truth)
        
        exact_match = self.calculate_exact_match(predicted, ground_truth_str)
        partial_match = self.calculate_partial_match(predicted, ground_truth_str)
        precision, recall, f1_score = self.calculate_f1_score(predicted, ground_truth_str)
        semantic_similarity = self.calculate_semantic_similarity(predicted, ground_truth_str)
        
        result = {
            "exact_match": exact_match,
            "partial_match": partial_match,
            "f1_score": f1_score,
            "precision": precision,
            "recall": recall,
            "semantic_similarity": semantic_similarity,
            "is_adversarial": False
        }
        
        # Check adversarial performance if adversarial answer provided
        if adversarial_answer:
            adv_exact_match = self.calculate_exact_match(predicted, adversarial_answer)
            result["avoided_adversarial"] = not adv_exact_match
            result["adversarial_confusion"] = adv_exact_match
        
        return result
    
    def calculate_category_scores(self, qa_results: List[Dict]) -> Dict:
        """
        Calculate scores by LOCOMO question category
        
        Args:
            qa_results: List of QA evaluation results
            
        Returns:
            Dictionary with scores by category
        """
        category_results = {category_name: [] for category_name in LOCOMO_QUESTION_CATEGORIES.values()}
        
        # Group results by category
        for result in qa_results:
            category_id = result.get("category", 0)
            category_name = LOCOMO_QUESTION_CATEGORIES.get(category_id, "unknown")
            
            if "evaluation_metrics" in result:
                category_results[category_name].append(result["evaluation_metrics"])
        
        # Calculate aggregate scores for each category
        category_scores = {}
        for category_name, results in category_results.items():
            if not results:
                category_scores[category_name] = {
                    "count": 0,
                    "exact_match_score": 0.0,
                    "partial_match_score": 0.0,
                    "avg_f1_score": 0.0,
                    "avg_precision": 0.0,
                    "avg_recall": 0.0,
                    "semantic_similarity": 0.0
                }
                continue
            
            count = len(results)
            
            category_scores[category_name] = {
                "count": count,
                "exact_match_score": sum(r.get("exact_match", 0) for r in results) / count,
                "partial_match_score": sum(r.get("partial_match", 0) for r in results) / count,
                "avg_f1_score": sum(r.get("f1_score", 0) for r in results) / count,
                "avg_precision": sum(r.get("precision", 0) for r in results) / count,
                "avg_recall": sum(r.get("recall", 0) for r in results) / count,
                "semantic_similarity": sum(r.get("semantic_similarity", 0) for r in results) / count
            }
            
            # Special handling for adversarial questions
            adversarial_results = [r for r in results if r.get("is_adversarial", False)]
            if adversarial_results:
                category_scores[category_name]["adversarial_avoidance_rate"] = sum(
                    r.get("avoided_adversarial", 0) for r in adversarial_results
                ) / len(adversarial_results)
        
        return category_scores
    
    def calculate_overall_scores(self, qa_results: List[Dict], 
                               judge_scores: Optional[Dict] = None) -> Dict:
        """
        Calculate overall benchmark scores
        
        Args:
            qa_results: List of QA evaluation results
            judge_scores: Optional LLM judge scores
            
        Returns:
            Dictionary with overall scores
        """
        if not qa_results:
            return {"error": "No QA results provided"}
        
        # Extract evaluation metrics
        all_metrics = []
        for result in qa_results:
            if "evaluation_metrics" in result:
                all_metrics.append(result["evaluation_metrics"])
        
        if not all_metrics:
            return {"error": "No evaluation metrics found in results"}
        
        count = len(all_metrics)
        
        # Calculate aggregate metrics
        overall_scores = {
            "total_questions": count,
            "exact_match_accuracy": sum(m.get("exact_match", 0) for m in all_metrics) / count,
            "partial_match_accuracy": sum(m.get("partial_match", 0) for m in all_metrics) / count,
            "macro_avg_f1": sum(m.get("f1_score", 0) for m in all_metrics) / count,
            "macro_avg_precision": sum(m.get("precision", 0) for m in all_metrics) / count,
            "macro_avg_recall": sum(m.get("recall", 0) for m in all_metrics) / count,
            "avg_semantic_similarity": sum(m.get("semantic_similarity", 0) for m in all_metrics) / count
        }
        
        # Add LLM judge scores if available
        if judge_scores and "overall_scores" in judge_scores:
            judge_overall = judge_scores["overall_scores"]
            overall_scores.update({
                "llm_judge_score": judge_overall.get("j_score", 0.0),
                "llm_judge_percentage": judge_overall.get("j_score_percentage", 0.0),
                "judge_accuracy": judge_overall.get("accuracy", 0.0),
                "judge_completeness": judge_overall.get("completeness", 0.0),
                "judge_relevance": judge_overall.get("relevance", 0.0),
                "judge_clarity": judge_overall.get("clarity", 0.0)
            })
        
        # Calculate composite scores
        overall_scores["composite_f1_accuracy"] = (
            overall_scores["macro_avg_f1"] + overall_scores["exact_match_accuracy"]
        ) / 2
        
        if judge_scores:
            overall_scores["comprehensive_score"] = (
                overall_scores["macro_avg_f1"] * 0.3 +
                overall_scores["exact_match_accuracy"] * 0.3 +
                overall_scores["llm_judge_score"] * 0.4
            )
        
        # Performance assessment
        overall_scores["high_performance"] = overall_scores.get("llm_judge_percentage", 0.0) >= 70.0
        
        return overall_scores
    
    def generate_score_report(self, qa_results: List[Dict], judge_scores: Optional[Dict] = None,
                            performance_metrics: Optional[Dict] = None) -> Dict:
        """
        Generate comprehensive score report
        
        Args:
            qa_results: QA evaluation results
            judge_scores: LLM judge scores
            performance_metrics: Performance tracking metrics
            
        Returns:
            Comprehensive score report
        """
        # Add evaluation metrics to QA results
        enhanced_results = []
        for result in qa_results:
            enhanced_result = result.copy()
            if "generated_answer" in result and "correct_answer" in result:
                metrics = self.evaluate_single_qa(
                    result["generated_answer"],
                    result["correct_answer"],
                    result.get("adversarial_answer")
                )
                enhanced_result["evaluation_metrics"] = metrics
            enhanced_results.append(enhanced_result)
        
        # Calculate scores
        overall_scores = self.calculate_overall_scores(enhanced_results, judge_scores)
        category_scores = self.calculate_category_scores(enhanced_results)
        
        report = {
            "benchmark_summary": {
                "total_questions": overall_scores.get("total_questions", 0),
                "evaluation_date": "2025-08-18",
                "dataset": "LOCOMO-10",
            },
            "overall_performance": overall_scores,
            "category_performance": category_scores,
            "detailed_results": enhanced_results
        }
        
        # Add performance metrics if available
        if performance_metrics:
            report["performance_metrics"] = performance_metrics
        
        # Add LLM judge results if available
        if judge_scores:
            report["judge_evaluation"] = judge_scores
        
        # Generate performance summary
        report["performance_summary"] = self._generate_performance_summary(overall_scores, category_scores)
        
        return report
    
    def _generate_performance_summary(self, overall_scores: Dict, category_scores: Dict) -> List[str]:
        """Generate human-readable performance summary"""
        summary = []
        
        # Overall performance
        exact_match = overall_scores.get("exact_match_accuracy", 0.0) * 100
        f1_score = overall_scores.get("macro_avg_f1", 0.0) * 100
        llm_judge = overall_scores.get("llm_judge_percentage", 0.0)
        
        summary.append(f"Overall Performance: {exact_match:.1f}% exact match, {f1_score:.1f}% F1 score")
        
        if llm_judge > 0:
            summary.append(f"LLM Judge Score: {llm_judge:.1f}% (Target: ≥70% for high performance)")
            
            if llm_judge >= 70.0:
                summary.append(f"🎉 EXCELLENT performance - exceeds high performance threshold!")
            elif llm_judge >= 60.0:
                summary.append(f"📊 GOOD performance with room for optimization")
            else:
                summary.append(f"🔧 Performance below target - areas for improvement identified")
        
        # Category performance
        summary.append("\nPerformance by Question Type:")
        for category, scores in category_scores.items():
            if scores["count"] > 0:
                cat_f1 = scores["avg_f1_score"] * 100
                cat_exact = scores["exact_match_score"] * 100
                summary.append(f"  {category}: {cat_exact:.1f}% exact match, {cat_f1:.1f}% F1 ({scores['count']} questions)")
        
        return summary


if __name__ == "__main__":
    # Test the score calculator
    calculator = LocomoScoreCalculator()
    
    # Test individual metrics
    pred = "Caroline attended the LGBTQ support group on May 7, 2023"
    truth = "7 May 2023"
    
    precision, recall, f1 = calculator.calculate_f1_score(pred, truth)
    exact_match = calculator.calculate_exact_match(pred, truth)
    
    print(f"F1 Score Test:")
    print(f"Predicted: {pred}")
    print(f"Ground Truth: {truth}")
    print(f"Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
    print(f"Exact Match: {exact_match}")
    
    # Test comprehensive evaluation
    metrics = calculator.evaluate_single_qa(pred, truth)
    print(f"\nComprehensive Metrics: {metrics}")
    
    # Test with sample QA results
    sample_results = [
        {
            "question": "When did Caroline go to the LGBTQ support group?",
            "generated_answer": "Caroline attended the LGBTQ support group on May 7, 2023",
            "correct_answer": "7 May 2023",
            "category": 2
        },
        {
            "question": "What is Caroline's identity?", 
            "generated_answer": "transgender woman",
            "correct_answer": "Transgender woman",
            "category": 1
        }
    ]
    
    report = calculator.generate_score_report(sample_results)
    print(f"\nScore Report:")
    print(f"Overall F1: {report['overall_performance']['macro_avg_f1']:.3f}")
    print(f"Exact Match: {report['overall_performance']['exact_match_accuracy']:.3f}")
    print(f"Performance Summary: {report['performance_summary'][0]}")