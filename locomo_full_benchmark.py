#!/usr/bin/env python3
"""
Complete LoCoMo Benchmark for OSS Community
Runs the full benchmark evaluation on all 10 conversations with ~2000 questions
This is the comprehensive evaluation for comparing Memori against research baselines
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger
from memori.locomo.benchmark_suite import LocomotBenchmarkSuite


def setup_logging():
    """Setup logging for full benchmark run"""
    log_file = Path("locomo_full_benchmark.log")
    
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    logger.add(log_file, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
    
    return log_file


def check_api_key():
    """Check if OpenAI API key is available"""
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY environment variable not set!")
        logger.info("Please set your OpenAI API key:")
        logger.info("   Windows: set OPENAI_API_KEY=your_api_key_here")
        logger.info("   Linux/Mac: export OPENAI_API_KEY=your_api_key_here")
        return False
    return True


def run_full_benchmark():
    """Run complete LoCoMo benchmark evaluation"""
    
    log_file = setup_logging()
    
    logger.info("🚀 STARTING COMPLETE LOCOMO BENCHMARK FOR OSS COMMUNITY")
    logger.info("="*80)
    logger.info("This will evaluate Memori against the full LoCoMo dataset:")
    logger.info("  • All 10 conversations (6,000+ dialogue turns)")
    logger.info("  • All ~2,000 question-answer pairs")
    logger.info("  • 5 question types (single-hop, multi-hop, temporal, knowledge, adversarial)")
    logger.info("  • Real AI memory processing with OpenAI API")
    logger.info("  • LLM-as-a-Judge evaluation")
    logger.info("  • Performance comparison vs research baselines")
    logger.info("="*80)
    
    # Check prerequisites
    if not check_api_key():
        return None
    
    logger.info("📋 Estimated completion time: 2-3 hours")
    logger.info("💰 Estimated cost: $20-40 (depending on API usage)")
    logger.info("📊 Target metrics:")
    logger.info("  • J-Score >70% (LoCoMo high performance threshold)")
    logger.info("  • F1 Score >80% (strong accuracy target)")
    logger.info("  • Latency <2s per query (efficiency target)")
    logger.info("  • Token efficiency optimization")
    
    # Confirmation prompt
    response = input("\n🤔 Continue with full benchmark? (y/N): ").strip().lower()
    if response != 'y':
        logger.info("❌ Benchmark cancelled by user")
        return None
    
    try:
        start_time = datetime.now()
        logger.info(f"⏰ Starting full benchmark at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Initialize benchmark suite
        logger.info("🔧 Initializing benchmark suite...")
        benchmark = LocomotBenchmarkSuite(use_real_ai=True)
        
        # Create results directory
        results_dir = Path("locomo_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"locomo_full_benchmark_{timestamp}.json"
        
        # Run complete benchmark
        logger.info("🎯 Starting complete benchmark evaluation...")
        report = benchmark.run_full_benchmark(
            max_conversations=None,    # ALL 10 conversations
            max_questions=None,        # ALL ~2000 questions  
            output_path=str(results_file)
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Display comprehensive results
        print("\n" + "="*80)
        print("🎉 COMPLETE LOCOMO BENCHMARK FINISHED!")
        print("="*80)
        
        # Key performance metrics
        overall_perf = report["detailed_scores"]["overall_performance"]
        j_score = overall_perf.get("llm_judge_percentage", 0.0)
        f1_score = overall_perf.get("macro_avg_f1", 0.0) * 100
        exact_match = overall_perf.get("exact_match_accuracy", 0.0) * 100
        
        print(f"\n📊 FINAL BENCHMARK RESULTS:")
        print(f"   🎯 J-Score: {j_score:.1f}% (Target: >70%)")
        print(f"   📈 F1 Score: {f1_score:.1f}% (Target: >80%)")
        print(f"   ✅ Exact Match: {exact_match:.1f}%")
        
        # Performance metrics
        performance_summary = report["performance_tracking"]
        avg_latency = performance_summary.get("overall_statistics", {}).get("avg_time", 0.0)
        total_tokens = performance_summary.get("overall_statistics", {}).get("total_tokens", 0)
        
        print(f"\n⚡ EFFICIENCY METRICS:")
        print(f"   🚀 Average latency: {avg_latency:.2f}s per operation")
        print(f"   💾 Total tokens used: {total_tokens:,}")
        print(f"   📈 Operations per second: {performance_summary.get('operations_per_second', 0.0):.2f}")
        
        # Success indicators
        high_j_score = j_score >= 70.0
        high_f1_score = f1_score >= 80.0
        good_latency = avg_latency <= 2.0
        
        print(f"\n🏆 PERFORMANCE ASSESSMENT:")
        print(f"   {'✅' if high_j_score else '❌'} High J-Score (≥70%): {high_j_score}")
        print(f"   {'✅' if high_f1_score else '❌'} High F1 Score (≥80%): {high_f1_score}")
        print(f"   {'✅' if good_latency else '❌'} Low latency (≤2s): {good_latency}")
        
        overall_success = high_j_score and high_f1_score
        print(f"   {'🎉' if overall_success else '📊'} Overall: {'EXCELLENT' if overall_success else 'GOOD' if high_j_score or high_f1_score else 'NEEDS IMPROVEMENT'}")
        
        # Processing summary
        metadata = report["detailed_scores"]["benchmark_metadata"]
        print(f"\n📋 PROCESSING SUMMARY:")
        print(f"   • Total conversations: {metadata['total_conversations_processed']}/10")
        print(f"   • Total memories stored: {metadata['total_memories_stored']:,}")
        print(f"   • Total evaluation time: {duration.total_seconds()/60:.1f} minutes")
        print(f"   • Processing type: {metadata['processing_type']}")
        
        # Category breakdown
        if "category_performance" in report["detailed_scores"]:
            print(f"\n📈 PERFORMANCE BY QUESTION TYPE:")
            for category, scores in report["detailed_scores"]["category_performance"].items():
                if scores["count"] > 0:
                    cat_f1 = scores["avg_f1_score"] * 100
                    cat_exact = scores["exact_match_score"] * 100
                    print(f"   • {category:<15}: {cat_exact:5.1f}% exact | {cat_f1:5.1f}% F1 | ({scores['count']:3d} questions)")
        
        # Output files
        print(f"\n📁 OUTPUT FILES:")
        print(f"   • Results: {results_file}")
        print(f"   • Log file: {log_file}")
        
        # Benchmark summary
        print(f"\n🌟 BENCHMARK SUMMARY:")
        if overall_success:
            print(f"   🎉 Memori demonstrates EXCELLENT performance on LoCoMo benchmark!")
            print(f"   🚀 Achieves high scores across multiple evaluation dimensions")
        elif high_j_score or high_f1_score:
            print(f"   📊 Memori shows GOOD performance with room for optimization")
            print(f"   💡 Strong foundation with opportunities for targeted improvements")
        else:
            print(f"   🔧 Benchmark reveals areas for improvement in memory processing")
            print(f"   📈 Detailed results provide roadmap for optimization")
        
        # Next steps
        print(f"\n🔄 NEXT STEPS:")
        print(f"   1. Share results with OSS community")
        print(f"   2. Analyze category-specific performance for improvements")
        print(f"   3. Consider optimizations based on efficiency metrics")
        print(f"   4. Use benchmark for continuous evaluation during development")
        
        logger.info(f"✅ Full benchmark completed successfully in {duration}")
        return report
        
    except KeyboardInterrupt:
        logger.warning("❌ Benchmark interrupted by user")
        return None
    except Exception as e:
        logger.error(f"❌ Full benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main entry point"""
    try:
        report = run_full_benchmark()
        if report:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()