"""Performance benchmarks for AI Utilities.

This module provides baseline performance measurements for key operations
to help track performance regressions and guide optimization efforts.
"""

import time
import tracemalloc
import psutil
import os
from typing import Dict, List, Any
from dataclasses import dataclass

from ai_utilities import AiClient, AiSettings
from tests.fake_provider import FakeProvider


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    name: str
    duration_ms: float
    memory_mb: float
    operations_per_second: float
    metadata: Dict[str, Any]


class PerformanceBenchmarks:
    """Performance benchmarking suite for AI Utilities."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.results: List[BenchmarkResult] = []
    
    def start_memory_tracking(self):
        """Start memory tracking."""
        tracemalloc.start()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def stop_memory_tracking(self) -> float:
        """Stop memory tracking and return memory used in MB."""
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = current_memory - self.start_memory
        return memory_used
    
    def benchmark_cold_start(self) -> BenchmarkResult:
        """Benchmark cold start time - importing and creating first client."""
        self.start_memory_tracking()
        
        start_time = time.perf_counter()
        
        # Simulate cold start by importing in subprocess would be ideal,
        # but we'll measure client creation time as proxy
        settings = AiSettings(api_key="test-key", model="test-model")
        fake_provider = FakeProvider(["test response"])
        client = AiClient(settings, provider=fake_provider, auto_setup=False)
        
        end_time = time.perf_counter()
        memory_used = self.stop_memory_tracking()
        
        duration_ms = (end_time - start_time) * 1000
        ops_per_second = 1000 / duration_ms if duration_ms > 0 else 0
        
        result = BenchmarkResult(
            name="cold_start",
            duration_ms=duration_ms,
            memory_mb=memory_used,
            operations_per_second=ops_per_second,
            metadata={"client_created": True}
        )
        
        self.results.append(result)
        return result
    
    def benchmark_client_creation(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark client creation performance."""
        self.start_memory_tracking()
        
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            settings = AiSettings(api_key="test-key", model="test-model")
            fake_provider = FakeProvider(["test response"])
            client = AiClient(settings, provider=fake_provider, auto_setup=False)
            del client  # Clean up
        
        end_time = time.perf_counter()
        memory_used = self.stop_memory_tracking()
        
        total_duration = (end_time - start_time) * 1000
        avg_duration_ms = total_duration / iterations
        ops_per_second = iterations / (total_duration / 1000) if total_duration > 0 else 0
        
        result = BenchmarkResult(
            name="client_creation",
            duration_ms=avg_duration_ms,
            memory_mb=memory_used / iterations,
            operations_per_second=ops_per_second,
            metadata={"iterations": iterations}
        )
        
        self.results.append(result)
        return result
    
    def benchmark_simple_request(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark simple AI request performance."""
        fake_provider = FakeProvider(["Test response for benchmark"])
        settings = AiSettings(api_key="test-key", model="test-model")
        client = AiClient(settings, provider=fake_provider, auto_setup=False)
        
        self.start_memory_tracking()
        
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            response = client.ask("test prompt")
        
        end_time = time.perf_counter()
        memory_used = self.stop_memory_tracking()
        
        total_duration = (end_time - start_time) * 1000
        avg_duration_ms = total_duration / iterations
        ops_per_second = iterations / (total_duration / 1000) if total_duration > 0 else 0
        
        result = BenchmarkResult(
            name="simple_request",
            duration_ms=avg_duration_ms,
            memory_mb=memory_used / iterations,
            operations_per_second=ops_per_second,
            metadata={"iterations": iterations}
        )
        
        self.results.append(result)
        return result
    
    def benchmark_cached_requests(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark cached request performance."""
        fake_provider = FakeProvider(["Cached response"])
        settings = AiSettings(
            api_key="test-key", 
            model="test-model",
            cache_enabled=True,
            cache_backend="memory"
        )
        client = AiClient(settings, provider=fake_provider, auto_setup=False)
        
        self.start_memory_tracking()
        
        start_time = time.perf_counter()
        
        # First request to populate cache
        client.ask("cache test")
        
        # Subsequent requests should hit cache
        cache_start = time.perf_counter()
        for _ in range(iterations):
            response = client.ask("cache test")
        cache_end = time.perf_counter()
        
        end_time = time.perf_counter()
        memory_used = self.stop_memory_tracking()
        
        cache_duration = (cache_end - cache_start) * 1000
        avg_duration_ms = cache_duration / iterations
        ops_per_second = iterations / (cache_duration / 1000) if cache_duration > 0 else 0
        
        result = BenchmarkResult(
            name="cached_request",
            duration_ms=avg_duration_ms,
            memory_mb=memory_used / iterations,
            operations_per_second=ops_per_second,
            metadata={"iterations": iterations, "cache_hit": True}
        )
        
        self.results.append(result)
        return result
    
    def benchmark_memory_usage(self) -> BenchmarkResult:
        """Benchmark memory usage under load."""
        clients = []
        
        self.start_memory_tracking()
        
        # Create multiple clients to test memory usage
        for i in range(10):
            settings = AiSettings(api_key=f"test-key-{i}", model="test-model")
            fake_provider = FakeProvider([f"Response {i}"])
            client = AiClient(settings, provider=fake_provider, auto_setup=False)
            clients.append(client)
        
        # Make some requests
        for i, client in enumerate(clients):
            client.ask(f"test prompt {i}")
        
        memory_used = self.stop_memory_tracking()
        
        result = BenchmarkResult(
            name="memory_usage",
            duration_ms=0,  # Not timing this one
            memory_mb=memory_used,
            operations_per_second=0,
            metadata={"clients_created": len(clients)}
        )
        
        self.results.append(result)
        return result
    
    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmarks and return results."""
        print("🚀 Running AI Utilities Performance Benchmarks...")
        print("=" * 60)
        
        results = []
        
        # Cold start benchmark
        print("📊 Benchmarking cold start...")
        result = self.benchmark_cold_start()
        results.append(result)
        print(f"   Cold start: {result.duration_ms:.2f}ms, {result.memory_mb:.2f}MB")
        
        # Client creation benchmark
        print("📊 Benchmarking client creation...")
        result = self.benchmark_client_creation()
        results.append(result)
        print(f"   Client creation: {result.duration_ms:.2f}ms avg, {result.operations_per_second:.0f} ops/sec")
        
        # Simple request benchmark
        print("📊 Benchmarking simple requests...")
        result = self.benchmark_simple_request()
        results.append(result)
        print(f"   Simple request: {result.duration_ms:.2f}ms avg, {result.operations_per_second:.0f} ops/sec")
        
        # Cached request benchmark
        print("📊 Benchmarking cached requests...")
        result = self.benchmark_cached_requests()
        results.append(result)
        print(f"   Cached request: {result.duration_ms:.2f}ms avg, {result.operations_per_second:.0f} ops/sec")
        
        # Memory usage benchmark
        print("📊 Benchmarking memory usage...")
        result = self.benchmark_memory_usage()
        results.append(result)
        print(f"   Memory usage: {result.memory_mb:.2f}MB for 10 clients")
        
        print("=" * 60)
        print("✅ All benchmarks completed!")
        
        return results
    
    def print_summary(self):
        """Print a summary of all benchmark results."""
        print("\n📈 Performance Summary")
        print("=" * 60)
        
        for result in self.results:
            print(f"{result.name:20} | {result.duration_ms:8.2f}ms | {result.memory_mb:8.2f}MB | {result.operations_per_second:8.0f} ops/sec")
        
        print("=" * 60)
        
        # Performance insights
        print("\n💡 Performance Insights:")
        
        # Find cached vs uncached performance
        simple_result = next((r for r in self.results if r.name == "simple_request"), None)
        cached_result = next((r for r in self.results if r.name == "cached_request"), None)
        
        if simple_result and cached_result:
            speedup = simple_result.duration_ms / cached_result.duration_ms if cached_result.duration_ms > 0 else 0
            print(f"   🚀 Cache provides {speedup:.1f}x speedup for requests")
        
        # Memory efficiency
        memory_result = next((r for r in self.results if r.name == "memory_usage"), None)
        if memory_result:
            print(f"   💾 Memory usage: {memory_result.memory_mb:.2f}MB per client")
        
        print("\n📯 Baseline established for future performance tracking!")


def run_benchmarks():
    """Run performance benchmarks and print results."""
    benchmarks = PerformanceBenchmarks()
    results = benchmarks.run_all_benchmarks()
    benchmarks.print_summary()
    return results


if __name__ == "__main__":
    run_benchmarks()
