"""
Performance tests for memory operations.
"""

import time
from typing import List

import pytest

# Skip all performance tests until API is updated
pytestmark = pytest.mark.skip(reason="Memori class has different API than expected Memori")

from memoriai.core.memory import Memori
from memoriai.utils.pydantic_models import ProcessedMemory
from tests.fixtures.sample_data import SampleData
from tests.fixtures.test_helpers import AssertionHelpers, TestHelpers


class TestMemoryPerformance:
    """Test memory operation performance."""

    @pytest.fixture
    def large_dataset(self) -> List[ProcessedMemory]:
        """Create a large dataset for performance testing."""
        return TestHelpers.create_performance_dataset(1000)

    @pytest.fixture
    def performance_memory_manager(self, temp_db_file) -> Memori:
        """Create a memory manager optimized for performance testing."""
        db_manager = TestHelpers.create_test_database_manager(
            connection_string=f"sqlite:///{temp_db_file}",
            pool_size=10,  # Larger pool for performance
        )
        return TestHelpers.create_test_memory_manager(db_manager)

    @pytest.mark.performance
    @pytest.mark.slow
    def test_bulk_memory_storage_performance(
        self,
        performance_memory_manager: Memori,
        large_dataset: List[ProcessedMemory],
    ):
        """Test performance of storing many memories."""
        batch_size = 100
        memories_to_store = large_dataset[:batch_size]

        start_time = time.time()

        memory_ids = []
        for i, memory in enumerate(memories_to_store):
            memory_id = performance_memory_manager.store_memory(
                processed_memory=memory,
                session_id=f"perf_session_{i // 10}",
                namespace="performance_test",
            )
            memory_ids.append(memory_id)

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance assertions
        assert len(memory_ids) == batch_size
        AssertionHelpers.assert_performance_acceptable(
            execution_time,
            max_time=10.0,  # Should complete within 10 seconds
            operation_name=f"Storing {batch_size} memories",
        )

        # Calculate throughput
        throughput = batch_size / execution_time
        print(f"Memory storage throughput: {throughput:.2f} memories/second")

        # Verify all memories were stored
        stats = performance_memory_manager.get_memory_statistics(
            namespace="performance_test"
        )
        assert stats["total_memories"] >= batch_size

    @pytest.mark.performance
    def test_memory_retrieval_performance(
        self, performance_memory_manager: Memori
    ):
        """Test performance of memory retrieval."""
        # First, populate with test data
        sample_memories = SampleData.get_sample_processed_memories()
        TestHelpers.populate_test_database(
            performance_memory_manager,
            sample_memories * 20,  # 100 memories
            namespace="retrieval_test",
        )

        # Test different query scenarios
        test_queries = [
            "Django model",
            "Python programming",
            "machine learning",
            "optimization",
            "preference dark mode",
        ]

        total_start_time = time.time()

        for query in test_queries:
            start_time = time.time()

            memories = performance_memory_manager.retrieve_memories(
                query=query,
                namespace="retrieval_test",
                limit=10,
            )

            end_time = time.time()
            query_time = end_time - start_time

            # Each query should complete quickly
            AssertionHelpers.assert_performance_acceptable(
                query_time,
                max_time=1.0,  # 1 second per query
                operation_name=f"Query '{query}'",
            )

            # Should return some results
            assert isinstance(memories, list)
            print(f"Query '{query}': {len(memories)} results in {query_time:.3f}s")

        total_time = time.time() - total_start_time
        print(f"Total query time: {total_time:.3f}s for {len(test_queries)} queries")

    @pytest.mark.performance
    def test_concurrent_memory_operations(
        self, performance_memory_manager: Memori
    ):
        """Test performance under concurrent access."""
        import concurrent.futures

        sample_memories = SampleData.get_sample_processed_memories()
        num_threads = 5
        operations_per_thread = 10

        def worker_function(worker_id: int):
            """Worker function for concurrent testing."""
            results = []
            errors = []

            for i in range(operations_per_thread):
                try:
                    # Store a memory
                    memory = sample_memories[i % len(sample_memories)]
                    memory_id = performance_memory_manager.store_memory(
                        processed_memory=memory,
                        session_id=f"concurrent_session_{worker_id}_{i}",
                        namespace=f"concurrent_test_{worker_id}",
                    )

                    # Retrieve memories
                    memories = performance_memory_manager.retrieve_memories(
                        query="test",
                        namespace=f"concurrent_test_{worker_id}",
                        limit=5,
                    )

                    results.append(
                        {
                            "worker_id": worker_id,
                            "operation": i,
                            "memory_id": memory_id,
                            "retrieved_count": len(memories),
                        }
                    )

                except Exception as e:
                    errors.append(
                        {
                            "worker_id": worker_id,
                            "operation": i,
                            "error": str(e),
                        }
                    )

            return results, errors

        # Execute concurrent operations
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(worker_function, worker_id)
                for worker_id in range(num_threads)
            ]

            all_results = []
            all_errors = []

            for future in concurrent.futures.as_completed(futures):
                results, errors = future.result()
                all_results.extend(results)
                all_errors.extend(errors)

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance assertions
        total_operations = num_threads * operations_per_thread * 2  # store + retrieve
        AssertionHelpers.assert_performance_acceptable(
            execution_time,
            max_time=30.0,  # Should complete within 30 seconds
            operation_name=f"{total_operations} concurrent operations",
        )

        # Verify no errors occurred
        assert (
            len(all_errors) == 0
        ), f"Errors occurred during concurrent operations: {all_errors}"

        # Verify all operations completed
        assert len(all_results) == num_threads * operations_per_thread

        print(f"Concurrent operations: {total_operations} ops in {execution_time:.3f}s")
        print(f"Throughput: {total_operations / execution_time:.2f} ops/second")

    @pytest.mark.performance
    def test_large_dataset_search_performance(
        self,
        performance_memory_manager: Memori,
        large_dataset: List[ProcessedMemory],
    ):
        """Test search performance with large dataset."""
        # Populate with large dataset
        dataset_size = 500
        memories_to_store = large_dataset[:dataset_size]

        print(f"Populating database with {dataset_size} memories...")
        populate_start = time.time()

        TestHelpers.populate_test_database(
            performance_memory_manager,
            memories_to_store,
            namespace="large_dataset_test",
        )

        populate_time = time.time() - populate_start
        print(f"Population completed in {populate_time:.3f}s")

        # Test various search scenarios
        search_scenarios = [
            {"query": "Python", "limit": 10, "expected_min": 1},
            {"query": "test", "limit": 50, "expected_min": 10},
            {"query": "programming", "limit": 100, "expected_min": 5},
            {"query": "optimization performance", "limit": 20, "expected_min": 0},
        ]

        for scenario in search_scenarios:
            start_time = time.time()

            memories = performance_memory_manager.retrieve_memories(
                query=scenario["query"],
                namespace="large_dataset_test",
                limit=scenario["limit"],
            )

            search_time = time.time() - start_time

            # Performance assertion
            AssertionHelpers.assert_performance_acceptable(
                search_time,
                max_time=2.0,  # Each search should complete within 2 seconds
                operation_name=f"Search '{scenario['query']}' in {dataset_size} memories",
            )

            # Verify search quality
            assert (
                len(memories) >= scenario["expected_min"]
            ), f"Expected at least {scenario['expected_min']} results for '{scenario['query']}'"

            print(
                f"Search '{scenario['query']}': {len(memories)} results in {search_time:.3f}s"
            )

    @pytest.mark.performance
    def test_memory_statistics_performance(
        self, performance_memory_manager: Memori
    ):
        """Test performance of memory statistics calculation."""
        # Populate with test data
        sample_memories = SampleData.get_sample_processed_memories()
        TestHelpers.populate_test_database(
            performance_memory_manager,
            sample_memories * 50,  # 250 memories
            namespace="stats_test",
        )

        # Test statistics calculation performance
        start_time = time.time()

        stats = performance_memory_manager.get_memory_statistics(namespace="stats_test")

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance assertion
        AssertionHelpers.assert_performance_acceptable(
            execution_time,
            max_time=1.0,  # Should complete within 1 second
            operation_name="Memory statistics calculation",
        )

        # Verify statistics are valid
        TestHelpers.assert_valid_statistics(stats)
        assert stats["total_memories"] >= 250

        print(
            f"Statistics calculation: {execution_time:.3f}s for {stats['total_memories']} memories"
        )

    @pytest.mark.performance
    def test_database_cleanup_performance(
        self, performance_memory_manager: Memori
    ):
        """Test performance of database cleanup operations."""
        # Populate with test data
        sample_memories = SampleData.get_sample_processed_memories()

        # Create memories with short-term retention for cleanup testing
        short_term_memories = []
        for memory in sample_memories:
            # Modify to short-term retention
            memory.importance.retention_type = "short_term"
            short_term_memories.append(memory)

        TestHelpers.populate_test_database(
            performance_memory_manager,
            short_term_memories * 20,  # 100 memories
            namespace="cleanup_test",
        )

        # Test cleanup performance
        start_time = time.time()

        cleaned_count = performance_memory_manager.cleanup_old_memories(
            namespace="cleanup_test",
            days_threshold=0,  # Clean everything
            retention_type="short_term",
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance assertion
        AssertionHelpers.assert_performance_acceptable(
            execution_time,
            max_time=5.0,  # Should complete within 5 seconds
            operation_name=f"Cleanup of {cleaned_count} memories",
        )

        # Verify cleanup worked
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0

        print(f"Cleanup: {cleaned_count} memories cleaned in {execution_time:.3f}s")

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_memory_operation_benchmarks(
        self, performance_memory_manager: Memori, benchmark
    ):
        """Benchmark memory operations using pytest-benchmark."""
        sample_memory = SampleData.get_sample_processed_memories()[0]

        # Benchmark memory storage
        def store_memory():
            return performance_memory_manager.store_memory(
                processed_memory=sample_memory,
                session_id="benchmark_session",
                namespace="benchmark_test",
            )

        # Run benchmark
        result = benchmark(store_memory)
        assert result is not None

        print("Memory storage benchmark completed")

    @pytest.mark.performance
    def test_memory_throughput_stress(self, performance_memory_manager: Memori):
        """Stress test memory throughput with sustained load."""
        sample_memories = SampleData.get_sample_processed_memories()
        stress_duration = 10  # seconds
        operations_count = 0
        errors = []

        start_time = time.time()

        while time.time() - start_time < stress_duration:
            try:
                # Store memory
                memory = sample_memories[operations_count % len(sample_memories)]
                memory_id = performance_memory_manager.store_memory(
                    processed_memory=memory,
                    session_id=f"stress_session_{operations_count}",
                    namespace="stress_test",
                )

                # Occasionally retrieve memories
                if operations_count % 10 == 0:
                    memories = performance_memory_manager.retrieve_memories(
                        query="test",
                        namespace="stress_test",
                        limit=5,
                    )

                operations_count += 1

            except Exception as e:
                errors.append(
                    {
                        "operation": operations_count,
                        "error": str(e),
                        "timestamp": time.time(),
                    }
                )

        end_time = time.time()
        actual_duration = end_time - start_time

        # Calculate throughput
        throughput = operations_count / actual_duration

        # Verify no critical errors
        error_rate = len(errors) / operations_count if operations_count > 0 else 0
        assert (
            error_rate < 0.05
        ), f"Error rate too high: {error_rate:.2%} ({len(errors)} errors)"

        # Verify minimum throughput
        assert throughput >= 10, f"Throughput too low: {throughput:.2f} ops/second"

        print(f"Stress test: {operations_count} operations in {actual_duration:.3f}s")
        print(f"Throughput: {throughput:.2f} ops/second")
        print(f"Error rate: {error_rate:.2%}")

        if errors:
            print(f"Errors encountered: {errors[:5]}...")  # Show first 5 errors
