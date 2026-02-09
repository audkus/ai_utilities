"""
Comprehensive tests for metrics monitoring examples.

Tests both basic and advanced metrics examples to ensure they work correctly
and demonstrate proper usage patterns.
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ai_utilities.metrics import MetricsCollector, PrometheusExporter, JSONExporter


class TestMetricsMonitoringBasic:
    """Test basic metrics monitoring examples."""
    
    def test_basic_metrics_collection(self):
        """Test basic metrics collection functionality."""
        collector = MetricsCollector()
        
        # Test counter metrics
        collector.increment_counter("test_counter", labels={"env": "test"})
        collector.increment_counter("test_counter", value=5, labels={"env": "test"})
        
        # Test gauge metrics
        collector.set_gauge("test_gauge", 42.5, labels={"type": "test"})
        
        # Test histogram metrics
        collector.observe_histogram("test_histogram", 1.5, labels={"bucket": "test"})
        collector.observe_histogram("test_histogram", 2.5, labels={"bucket": "test"})
        
        # Test timer metrics
        collector.record_timer("test_timer", 0.8, labels={"operation": "test"})
        collector.record_timer("test_timer", 1.2, labels={"operation": "test"})
        
        # Get all metrics
        all_metrics = collector.get_all_metrics()
        
        # Verify metrics were created
        metric_names = [m.name for m in all_metrics]
        
        # Check for counter
        counter_metrics = [m for m in all_metrics if m.name == "test_counter" and m.metric_type.name == "COUNTER"]
        assert len(counter_metrics) >= 1
        assert any(m.value == 6 for m in counter_metrics)  # 1 + 5 = 6
        
        # Check for gauge
        gauge_metrics = [m for m in all_metrics if m.name == "test_gauge" and m.metric_type.name == "GAUGE"]
        assert len(gauge_metrics) >= 1
        assert any(m.value == 42.5 for m in gauge_metrics)
        
        # Check for histogram buckets
        histogram_metrics = [m for m in all_metrics if "test_histogram_bucket" in m.name]
        assert len(histogram_metrics) >= 1
        
        # Check for timer snapshots
        timer_metrics = {m.name: m.value for m in all_metrics if "test_timer" in m.name}
        assert "test_timer_count" in timer_metrics
        assert "test_timer_sum_seconds" in timer_metrics
        assert "test_timer_min_seconds" in timer_metrics
        assert "test_timer_max_seconds" in timer_metrics
        assert "test_timer_last_seconds" in timer_metrics
        
        # Verify timer snapshot values
        assert timer_metrics["test_timer_count"] == 2
        assert timer_metrics["test_timer_sum_seconds"] == 2.0  # 0.8 + 1.2
        assert timer_metrics["test_timer_min_seconds"] == 0.8
        assert timer_metrics["test_timer_max_seconds"] == 1.2
        assert timer_metrics["test_timer_last_seconds"] == 1.2
    
    def test_timer_context_manager(self):
        """Test timer context manager functionality."""
        from ai_utilities.metrics import metrics
        
        # Clear any existing metrics
        metrics.collector = MetricsCollector()
        
        # Test context manager
        with metrics.collector.timer("test_operation", labels={"type": "context"}):
            time.sleep(0.1)  # Small delay
        
        # Check that timer was recorded
        all_metrics = metrics.collector.get_all_metrics()
        timer_metrics = {m.name: m.value for m in all_metrics if "test_operation" in m.name}
        
        assert "test_operation_count" in timer_metrics
        assert "test_operation_last_seconds" in timer_metrics
        assert timer_metrics["test_operation_count"] == 1
        assert timer_metrics["test_operation_last_seconds"] > 0.05  # Should be > 0.05 due to sleep
    
    def test_prometheus_exporter(self):
        """Test Prometheus exporter functionality."""
        collector = MetricsCollector()
        
        # Add sample metrics
        collector.increment_counter("requests_total", labels={"method": "GET"})
        collector.set_gauge("active_users", 42)
        collector.record_timer("response_time", 1.5, labels={"endpoint": "/api"})
        
        # Export to Prometheus format
        exporter = PrometheusExporter(collector)
        output = exporter.export()
        
        # Verify output format
        assert isinstance(output, str)
        assert len(output) > 0
        
        # Check for expected metric names in output
        assert "requests_total" in output
        assert "active_users" in output
        assert "response_time" in output
        
        # Check for Prometheus format elements
        lines = output.split('\n')
        assert any(line.startswith('# HELP') for line in lines)
        assert any(line.startswith('# TYPE') for line in lines)
        assert any('requests_total{' in line for line in lines)
    
    def test_json_exporter(self):
        """Test JSON exporter functionality."""
        collector = MetricsCollector()
        
        # Add sample metrics
        collector.increment_counter("requests_total", labels={"method": "GET"})
        collector.set_gauge("active_users", 42)
        collector.record_timer("response_time", 1.5, labels={"endpoint": "/api"})
        
        # Export to JSON format
        exporter = JSONExporter(collector)
        output = exporter.export()
        
        # Verify output format
        assert isinstance(output, str)
        
        # Parse JSON
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check metric structure
        for metric in data[:3]:  # Check first 3 metrics
            assert "name" in metric
            assert "value" in metric
            assert "metric_type" in metric
            assert "timestamp" in metric
    
    def test_example_script_execution(self):
        """Test that the basic metrics example script can be executed."""
        example_path = Path(__file__).parent.parent.parent / "examples/quickstarts/metrics_monitoring_basic.py"
        
        assert example_path.exists(), f"Example script not found: {example_path}"
        
        # Test script compilation
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        # Should be valid Python
        compile(script_content, str(example_path), 'exec')
        
        # Test that main function exists
        assert "def main():" in script_content
        assert "if __name__ == \"__main__\":" in script_content


class TestMetricsMonitoringAdvanced:
    """Test advanced metrics monitoring examples."""
    
    def test_application_metrics_class(self):
        """Test ApplicationMetrics class functionality."""
        # Import the advanced example
        example_path = Path(__file__).parent.parent.parent / "examples/advanced/metrics_monitoring_advanced.py"
        
        # Read and execute the ApplicationMetrics class definition
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        # Extract the ApplicationMetrics class
        exec_globals = {}
        exec(script_content, exec_globals)
        
        ApplicationMetrics = exec_globals['ApplicationMetrics']
        
        # Test initialization
        app_metrics = ApplicationMetrics()
        assert hasattr(app_metrics, 'collector')
        assert isinstance(app_metrics.collector, MetricsCollector)
        
        # Test tracking methods
        app_metrics.track_request("/api/test", "GET", 200, 0.1)
        app_metrics.track_ai_usage("gpt-4", 100, 1.5, True)
        app_metrics.track_database_operation("SELECT", "users", 0.05, 10)
        app_metrics.track_cache_performance("redis", True, 0.01)
        
        # Check metrics were recorded
        all_metrics = app_metrics.collector.get_all_metrics()
        metric_names = [m.name for m in all_metrics]
        
        assert "http_requests_total" in metric_names
        assert "ai_requests_total" in metric_names
        assert "db_operations_total" in metric_names
        assert "cache_operations_total" in metric_names
    
    def test_health_metrics(self):
        """Test health metrics calculation."""
        example_path = Path(__file__).parent.parent.parent / "examples/advanced/metrics_monitoring_advanced.py"
        
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        exec_globals = {}
        exec(script_content, exec_globals)
        
        ApplicationMetrics = exec_globals['ApplicationMetrics']
        
        app_metrics = ApplicationMetrics()
        
        # Add some test data
        app_metrics.track_request("/api/test", "GET", 200, 0.1)
        app_metrics.track_request("/api/test", "GET", 500, 0.2)  # Error
        
        # Get health metrics
        health = app_metrics.get_health_metrics()
        
        assert "error_rate" in health
        assert "uptime_seconds" in health
        assert "total_requests" in health
        assert "total_errors" in health
        assert "healthy" in health
        
        assert health["total_requests"] == 2
        assert health["total_errors"] == 1
        assert health["error_rate"] == 0.5
        assert health["healthy"] == False  # 50% error rate > 5% threshold
    
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    @patch('psutil.disk_usage')
    def test_system_metrics(self, mock_disk, mock_cpu, mock_memory):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_memory.return_value = MagicMock(used=1024*1024*1024, available=2*1024*1024*1024)
        mock_cpu.return_value = 25.5
        mock_disk.return_value = MagicMock(used=10*1024*1024*1024, free=20*1024*1024*1024)
        
        example_path = Path(__file__).parent.parent.parent / "examples/advanced/metrics_monitoring_advanced.py"
        
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        exec_globals = {}
        exec(script_content, exec_globals)
        
        ApplicationMetrics = exec_globals['ApplicationMetrics']
        
        app_metrics = ApplicationMetrics()
        app_metrics.update_system_metrics()
        
        # Check system metrics
        all_metrics = app_metrics.collector.get_all_metrics()
        system_metrics = {m.name: m.value for m in all_metrics if m.name.startswith("system_")}
        
        assert "system_memory_bytes" in system_metrics
        assert "system_cpu_percent" in system_metrics
        assert "system_disk_bytes" in system_metrics
    
    def test_concurrent_metrics_collection(self):
        """Test thread-safe metrics collection."""
        example_path = Path(__file__).parent.parent.parent / "examples/advanced/metrics_monitoring_advanced.py"
        
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        exec_globals = {}
        exec(script_content, exec_globals)
        
        ApplicationMetrics = exec_globals['ApplicationMetrics']
        
        app_metrics = ApplicationMetrics()
        
        # Simulate concurrent operations
        def worker():
            for i in range(10):
                app_metrics.track_request(f"/api/test/{i}", "GET", 200, 0.01)
        
        import threading
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all metrics were recorded
        all_metrics = app_metrics.collector.get_all_metrics()
        request_metrics = [m for m in all_metrics if m.name == "http_requests_total"]
        
        # Should have 5 workers * 10 requests = 50 total
        total_requests = sum(m.value for m in request_metrics)
        assert total_requests == 50
    
    @pytest.mark.asyncio
    async def test_async_metrics_collection(self):
        """Test async metrics collection."""
        example_path = Path(__file__).parent.parent.parent / "examples/advanced/metrics_monitoring_advanced.py"
        
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        exec_globals = {}
        exec(script_content, exec_globals)
        
        ApplicationMetrics = exec_globals['ApplicationMetrics']
        
        app_metrics = ApplicationMetrics()
        
        # Simulate async operations
        async def async_worker():
            await asyncio.sleep(0.01)  # Simulate async work
            app_metrics.track_ai_usage("gpt-4", 50, 0.5, True)
        
        # Run multiple async workers
        tasks = [async_worker() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # Check metrics were recorded
        all_metrics = app_metrics.collector.get_all_metrics()
        ai_metrics = [m for m in all_metrics if m.name == "ai_requests_total"]
        
        total_ai_requests = sum(m.value for m in ai_metrics)
        assert total_ai_requests == 10
    
    def test_custom_dashboard_export(self):
        """Test custom dashboard export functionality."""
        example_path = Path(__file__).parent.parent.parent / "examples/advanced/metrics_monitoring_advanced.py"
        
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        exec_globals = {}
        exec(script_content, exec_globals)
        
        ApplicationMetrics = exec_globals['ApplicationMetrics']
        
        app_metrics = ApplicationMetrics()
        
        # Add some test data
        app_metrics.track_request("/api/test", "GET", 200, 0.1)
        app_metrics.track_ai_usage("gpt-4", 100, 1.5, True)
        
        # Create custom dashboard export
        def create_dashboard_export(collector):
            all_metrics = collector.get_all_metrics()
            
            dashboard_data = {
                "timestamp": time.time(),
                "metrics": {},
                "health": {}
            }
            
            for metric in all_metrics:
                category = metric.name.split('_')[0] if '_' in metric.name else 'other'
                if category not in dashboard_data["metrics"]:
                    dashboard_data["metrics"][category] = []
                
                dashboard_data["metrics"][category].append({
                    "name": metric.name,
                    "value": metric.value,
                    "type": metric.metric_type.name,
                    "labels": metric.labels
                })
            
            health = app_metrics.get_health_metrics()
            dashboard_data["health"] = health
            
            return dashboard_data
        
        dashboard_data = create_dashboard_export(app_metrics.collector)
        
        # Verify dashboard structure
        assert "timestamp" in dashboard_data
        assert "metrics" in dashboard_data
        assert "health" in dashboard_data
        
        # Check metrics categorization
        assert len(dashboard_data["metrics"]) > 0
        assert "health" in dashboard_data["health"]
    
    def test_advanced_example_script_execution(self):
        """Test that the advanced metrics example script can be executed."""
        example_path = Path(__file__).parent.parent.parent / "examples/advanced/metrics_monitoring_advanced.py"
        
        assert example_path.exists(), f"Advanced example script not found: {example_path}"
        
        # Test script compilation
        with open(example_path, 'r') as f:
            script_content = f.read()
        
        # Should be valid Python
        compile(script_content, str(example_path), 'exec')
        
        # Test that main function exists and is async
        assert "async def main():" in script_content
        assert "if __name__ == \"__main__\":" in script_content
        assert "asyncio.run(main())" in script_content


class TestMetricsIntegration:
    """Integration tests for metrics examples."""
    
    def test_metrics_end_to_end_workflow(self):
        """Test complete metrics workflow from collection to export."""
        # Create collector
        collector = MetricsCollector()
        
        # Simulate application workflow
        collector.increment_counter("user_sessions", labels={"status": "active"})
        collector.set_gauge("memory_usage", 512, labels={"component": "app"})
        
        # Simulate API requests with timing
        with collector.timer("api_request", labels={"endpoint": "/api/data"}):
            time.sleep(0.01)  # Simulate processing
        
        # Simulate AI operations
        collector.record_timer("ai_processing", 1.2, labels={"model": "gpt-4"})
        collector.increment_counter("ai_tokens", value=150, labels={"model": "gpt-4"})
        
        # Export to different formats
        prometheus_exporter = PrometheusExporter(collector)
        json_exporter = JSONExporter(collector)
        
        prometheus_output = prometheus_exporter.export()
        json_output = json_exporter.export()
        
        # Verify outputs
        assert len(prometheus_output) > 0
        assert len(json_output) > 0
        
        # Parse JSON and verify structure
        json_data = json.loads(json_output)
        assert isinstance(json_data, list)
        assert len(json_data) > 0
        
        # Verify specific metrics are present
        metric_names = [m["name"] for m in json_data]
        assert "user_sessions" in metric_names
        assert "memory_usage" in metric_names
        assert any("api_request" in name for name in metric_names)
        assert any("ai_processing" in name for name in metric_names)
        assert "ai_tokens" in metric_names
    
    def test_error_handling_and_recovery(self):
        """Test metrics collection during error conditions."""
        collector = MetricsCollector()
        
        # Simulate normal operations
        collector.increment_counter("operations", labels={"status": "success"})
        collector.record_timer("operation_time", 0.1, labels={"type": "normal"})
        
        # Simulate error conditions
        collector.increment_counter("operations", labels={"status": "error"})
        collector.record_timer("operation_time", 2.5, labels={"type": "slow"})
        
        # Get metrics and analyze
        all_metrics = collector.get_all_metrics()
        
        # Count success vs error operations
        success_metrics = [m for m in all_metrics if m.name == "operations" and "status" in m.labels and m.labels["status"] == "success"]
        error_metrics = [m for m in all_metrics if m.name == "operations" and "status" in m.labels and m.labels["status"] == "error"]
        
        assert len(success_metrics) > 0
        assert len(error_metrics) > 0
        
        # Check timing metrics
        timing_metrics = {m.name: m.value for m in all_metrics if "operation_time" in m.name}
        assert "operation_time_min_seconds" in timing_metrics
        assert "operation_time_max_seconds" in timing_metrics
        assert timing_metrics["operation_time_min_seconds"] <= timing_metrics["operation_time_max_seconds"]
    
    def test_metrics_performance(self):
        """Test metrics collection performance."""
        collector = MetricsCollector()
        
        # Measure performance of bulk operations
        start_time = time.time()
        
        # Record many metrics
        for i in range(1000):
            collector.increment_counter("bulk_operations", value=1)
            if i % 100 == 0:
                collector.set_gauge("progress", i, labels={"step": "bulk"})
        
        # Record timers
        for i in range(100):
            collector.record_timer("timer_test", 0.001 * i, labels={"batch": str(i // 10)})
        
        collection_time = time.time() - start_time
        
        # Get metrics
        start_time = time.time()
        all_metrics = collector.get_all_metrics()
        retrieval_time = time.time() - start_time
        
        # Performance assertions
        assert collection_time < 1.0  # Should complete in under 1 second
        assert retrieval_time < 0.5   # Retrieval should be fast
        assert len(all_metrics) > 1000  # Should have many metrics
        
        # Verify data integrity
        counter_metrics = [m for m in all_metrics if m.name == "bulk_operations"]
        assert sum(m.value for m in counter_metrics) == 1000
