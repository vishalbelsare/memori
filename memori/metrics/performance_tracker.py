"""
Performance Tracker for LOCOMO Benchmark

Tracks latency, token usage, and other performance metrics during benchmarking
to measure efficiency gains and compare against performance targets.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from loguru import logger


@dataclass
class PerformanceMetrics:
    """Individual performance measurement"""
    operation_type: str
    start_time: float
    end_time: float
    duration: float
    token_usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    
    @property
    def latency_ms(self) -> float:
        """Duration in milliseconds"""
        return self.duration * 1000


@dataclass
class BenchmarkSession:
    """Performance tracking for a complete benchmark session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: List[PerformanceMetrics] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)


class PerformanceTracker:
    """
    Tracks performance metrics during LOCOMO benchmarking.
    Measures latency, token usage, throughput, and efficiency.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize performance tracker
        
        Args:
            session_id: Optional session identifier
        """
        self.session_id = session_id or f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = BenchmarkSession(
            session_id=self.session_id,
            start_time=datetime.now()
        )
        
        # Active timers
        self.active_timers: Dict[str, float] = {}
        
        # Aggregated statistics
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.token_stats: Dict[str, List[Dict[str, int]]] = defaultdict(list)
        
        logger.info(f"Performance tracker initialized: {self.session_id}")
    
    def start_operation(self, operation_id: str, operation_type: str, metadata: Optional[Dict] = None) -> str:
        """
        Start timing an operation
        
        Args:
            operation_id: Unique identifier for this operation instance
            operation_type: Type of operation (e.g., 'memory_processing', 'qa_evaluation')
            metadata: Optional metadata about the operation
            
        Returns:
            Operation ID for ending the timer
        """
        start_time = time.perf_counter()
        timer_key = f"{operation_type}_{operation_id}"
        self.active_timers[timer_key] = start_time
        
        logger.debug(f"Started timing: {timer_key}")
        return timer_key
    
    def end_operation(self, timer_key: str, token_usage: Optional[Dict[str, int]] = None,
                     metadata: Optional[Dict] = None) -> PerformanceMetrics:
        """
        End timing an operation and record metrics
        
        Args:
            timer_key: Timer key returned from start_operation
            token_usage: Optional token usage statistics
            metadata: Optional additional metadata
            
        Returns:
            PerformanceMetrics object
        """
        if timer_key not in self.active_timers:
            logger.warning(f"Timer key not found: {timer_key}")
            return None
        
        end_time = time.perf_counter()
        start_time = self.active_timers.pop(timer_key)
        duration = end_time - start_time
        
        # Extract operation type from timer key
        operation_type = timer_key.split('_')[0] if '_' in timer_key else timer_key
        
        metrics = PerformanceMetrics(
            operation_type=operation_type,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            token_usage=token_usage,
            metadata=metadata or {}
        )
        
        # Record metrics
        self.current_session.metrics.append(metrics)
        self.operation_stats[operation_type].append(duration)
        
        if token_usage:
            self.token_stats[operation_type].append(token_usage)
        
        logger.debug(f"Completed timing: {timer_key} ({duration:.3f}s)")
        return metrics
    
    def record_instant_metric(self, operation_type: str, duration: float, 
                             token_usage: Optional[Dict[str, int]] = None,
                             metadata: Optional[Dict] = None) -> PerformanceMetrics:
        """
        Record a metric for an operation that's already completed
        
        Args:
            operation_type: Type of operation
            duration: Operation duration in seconds
            token_usage: Optional token usage statistics
            metadata: Optional metadata
            
        Returns:
            PerformanceMetrics object
        """
        now = time.perf_counter()
        metrics = PerformanceMetrics(
            operation_type=operation_type,
            start_time=now - duration,
            end_time=now,
            duration=duration,
            token_usage=token_usage,
            metadata=metadata or {}
        )
        
        # Record metrics
        self.current_session.metrics.append(metrics)
        self.operation_stats[operation_type].append(duration)
        
        if token_usage:
            self.token_stats[operation_type].append(token_usage)
        
        return metrics
    
    def get_operation_statistics(self, operation_type: Optional[str] = None) -> Dict:
        """
        Get aggregated statistics for operations
        
        Args:
            operation_type: Specific operation type, or None for all
            
        Returns:
            Dictionary with performance statistics
        """
        if operation_type:
            if operation_type not in self.operation_stats:
                return {"error": f"No data for operation type: {operation_type}"}
            
            durations = self.operation_stats[operation_type]
            tokens = self.token_stats.get(operation_type, [])
            
            stats = self._calculate_stats(durations, tokens)
            stats["operation_type"] = operation_type
            return stats
        
        # Return stats for all operation types
        all_stats = {}
        for op_type, durations in self.operation_stats.items():
            tokens = self.token_stats.get(op_type, [])
            all_stats[op_type] = self._calculate_stats(durations, tokens)
        
        return all_stats
    
    def _calculate_stats(self, durations: List[float], tokens: List[Dict[str, int]]) -> Dict:
        """Calculate statistics from duration and token data"""
        if not durations:
            return {"count": 0}
        
        # Duration statistics
        stats = {
            "count": len(durations),
            "total_time": sum(durations),
            "avg_time": sum(durations) / len(durations),
            "min_time": min(durations),
            "max_time": max(durations),
            "avg_latency_ms": (sum(durations) / len(durations)) * 1000,
            "min_latency_ms": min(durations) * 1000,
            "max_latency_ms": max(durations) * 1000
        }
        
        # Token statistics
        if tokens:
            total_tokens = sum(t.get("total_tokens", 0) for t in tokens)
            prompt_tokens = sum(t.get("prompt_tokens", 0) for t in tokens)
            completion_tokens = sum(t.get("completion_tokens", 0) for t in tokens)
            
            stats.update({
                "total_tokens": total_tokens,
                "avg_tokens_per_operation": total_tokens / len(tokens),
                "total_prompt_tokens": prompt_tokens,
                "total_completion_tokens": completion_tokens,
                "avg_prompt_tokens": prompt_tokens / len(tokens) if tokens else 0,
                "avg_completion_tokens": completion_tokens / len(tokens) if tokens else 0
            })
        
        return stats
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        
        # End session if not already ended
        if not self.current_session.end_time:
            self.current_session.end_time = datetime.now()
        
        session_duration = (self.current_session.end_time - self.current_session.start_time).total_seconds()
        
        # Overall statistics
        all_durations = []
        all_tokens = []
        
        for durations in self.operation_stats.values():
            all_durations.extend(durations)
        
        for tokens in self.token_stats.values():
            all_tokens.extend(tokens)
        
        overall_stats = self._calculate_stats(all_durations, all_tokens)
        
        # Operation-specific statistics
        operation_stats = self.get_operation_statistics()
        
        # Efficiency metrics
        throughput = len(all_durations) / session_duration if session_duration > 0 else 0
        
        summary = {
            "session_id": self.session_id,
            "session_start": self.current_session.start_time.isoformat(),
            "session_end": self.current_session.end_time.isoformat(),
            "session_duration": session_duration,
            "total_operations": len(self.current_session.metrics),
            "operations_per_second": throughput,
            "overall_statistics": overall_stats,
            "operation_statistics": operation_stats
        }
        
        return summary
    
    def compare_with_baseline(self, baseline_latency: float, baseline_tokens: int) -> Dict:
        """
        Compare current performance with a baseline system
        
        Args:
            baseline_latency: Baseline average latency in seconds
            baseline_tokens: Baseline average tokens per operation
            
        Returns:
            Comparison metrics
        """
        current_stats = self.get_performance_summary()["overall_statistics"]
        
        if not current_stats or current_stats.get("count", 0) == 0:
            return {"error": "No performance data available for comparison"}
        
        current_latency = current_stats["avg_time"]
        current_tokens = current_stats.get("avg_tokens_per_operation", 0)
        
        # Calculate improvements
        latency_reduction = (baseline_latency - current_latency) / baseline_latency * 100 if baseline_latency > 0 else 0
        token_reduction = (baseline_tokens - current_tokens) / baseline_tokens * 100 if baseline_tokens > 0 else 0
        
        # Speed improvement
        speed_improvement = baseline_latency / current_latency if current_latency > 0 else 0
        
        comparison = {
            "baseline_latency": baseline_latency,
            "current_latency": current_latency,
            "latency_reduction_percentage": latency_reduction,
            "latency_improvement_achieved": latency_reduction >= 50.0,  # 50% improvement target
            
            "baseline_tokens": baseline_tokens,
            "current_tokens": current_tokens,
            "token_reduction_percentage": token_reduction,
            "token_improvement_achieved": token_reduction >= 30.0,  # 30% efficiency target
            
            "speed_improvement_factor": speed_improvement,
            
            "meets_latency_target": current_latency <= 2.0,  # ≤2s response time
            "meets_efficiency_target": token_reduction >= 30.0,
            "overall_efficiency_score": (latency_reduction + token_reduction) / 2
        }
        
        return comparison
    
    def export_metrics(self) -> List[Dict]:
        """Export all metrics for external analysis"""
        return [
            {
                "operation_type": metric.operation_type,
                "duration": metric.duration,
                "latency_ms": metric.latency_ms,
                "token_usage": metric.token_usage,
                "metadata": metric.metadata,
                "timestamp": metric.start_time
            }
            for metric in self.current_session.metrics
        ]
    
    def finalize_session(self) -> Dict:
        """Finalize the current session and return summary"""
        self.current_session.end_time = datetime.now()
        
        summary = self.get_performance_summary()
        
        logger.info(f"Performance session finalized: {self.session_id}")
        logger.info(f"Total operations: {summary['total_operations']}")
        logger.info(f"Session duration: {summary['session_duration']:.2f}s")
        logger.info(f"Average latency: {summary['overall_statistics'].get('avg_latency_ms', 0):.1f}ms")
        
        return summary


# Context managers for easy timing
class TimedOperation:
    """Context manager for timing operations"""
    
    def __init__(self, tracker: PerformanceTracker, operation_type: str, 
                 operation_id: Optional[str] = None, metadata: Optional[Dict] = None):
        self.tracker = tracker
        self.operation_type = operation_type
        self.operation_id = operation_id or f"{operation_type}_{int(time.time())}"
        self.metadata = metadata
        self.timer_key = None
        self.token_usage = None
    
    def __enter__(self):
        self.timer_key = self.tracker.start_operation(
            self.operation_id, self.operation_type, self.metadata
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_key:
            self.tracker.end_operation(self.timer_key, self.token_usage, self.metadata)
    
    def set_token_usage(self, token_usage: Dict[str, int]):
        """Set token usage for this operation"""
        self.token_usage = token_usage


if __name__ == "__main__":
    # Test the performance tracker
    tracker = PerformanceTracker("test_session")
    
    # Test timed operations
    with TimedOperation(tracker, "memory_processing", metadata={"chunks": 5}) as op:
        time.sleep(0.1)  # Simulate processing
        op.set_token_usage({"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50})
    
    with TimedOperation(tracker, "qa_evaluation", metadata={"questions": 3}) as op:
        time.sleep(0.05)  # Simulate evaluation
        op.set_token_usage({"total_tokens": 200, "prompt_tokens": 120, "completion_tokens": 80})
    
    # Test instant metric recording
    tracker.record_instant_metric("search", 0.02, {"total_tokens": 50})
    
    # Get statistics
    summary = tracker.get_performance_summary()
    print(f"Performance Summary:")
    print(f"Total operations: {summary['total_operations']}")
    print(f"Average latency: {summary['overall_statistics']['avg_latency_ms']:.1f}ms")
    print(f"Total tokens: {summary['overall_statistics']['total_tokens']}")
    
    # Compare with performance baseline
    comparison = tracker.compare_with_baseline(baseline_latency=2.0, baseline_tokens=1000)
    print(f"\nComparison with baseline:")
    print(f"Latency reduction: {comparison['latency_reduction_percentage']:.1f}%")
    print(f"Token reduction: {comparison['token_reduction_percentage']:.1f}%")
    print(f"Meets performance targets: {comparison['meets_latency_target']} (latency), {comparison['meets_efficiency_target']} (efficiency)")
    
    # Finalize session
    final_summary = tracker.finalize_session()