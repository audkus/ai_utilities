#!/usr/bin/env python3
"""
Performance benchmarks for AI Utilities monitoring scripts.

Tests performance characteristics including:
- Response time benchmarks
- Memory usage profiling
- Concurrent operation performance
- Scalability testing
- Resource utilization monitoring
"""

import os
import sys
import tempfile
import time
import psutil
import threading
import concurrent.futures
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add scripts to path for imports
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)


class PerformanceBenchmark:
    """Base class for performance benchmarks."""
    
    def setup_method(self):
        """Set up benchmark environment."""
        self.start_time = None
        self.end_time = None
        self.memory_start = None
        self.memory_end = None
        
    def start_timing(self):
        """Start performance timing."""
        self.start_time = time.time()
        self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def end_timing(self):
        """End performance timing."""
        self.end_time = time.time()
        self.memory_end = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def get_duration(self):
        """Get execution duration."""
        return self.end_time - self.start_time if self.end_time and self.start_time else 0
        
    def get_memory_usage(self):
        """Get memory usage delta."""
        return self.memory_end - self.memory_start if self.memory_end and self.memory_start else 0


class TestProviderHealthMonitorBenchmarks(PerformanceBenchmark):
    """Performance benchmarks for provider health monitor."""
    
    def test_health_check_response_time(self):
        """Benchmark health check response times."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock fast response
        with patch('provider_health_monitor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
            mock_response.elapsed.total_seconds.return_value = 0.05  # 50ms
            mock_get.return_value = mock_response
            
            self.start_timing()
            result = monitor.check_provider_health("openai", "https://api.openai.com/v1/models")
            self.end_timing()
            
            # Performance assertions
            assert self.get_duration() < 1.0, f"Health check took {self.get_duration():.3f}s, should be < 1.0s"
            assert self.get_memory_usage() < 10, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 10MB"
            assert result["status"] == "healthy"
    
    def test_concurrent_health_checks(self):
        """Benchmark concurrent health check performance."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock responses for concurrent calls
        with patch('provider_health_monitor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_get.return_value = mock_response
            
            providers = ["openai", "groq", "together", "anthropic", "cohere"]
            
            self.start_timing()
            
            # Run concurrent health checks
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(monitor.check_provider_health, provider, f"https://api.{provider}.com/v1/models")
                    for provider in providers
                ]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            self.end_timing()
            
            # Performance assertions
            assert self.get_duration() < 2.0, f"Concurrent checks took {self.get_duration():.3f}s, should be < 2.0s"
            assert len(results) == 5
            assert all(result["status"] == "healthy" for result in results)
    
    def test_large_scale_health_monitoring(self):
        """Benchmark large-scale health monitoring."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock responses for large-scale test
        with patch('provider_health_monitor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": f"model-{i}" for i in range(100)}]}
            mock_response.elapsed.total_seconds.return_value = 0.2
            mock_get.return_value = mock_response
            
            # Simulate monitoring many providers
            provider_count = 20
            self.start_timing()
            
            results = []
            for i in range(provider_count):
                result = monitor.check_provider_health(f"provider-{i}", f"https://api.provider-{i}.com/v1/models")
                results.append(result)
            
            self.end_timing()
            
            # Performance assertions
            assert self.get_duration() < 10.0, f"Large-scale monitoring took {self.get_duration():.3f}s, should be < 10.0s"
            assert len(results) == provider_count
            assert self.get_memory_usage() < 50, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 50MB"


class TestDailyProviderCheckBenchmarks(PerformanceBenchmark):
    """Performance benchmarks for daily provider check."""
    
    def test_daily_check_performance(self):
        """Benchmark daily check execution performance."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        # Mock responses
        with patch('daily_provider_check.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
            mock_response.elapsed.total_seconds.return_value = 0.15
            mock_get.return_value = mock_response
            
            self.start_timing()
            results = checker.run_all_checks()
            self.end_timing()
            
            # Performance assertions
            assert self.get_duration() < 5.0, f"Daily check took {self.get_duration():.3f}s, should be < 5.0s"
            assert len(results) > 0
            assert self.get_memory_usage() < 20, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 20MB"
    
    def test_historical_data_processing(self):
        """Benchmark historical data processing performance."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        # Create large historical dataset
        large_history = {}
        for day in range(365):  # 1 year of data
            date_str = f"2025-{day//30:02d}-{day%30:02d}"
            large_history[date_str] = {
                "providers": {
                    "openai": {"status": "healthy", "response_time_ms": 150},
                    "groq": {"status": "healthy", "response_time_ms": 100}
                }
            }
        
        checker.historical_data = large_history
        
        self.start_timing()
        trends = checker.analyze_trends("openai", days=365)
        self.end_timing()
        
        # Performance assertions
        assert self.get_duration() < 2.0, f"Trend analysis took {self.get_duration():.3f}s, should be < 2.0s"
        assert "availability_percentage" in trends
        assert self.get_memory_usage() < 30, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 30MB"
    
    def test_report_generation_performance(self):
        """Benchmark report generation performance."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        # Mock comprehensive check results
        check_results = {
            "date": "2026-01-10",
            "timestamp": "2026-01-10T09:00:00Z",
            "providers": {
                f"provider-{i}": {
                    "status": "healthy" if i % 2 == 0 else "degraded",
                    "response_time_ms": 100 + i * 10
                } for i in range(50)  # 50 providers
            }
        }
        
        self.start_timing()
        report = checker.generate_daily_report(check_results)
        self.end_timing()
        
        # Performance assertions
        assert self.get_duration() < 1.0, f"Report generation took {self.get_duration():.3f}s, should be < 1.0s"
        assert report["summary"]["total_providers"] == 50
        assert self.get_memory_usage() < 15, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 15MB"


class TestProviderChangeDetectorBenchmarks(PerformanceBenchmark):
    """Performance benchmarks for provider change detector."""
    
    def test_change_detection_performance(self):
        """Benchmark change detection performance."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Mock large model lists
        with patch('provider_change_detector.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"id": f"model-{i}", "object": "model"} for i in range(1000)]
            }
            mock_response.elapsed.total_seconds.return_value = 0.3
            mock_get.return_value = mock_response
            
            self.start_timing()
            changes = detector.run_detection_cycle()
            self.end_timing()
            
            # Performance assertions
            assert self.get_duration() < 5.0, f"Change detection took {self.get_duration():.3f}s, should be < 5.0s"
            assert self.get_memory_usage() < 25, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 25MB"
    
    def test_baseline_comparison_performance(self):
        """Benchmark baseline comparison performance."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Create large baseline and current data
        baseline = {
            "openai": {
                "models": [{"id": f"model-{i}"} for i in range(500)],
                "model_count": 500
            }
        }
        
        current = {
            "openai": {
                "models": [{"id": f"model-{i}"} for i in range(600)],  # 100 new models
                "model_count": 600
            }
        }
        
        self.start_timing()
        changes = detector.detect_model_changes(baseline, current)
        self.end_timing()
        
        # Performance assertions
        assert self.get_duration() < 0.5, f"Baseline comparison took {self.get_duration():.3f}s, should be < 0.5s"
        assert len(changes["openai"]["added_models"]) == 100
        assert self.get_memory_usage() < 10, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 10MB"
    
    def test_pricing_change_analysis_performance(self):
        """Benchmark pricing change analysis performance."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Create large pricing datasets
        baseline = {
            "openai": {
                "pricing": {f"model-{i}": f"${i * 0.001}/1K tokens" for i in range(100)}
            }
        }
        
        current = {
            "openai": {
                "pricing": {f"model-{i}": f"${i * 0.0011}/1K tokens" for i in range(100)}  # 10% price increase
            }
        }
        
        self.start_timing()
        changes = detector.detect_pricing_changes(baseline, current)
        self.end_timing()
        
        # Performance assertions
        assert self.get_duration() < 0.3, f"Pricing analysis took {self.get_duration():.3f}s, should be < 0.3s"
        assert len(changes["openai"]["price_changes"]) == 100
        assert self.get_memory_usage() < 5, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 5MB"


class TestWebUIAPIHelperBenchmarks(PerformanceBenchmark):
    """Performance benchmarks for WebUI API helper."""
    
    def test_webui_discovery_performance(self):
        """Benchmark WebUI discovery performance."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        # Mock WebUI discovery on multiple ports
        with patch('webui_api_helper.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "llama-2-7b"}]}
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_get.return_value = mock_response
            
            ports = list(range(7860, 7920))  # 60 ports
            
            self.start_timing()
            results = helper.scan_for_webuis(ports)
            self.end_timing()
            
            # Performance assertions
            assert self.get_duration() < 15.0, f"WebUI discovery took {self.get_duration():.3f}s, should be < 15.0s"
            assert len(results) == 60
            assert self.get_memory_usage() < 20, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 20MB"
    
    def test_configuration_generation_performance(self):
        """Benchmark configuration generation performance."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        # Test bulk configuration generation
        webui_configs = [
            {
                "type": "text-generation-webui",
                "host": "localhost",
                "port": 7860 + i,
                "models": [f"model-{j}" for j in range(10)]
            } for i in range(20)  # 20 configurations
        ]
        
        self.start_timing()
        
        configs = []
        for config in webui_configs:
            ai_config = helper.generate_ai_utilities_config(config)
            env_content = helper.generate_env_file_content(config)
            configs.append({"ai_config": ai_config, "env_content": env_content})
        
        self.end_timing()
        
        # Performance assertions
        assert self.get_duration() < 1.0, f"Config generation took {self.get_duration():.3f}s, should be < 1.0s"
        assert len(configs) == 20
        assert self.get_memory_usage() < 10, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 10MB"
    
    def test_connection_testing_performance(self):
        """Benchmark connection testing performance."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        # Mock connection testing
        with patch('webui_api_helper.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": [{"text": "Test response"}]}
            mock_response.elapsed.total_seconds.return_value = 0.2
            mock_get.return_value = mock_response
            
            configs = [
                {
                    "provider": "openai_compatible",
                    "base_url": f"http://localhost:{7860 + i}/api/v1",
                    "api_key": "not_required"
                } for i in range(10)
            ]
            
            self.start_timing()
            
            results = []
            for config in configs:
                result = helper.test_webui_connection(config)
                results.append(result)
            
            self.end_timing()
            
            # Performance assertions
            assert self.get_duration() < 5.0, f"Connection testing took {self.get_duration():.3f}s, should be < 5.0s"
            assert all(result["status"] == "success" for result in results)
            assert self.get_memory_usage() < 15, f"Memory usage increased by {self.get_memory_usage():.1f}MB, should be < 15MB"


class TestResourceUtilizationBenchmarks(PerformanceBenchmark):
    """Resource utilization benchmarks."""
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in monitoring scripts."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock responses
        with patch('provider_health_monitor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
            mock_get.return_value = mock_response
            
            # Monitor memory usage over multiple iterations
            memory_samples = []
            
            for iteration in range(100):
                self.start_timing()
                result = monitor.check_provider_health("openai", "https://api.openai.com/v1/models")
                self.end_timing()
                
                memory_samples.append(self.get_memory_usage())
                
                # Force garbage collection periodically
                if iteration % 10 == 0:
                    import gc
                    gc.collect()
            
            # Check for memory leaks
            avg_memory = sum(memory_samples) / len(memory_samples)
            max_memory = max(memory_samples)
            
            # Memory should not grow excessively
            assert max_memory - avg_memory < 5, f"Potential memory leak detected: max={max_memory:.1f}MB, avg={avg_memory:.1f}MB"
    
    def test_cpu_utilization_monitoring(self):
        """Test CPU utilization during monitoring operations."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock responses with some processing time
        with patch('provider_health_monitor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
            mock_get.return_value = mock_response
            
            # Monitor CPU usage during concurrent operations
            process = psutil.Process()
            
            def cpu_monitor():
                cpu_samples = []
                for _ in range(50):
                    cpu_percent = process.cpu_percent()
                    cpu_samples.append(cpu_percent)
                    time.sleep(0.01)
                return cpu_samples
            
            # Start CPU monitoring
            monitor_thread = threading.Thread(target=cpu_monitor)
            monitor_thread.start()
            
            # Run monitoring operations
            self.start_timing()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(monitor.check_provider_health, f"provider-{i}", f"https://api.provider-{i}.com/v1")
                    for i in range(20)
                ]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            self.end_timing()
            
            monitor_thread.join()
            
            # Performance assertions
            assert self.get_duration() < 10.0, f"Concurrent monitoring took {self.get_duration():.3f}s, should be < 10.0s"
            assert len(results) == 20
    
    def test_io_performance_benchmarks(self):
        """Test I/O performance for file operations."""
        from provider_health_monitor import ProviderHealthMonitor
        import json
        
        monitor = ProviderHealthMonitor()
        
        # Test report file I/O performance
        test_reports = []
        
        # Generate test data
        for i in range(100):
            report = {
                "timestamp": time.time(),
                "providers": {
                    "openai": {"status": "healthy", "response_time_ms": 100 + i},
                    "groq": {"status": "healthy", "response_time_ms": 80 + i}
                },
                "summary": {"total": 2, "healthy": 2}
            }
            test_reports.append(report)
        
        # Benchmark file writing
        temp_file = Path(tempfile.mkdtemp()) / "benchmark_report.json"
        
        self.start_timing()
        
        for report in test_reports:
            with open(temp_file, 'w') as f:
                json.dump(report, f)
        
        self.end_timing()
        
        write_duration = self.get_duration()
        
        # Benchmark file reading
        self.start_timing()
        
        for _ in test_reports:
            with open(temp_file, 'r') as f:
                loaded_report = json.load(f)
        
        self.end_timing()
        
        read_duration = self.get_duration()
        
        # Performance assertions
        assert write_duration < 2.0, f"File writing took {write_duration:.3f}s, should be < 2.0s"
        assert read_duration < 1.0, f"File reading took {read_duration:.3f}s, should be < 1.0s"
        
        # Cleanup
        temp_file.unlink()


class TestScalabilityBenchmarks(PerformanceBenchmark):
    """Scalability benchmarks for monitoring scripts."""
    
    def test_provider_count_scalability(self):
        """Test scalability with increasing provider counts."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock responses
        with patch('provider_health_monitor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_get.return_value = mock_response
            
            provider_counts = [5, 10, 25, 50, 100]
            performance_data = []
            
            for count in provider_counts:
                self.start_timing()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(count, 20)) as executor:
                    futures = [
                        executor.submit(monitor.check_provider_health, f"provider-{i}", f"https://api.provider-{i}.com/v1")
                        for i in range(count)
                    ]
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
                self.end_timing()
                
                performance_data.append({
                    "provider_count": count,
                    "duration": self.get_duration(),
                    "memory_usage": self.get_memory_usage(),
                    "success_rate": sum(1 for r in results if r["status"] == "healthy") / len(results)
                })
            
            # Analyze scalability
            for data in performance_data:
                # Performance should scale reasonably
                expected_max_duration = data["provider_count"] * 0.5  # 500ms per provider max
                assert data["duration"] < expected_max_duration, f"Scalability issue: {data['provider_count']} providers took {data['duration']:.3f}s"
                assert data["success_rate"] == 1.0, f"Success rate dropped to {data['success_rate']:.2f} for {data['provider_count']} providers"
    
    def test_data_volume_scalability(self):
        """Test scalability with increasing data volumes."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        # Test with increasing historical data sizes
        data_sizes = [100, 500, 1000, 2000]  # Number of days
        
        for size in data_sizes:
            # Generate large historical dataset
            large_history = {}
            for day in range(size):
                date_str = f"2025-{day//30:02d}-{day%30:02d}"
                large_history[date_str] = {
                    "providers": {
                        "openai": {"status": "healthy", "response_time_ms": 150},
                        "groq": {"status": "healthy", "response_time_ms": 100}
                    }
                }
            
            checker.historical_data = large_history
            
            self.start_timing()
            trends = checker.analyze_trends("openai", days=size)
            self.end_timing()
            
            # Performance should scale linearly, not exponentially
            max_expected_time = size * 0.001  # 1ms per day max
            assert self.get_duration() < max_expected_time, f"Data volume scalability issue: {size} days took {self.get_duration():.3f}s"
    
    def test_concurrent_load_scalability(self):
        """Test scalability under concurrent load."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock responses
        with patch('provider_health_monitor.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
            mock_response.elapsed.total_seconds.return_value = 0.05
            mock_get.return_value = mock_response
            
            # Test with different concurrency levels
            concurrency_levels = [1, 5, 10, 20, 50]
            
            for concurrency in concurrency_levels:
                self.start_timing()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [
                        executor.submit(monitor.check_provider_health, f"provider-{i}", f"https://api.provider-{i}.com/v1")
                        for i in range(50)  # Fixed number of tasks
                    ]
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
                self.end_timing()
                
                # Higher concurrency should improve or maintain performance
                assert self.get_duration() < 10.0, f"Concurrency scalability issue: {concurrency} workers took {self.get_duration():.3f}s"
                assert len(results) == 50
                assert all(result["status"] == "healthy" for result in results)
