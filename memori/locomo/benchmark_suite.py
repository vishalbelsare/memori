"""
LOCOMO Benchmark Suite - Complete Orchestrator

Main orchestrator for running complete LOCOMO benchmarks against Memori.
Integrates all components: data loading, memory processing, evaluation, and reporting.
"""

import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

from ..agents.memory_agent import MemoryAgent
from ..agents.retrieval_agent import MemorySearchEngine
from ..core.database import DatabaseManager
from ..evaluation.judge_client import LLMJudgeClient
from ..evaluation.qa_evaluator import LocomoQAEvaluator
from ..evaluation.summary_evaluator import LocomoSummaryEvaluator
from ..metrics.performance_tracker import PerformanceTracker, TimedOperation
from ..metrics.score_calculator import LocomoScoreCalculator
from .data_loader import load_locomo_dataset
from .real_memory_processor import RealMemoryProcessor


class LocomotBenchmarkSuite:
    """
    Complete LOCOMO benchmark orchestrator.
    Runs end-to-end evaluation of Memori against LOCOMO dataset.
    """
    
    def __init__(self, database_path: Optional[str] = None, namespace: Optional[str] = None,
                 use_real_ai: bool = True):
        """
        Initialize benchmark suite
        
        Args:
            database_path: Path to database file (creates temp if None)
            namespace: Benchmark namespace (generates if None)
            use_real_ai: Whether to use real AI processing (recommended for accurate results)
        """
        self.benchmark_id = f"locomo_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.namespace = namespace or f"benchmark_{uuid.uuid4().hex[:8]}"
        self.use_real_ai = use_real_ai
        
        # Setup database
        if database_path:
            self.db_path = database_path
            self.temp_db = None
        else:
            self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            self.temp_db.close()
            self.db_path = self.temp_db.name
        
        # Initialize components
        self.db_manager = DatabaseManager(f"sqlite:///{self.db_path}")
        self.memory_agent = MemoryAgent() if use_real_ai else None
        self.search_engine = MemorySearchEngine()
        
        # Processing and evaluation components
        if use_real_ai:
            self.memory_processor = RealMemoryProcessor(self.db_manager, self.memory_agent, self.namespace)
        else:
            # Fallback to rule-based processing
            from .conversation_processor import LocomoConversationProcessor
            self.memory_processor = LocomoConversationProcessor(self.db_manager, self.namespace)
        
        self.qa_evaluator = LocomoQAEvaluator(self.db_manager, self.search_engine, self.namespace)
        self.summary_evaluator = LocomoSummaryEvaluator(self.db_manager, self.namespace)
        self.judge_client = LLMJudgeClient()
        self.score_calculator = LocomoScoreCalculator()
        
        # Performance tracking
        self.performance_tracker = PerformanceTracker(self.benchmark_id)
        
        # Results storage
        self.conversation_results = []
        self.evaluation_results = {}
        
        logger.info(f"LOCOMO Benchmark Suite initialized: {self.benchmark_id}")
        logger.info(f"Using {'real AI' if use_real_ai else 'rule-based'} memory processing")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Namespace: {self.namespace}")
    
    def load_dataset(self) -> Dict:
        """Load LOCOMO dataset"""
        logger.info("Loading LOCOMO dataset...")
        
        with TimedOperation(self.performance_tracker, "dataset_loading") as op:
            dataset = load_locomo_dataset()
            op.set_token_usage({"total_tokens": 0})  # No tokens for data loading
        
        logger.info(f"Loaded {dataset.total_conversations} conversations with {dataset.total_qa_pairs} QA pairs")
        return dataset
    
    def process_conversations(self, dataset, max_conversations: Optional[int] = None) -> List[Dict]:
        """
        Process all conversations through Memori's memory system
        
        Args:
            dataset: LOCOMO dataset
            max_conversations: Maximum number of conversations to process (None for all)
            
        Returns:
            List of processing results
        """
        conversations_to_process = dataset.conversations
        if max_conversations:
            conversations_to_process = conversations_to_process[:max_conversations]
        
        logger.info(f"Processing {len(conversations_to_process)} conversations through memory system...")
        
        processing_results = []
        
        for i, conversation in enumerate(conversations_to_process):
            conversation_id = f"conv_{i+1:02d}_{conversation.speaker_a}_{conversation.speaker_b}"
            
            logger.info(f"Processing conversation {i+1}/{len(conversations_to_process)}: {conversation_id}")
            
            try:
                with TimedOperation(self.performance_tracker, "memory_processing", 
                                  conversation_id, {"turns": conversation.total_turns}) as op:
                    
                    if self.use_real_ai:
                        result = self.memory_processor.process_full_conversation_with_real_ai(
                            conversation, conversation_id
                        )
                    else:
                        result = self.memory_processor.process_full_conversation(
                            conversation, conversation_id
                        )
                    
                    # No direct token tracking for memory processing (handled internally)
                    op.set_token_usage({"total_tokens": 0})
                
                processing_results.append(result)
                
                logger.info(f"  ✅ Processed: {result['total_memories_stored']} memories stored")
                
            except Exception as e:
                logger.error(f"  ❌ Failed to process conversation {conversation_id}: {e}")
                processing_results.append({
                    "conversation_id": conversation_id,
                    "error": str(e),
                    "total_memories_stored": 0
                })
        
        total_memories = sum(r.get("total_memories_stored", 0) for r in processing_results)
        logger.info(f"Memory processing complete: {total_memories} total memories stored")
        
        self.conversation_results = processing_results
        return processing_results
    
    def evaluate_qa_performance(self, dataset, max_questions: Optional[int] = None) -> Dict:
        """
        Evaluate question-answering performance
        
        Args:
            dataset: LOCOMO dataset
            max_questions: Maximum number of questions to evaluate (None for all)
            
        Returns:
            QA evaluation results
        """
        logger.info("Evaluating question-answering performance...")
        
        # Collect all QA pairs
        all_qa_pairs = []
        for conversation in dataset.conversations:
            all_qa_pairs.extend(conversation.qa_pairs)
        
        if max_questions:
            all_qa_pairs = all_qa_pairs[:max_questions]
        
        logger.info(f"Evaluating {len(all_qa_pairs)} questions across 5 categories...")
        
        with TimedOperation(self.performance_tracker, "qa_evaluation", 
                          metadata={"questions": len(all_qa_pairs)}) as op:
            
            qa_results = self.qa_evaluator.evaluate_qa_batch(all_qa_pairs)
            
            # Track token usage from QA evaluation
            total_tokens = sum(
                result.get("metadata", {}).get("token_usage", {}).get("total_tokens", 0)
                for result in qa_results.get("individual_results", [])
            )
            op.set_token_usage({"total_tokens": total_tokens})
        
        logger.info(f"  QA Evaluation complete:")
        overall_perf = qa_results.get("overall_performance", {})
        logger.info(f"    Exact match accuracy: {overall_perf.get('exact_match_accuracy', 0.0):.3f}")
        logger.info(f"    Partial match accuracy: {overall_perf.get('partial_match_accuracy', 0.0):.3f}")
        logger.info(f"    Average response time: {overall_perf.get('avg_response_time', 0.0):.3f}s")
        
        self.evaluation_results["qa_evaluation"] = qa_results
        return qa_results
    
    def evaluate_llm_judge(self, qa_results: Dict) -> Dict:
        """
        Evaluate using LLM-as-a-Judge scoring
        
        Args:
            qa_results: QA evaluation results
            
        Returns:
            LLM judge results
        """
        logger.info("Running LLM-as-a-Judge evaluation...")
        
        individual_results = qa_results.get("individual_results", [])
        
        with TimedOperation(self.performance_tracker, "llm_judge_evaluation",
                          metadata={"evaluations": len(individual_results)}) as op:
            
            judge_results = self.judge_client.evaluate_qa_batch(individual_results)
            
            # Track token usage from judge evaluation
            total_tokens = judge_results.get("overall_scores", {}).get("total_tokens", 0)
            op.set_token_usage({"total_tokens": total_tokens})
        
        j_score = judge_results.get("overall_scores", {}).get("j_score_percentage", 0.0)
        logger.info(f"  LLM Judge evaluation complete:")
        logger.info(f"    J-Score: {j_score:.1f}% (Target: ≥70% for high performance)")
        
        if j_score >= 70.0:
            logger.info(f"    🎉 EXCELLENT performance - exceeds high performance threshold!")
        elif j_score >= 60.0:
            logger.info(f"    📊 GOOD performance with room for optimization")
        else:
            logger.info(f"    🔧 Performance below target - areas for improvement identified")
        
        self.evaluation_results["llm_judge"] = judge_results
        return judge_results
    
    def evaluate_event_summarization(self, dataset, max_conversations: Optional[int] = None) -> Dict:
        """
        Evaluate event summarization performance
        
        Args:
            dataset: LOCOMO dataset
            max_conversations: Maximum conversations to summarize (None for all)
            
        Returns:
            Summarization evaluation results
        """
        logger.info("Evaluating event summarization performance...")
        
        conversations_to_eval = [(conv, f"conv_{i+1:02d}") for i, conv in enumerate(dataset.conversations)]
        if max_conversations:
            conversations_to_eval = conversations_to_eval[:max_conversations]
        
        with TimedOperation(self.performance_tracker, "event_summarization",
                          metadata={"conversations": len(conversations_to_eval)}) as op:
            
            summary_results = self.summary_evaluator.evaluate_summary_batch(conversations_to_eval)
            
            # Track token usage
            total_tokens = summary_results.get("overall_performance", {}).get("total_tokens", 0)
            op.set_token_usage({"total_tokens": total_tokens})
        
        avg_score = summary_results.get("overall_performance", {}).get("avg_overall_score", 0.0)
        success_rate = summary_results.get("overall_performance", {}).get("success_rate", 0.0)
        
        logger.info(f"  Event summarization complete:")
        logger.info(f"    Average quality score: {avg_score:.2f}/5.0")
        logger.info(f"    Success rate: {success_rate:.3f}")
        
        self.evaluation_results["event_summarization"] = summary_results
        return summary_results
    
    def calculate_comprehensive_scores(self) -> Dict:
        """Calculate comprehensive benchmark scores"""
        logger.info("Calculating comprehensive benchmark scores...")
        
        # Get evaluation results
        qa_results = self.evaluation_results.get("qa_evaluation", {})
        judge_results = self.evaluation_results.get("llm_judge", {})
        summary_results = self.evaluation_results.get("event_summarization", {})
        
        # Get performance metrics
        performance_summary = self.performance_tracker.get_performance_summary()
        
        # Calculate comprehensive score report
        individual_qa = qa_results.get("individual_results", [])
        score_report = self.score_calculator.generate_score_report(
            individual_qa, judge_results, performance_summary
        )
        
        # Add benchmark-specific metrics
        benchmark_metrics = {
            "benchmark_id": self.benchmark_id,
            "namespace": self.namespace,
            "processing_type": "real_ai" if self.use_real_ai else "rule_based",
            "total_conversations_processed": len(self.conversation_results),
            "total_memories_stored": sum(r.get("total_memories_stored", 0) for r in self.conversation_results),
            "total_evaluation_time": performance_summary.get("session_duration", 0.0),
            "database_path": self.db_path
        }
        
        score_report["benchmark_metadata"] = benchmark_metrics
        
        # Performance baseline comparison
        baseline_comparison = self.performance_tracker.compare_with_baseline(
            baseline_latency=5.0,    # Standard baseline: 5s per query
            baseline_tokens=10000    # Standard token usage baseline
        )
        score_report["baseline_comparison"] = baseline_comparison
        
        return score_report
    
    def generate_benchmark_report(self, output_path: Optional[str] = None) -> Dict:
        """
        Generate complete benchmark report
        
        Args:
            output_path: Optional path to save report JSON file
            
        Returns:
            Complete benchmark report
        """
        logger.info("Generating comprehensive benchmark report...")
        
        # Calculate final scores
        comprehensive_scores = self.calculate_comprehensive_scores()
        
        # Create final report
        final_report = {
            "benchmark_metadata": {
                "benchmark_id": self.benchmark_id,
                "evaluation_date": datetime.now().isoformat(),
                "memori_version": "1.0",
                "locomo_dataset": "locomo-10",
                "processing_mode": "real_ai" if self.use_real_ai else "rule_based"
            },
            "executive_summary": self._generate_executive_summary(comprehensive_scores),
            "detailed_scores": comprehensive_scores,
            "performance_tracking": self.performance_tracker.finalize_session(),
            "conversation_processing": self.conversation_results,
            "evaluation_results": self.evaluation_results
        }
        
        # Save to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, default=str)
            
            logger.info(f"Benchmark report saved to: {output_file}")
        
        return final_report
    
    def _generate_executive_summary(self, comprehensive_scores: Dict) -> List[str]:
        """Generate executive summary of benchmark results"""
        summary = []
        
        overall_perf = comprehensive_scores.get("overall_performance", {})
        j_score = overall_perf.get("llm_judge_percentage", 0.0)
        exact_match = overall_perf.get("exact_match_accuracy", 0.0) * 100
        f1_score = overall_perf.get("macro_avg_f1", 0.0) * 100
        
        # Main results
        summary.append(f"LOCOMO Benchmark Results for Memori v1.0")
        summary.append(f"Evaluation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("")
        
        # Performance assessment
        summary.append("🎯 Performance Assessment:")
        summary.append(f"   J-Score: {j_score:.1f}% (Target: ≥70%)")
        
        if j_score >= 70.0:
            summary.append(f"   🎉 EXCELLENT - exceeds high performance threshold!")
        elif j_score >= 60.0:
            summary.append(f"   📊 GOOD performance with optimization opportunities")
        else:
            summary.append(f"   🔧 Below target - improvement areas identified")
        
        # Performance metrics
        baseline_comp = comprehensive_scores.get("baseline_comparison", {})
        current_latency = baseline_comp.get("current_latency", 0.0)
        token_reduction = baseline_comp.get("token_reduction_percentage", 0.0)
        
        summary.append("")
        summary.append("⚡ Efficiency Metrics:")
        summary.append(f"   Average latency: {current_latency:.2f}s (Target: ≤2s)")
        summary.append(f"   Token efficiency: {token_reduction:.1f}% improvement")
        
        # Overall accuracy
        summary.append("")
        summary.append("📊 Accuracy Metrics:")
        summary.append(f"   Exact Match: {exact_match:.1f}%")
        summary.append(f"   F1 Score: {f1_score:.1f}%")
        summary.append(f"   LLM Judge Score: {j_score:.1f}%")
        
        return summary
    
    def run_full_benchmark(self, max_conversations: Optional[int] = None,
                          max_questions: Optional[int] = None,
                          output_path: Optional[str] = None) -> Dict:
        """
        Run complete LOCOMO benchmark
        
        Args:
            max_conversations: Maximum conversations to process (None for all 10)
            max_questions: Maximum questions to evaluate (None for all ~2000)
            output_path: Optional path to save report
            
        Returns:
            Complete benchmark report
        """
        logger.info("🚀 Starting complete LOCOMO benchmark evaluation...")
        logger.info(f"Benchmark ID: {self.benchmark_id}")
        
        try:
            # 1. Load dataset
            dataset = self.load_dataset()
            
            # 2. Process conversations through memory system
            self.process_conversations(dataset, max_conversations)
            
            # 3. Evaluate QA performance
            qa_results = self.evaluate_qa_performance(dataset, max_questions)
            
            # 4. Run LLM-as-a-Judge evaluation
            self.evaluate_llm_judge(qa_results)
            
            # 5. Evaluate event summarization
            self.evaluate_event_summarization(dataset, max_conversations)
            
            # 6. Generate final report
            final_report = self.generate_benchmark_report(output_path)
            
            # Print executive summary
            logger.info("📋 BENCHMARK COMPLETE - Executive Summary:")
            for line in final_report["executive_summary"]:
                logger.info(f"   {line}")
            
            return final_report
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise
        
        finally:
            # Cleanup temporary database if created
            if self.temp_db and Path(self.temp_db.name).exists():
                try:
                    Path(self.temp_db.name).unlink()
                    logger.debug("Cleaned up temporary database")
                except:
                    pass
    
    def cleanup(self):
        """Clean up resources"""
        if self.temp_db:
            try:
                Path(self.temp_db.name).unlink()
                logger.debug("Cleaned up temporary database")
            except:
                pass


if __name__ == "__main__":
    # Run benchmark with sample data
    logger.info("Running LOCOMO Benchmark Suite...")
    
    try:
        # Initialize benchmark suite
        benchmark = LocomotBenchmarkSuite(use_real_ai=True)
        
        # Run benchmark with limited data for testing
        report = benchmark.run_full_benchmark(
            max_conversations=2,  # Test with first 2 conversations
            max_questions=10,     # Test with first 10 questions
            output_path="benchmark_results.json"
        )
        
        print("\n" + "="*80)
        print("LOCOMO BENCHMARK COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        # Print key results
        overall_perf = report["detailed_scores"]["overall_performance"]
        print(f"J-Score: {overall_perf.get('llm_judge_percentage', 0.0):.1f}%")
        print(f"F1 Score: {overall_perf.get('macro_avg_f1', 0.0)*100:.1f}%") 
        print(f"Exact Match: {overall_perf.get('exact_match_accuracy', 0.0)*100:.1f}%")
        
        baseline_comp = report["detailed_scores"]["baseline_comparison"]
        print(f"Meets performance targets: {baseline_comp.get('meets_latency_target', False)}")
        
    except Exception as e:
        logger.error(f"Benchmark test failed: {e}")
        raise