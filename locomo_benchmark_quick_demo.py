"""
Quick LoCoMo Benchmark Demo
Demonstrates the complete benchmark system with optimized settings for faster execution.
Perfect for testing, development, and quick validation of the benchmark system.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger
from memori.locomo.benchmark_suite import LocomotBenchmarkSuite
from dotenv import load_dotenv

load_dotenv()

def check_api_key():
    """Check if OpenAI API key is available"""
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY environment variable not set!")
        logger.info("Please set your OpenAI API key:")
        logger.info("   Windows: set OPENAI_API_KEY=your_api_key_here")
        logger.info("   Linux/Mac: export OPENAI_API_KEY=your_api_key_here")
        logger.info("   Or create a .env file with OPENAI_API_KEY=your_key")
        return False
    return True


def run_quick_benchmark_demo():
    """Run a quick demo of the complete benchmark system"""
    
    logger.info("🚀 Starting LoCoMo Benchmark Quick Demo...")
    logger.info("="*60)
    logger.info("This demonstrates our complete benchmark system:")
    logger.info("  • 1 conversation (~400 dialogue turns)")
    logger.info("  • 20 questions across 5 categories") 
    logger.info("  • Real AI memory processing")
    logger.info("  • Complete evaluation pipeline")
    logger.info("  • Performance vs baseline comparison")
    logger.info("="*60)
    
    # Check prerequisites
    if not check_api_key():
        return None
    
    try:
        start_time = datetime.now()
        logger.info(f"⏰ Starting demo at: {start_time.strftime('%H:%M:%S')}")
        
        # Initialize benchmark suite with real AI processing
        benchmark = LocomotBenchmarkSuite(use_real_ai=True)
        
        # Run benchmark with optimized settings for demo
        logger.info("Running benchmark: 1 conversation, 20 questions")
        report = benchmark.run_full_benchmark(
            max_conversations=1,    # Single conversation for demo
            max_questions=20,       # Limited questions for speed
            output_path="locomo_demo_results.json"
        )
        
        print("\n" + "="*80)
        print("🎯 LOCOMO BENCHMARK DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        # Extract and display key results
        overall_perf = report["detailed_scores"]["overall_performance"]
        j_score = overall_perf.get("llm_judge_percentage", 0.0)
        f1_score = overall_perf.get("macro_avg_f1", 0.0) * 100
        exact_match = overall_perf.get("exact_match_accuracy", 0.0) * 100
        
        print(f"\n📊 PERFORMANCE RESULTS:")
        print(f"   • J-Score: {j_score:.1f}% (Target: >70%)")
        print(f"   • F1 Score: {f1_score:.1f}% (Target: >80%)")  
        print(f"   • Exact Match: {exact_match:.1f}%")
        
        # Performance metrics
        performance_summary = report.get("performance_tracking", {})
        avg_latency = performance_summary.get("overall_statistics", {}).get("avg_time", 0.0)
        total_tokens = performance_summary.get("overall_statistics", {}).get("total_tokens", 0)
        
        print(f"\n⚡ EFFICIENCY METRICS:")
        print(f"   • Average latency: {avg_latency:.2f}s per operation")
        print(f"   • Total tokens used: {total_tokens:,}")
        
        # Assessment
        high_performance = j_score >= 70.0 and f1_score >= 80.0
        if high_performance:
            print(f"   • 🎉 EXCELLENT performance on LoCoMo benchmark!")
        elif j_score >= 70.0 or f1_score >= 80.0:
            print(f"   • 📊 GOOD performance with room for optimization")
        else:
            print(f"   • 🔧 Areas identified for improvement")
        
        # Processing summary
        metadata = report["detailed_scores"]["benchmark_metadata"] 
        print(f"\n📋 PROCESSING SUMMARY:")
        print(f"   • Conversations processed: {metadata['total_conversations_processed']}")
        print(f"   • Total memories stored: {metadata['total_memories_stored']}")
        print(f"   • Processing time: {metadata['total_evaluation_time']:.1f}s")
        print(f"   • Processing type: {metadata['processing_type']}")
        
        # Category breakdown
        if "category_performance" in report["detailed_scores"]:
            print(f"\n📈 PERFORMANCE BY QUESTION TYPE:")
            for category, scores in report["detailed_scores"]["category_performance"].items():
                if scores["count"] > 0:
                    f1 = scores["avg_f1_score"] * 100
                    exact = scores["exact_match_score"] * 100
                    print(f"   • {category}: {exact:.1f}% exact, {f1:.1f}% F1 ({scores['count']} questions)")
        
        # Executive summary
        if "executive_summary" in report:
            print(f"\n📋 EXECUTIVE SUMMARY:")
            for line in report["executive_summary"]:
                print(f"   {line}")
        
        print(f"\n✅ Demo results saved to: locomo_demo_results.json")
        print(f"✅ Full benchmark system validated and ready!")
        
        # Scale-up guidance
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🔄 TO RUN FULL BENCHMARK:")
        print(f"   python locomo_full_benchmark.py")
        print(f"   • This will process all 10 conversations with ~2000 questions")
        print(f"   • Expected time: 2-3 hours with real AI processing")
        print(f"   • Will provide complete OSS community benchmark results")
        
        logger.info(f"✅ Quick demo completed in {duration.total_seconds():.1f} seconds")
        return report
        
    except Exception as e:
        logger.error(f"❌ Benchmark demo failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main entry point"""
    try:
        report = run_quick_benchmark_demo()
        if report:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()