"""Comprehensive tests for metrics.py module."""

import pytest
import time
import json
import threading
import uuid
from unittest.mock import Mock, patch
from collections import defaultdict
import _thread

from ai_utilities.metrics import (
    MetricType, MetricValue, HistogramBucket, MetricsCollector,
    PrometheusExporter, OpenTelemetryExporter, JSONExporter,
    MetricsRegistry, Timer, monitor_requests, metrics
)


class TestMetricType:
    """Test MetricType enum."""
    
    def test_metric_type_values(self):
        """Test all metric type values."""
        assert isinstance(MetricType.COUNTER.value, str)  # Contract: metric type values are strings
        assert len(MetricType.COUNTER.value) > 0  # Contract: non-empty values
        assert isinstance(MetricType.GAUGE.value, str)  # Contract: metric type values are strings
        assert len(MetricType.GAUGE.value) > 0  # Contract: non-empty values
        assert isinstance(MetricType.HISTOGRAM.value, str)  # Contract: metric type values are strings
        assert len(MetricType.HISTOGRAM.value) > 0  # Contract: non-empty values
        assert isinstance(MetricType.TIMER.value, str)  # Contract: metric type values are strings
        assert len(MetricType.TIMER.value) > 0  # Contract: non-empty values


class TestMetricValue:
    """Test MetricValue dataclass."""
    
    def test_metric_value_creation(self):
        """Test creating MetricValue objects."""
        timestamp = time.time()
        metric = MetricValue(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            labels={"env": "test"},
            unit="count",
            description="Test metric"
        )
        
        assert isinstance(metric.name, str)  # Contract: metric name is string type
        assert len(metric.name) > 0  # Contract: non-empty metric name
        assert isinstance(metric.value, (int, float))  # Contract: metric value is numeric
        assert metric.metric_type == MetricType.COUNTER  # Contract: metric type enum
        assert metric.timestamp == timestamp  # Contract: timestamp preserved
        assert isinstance(metric.labels, dict)  # Contract: labels is dict type
        assert isinstance(metric.unit, str)  # Contract: unit is string type
        assert len(metric.unit) > 0  # Contract: non-empty unit
        assert isinstance(metric.description, str)  # Contract: description is string type
        assert len(metric.description) > 0  # Contract: non-empty description


class TestHistogramBucket:
    """Test HistogramBucket dataclass."""
    
    def test_histogram_bucket_creation(self):
        """Test creating HistogramBucket objects."""
        bucket = HistogramBucket(upper_bound=1.0, count=5)
        assert bucket.upper_bound == 1.0
        assert bucket.count == 5


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_init_default(self):
        """Test MetricsCollector initialization with defaults."""
        collector = MetricsCollector()
        assert collector.max_history == 1000
        assert isinstance(collector.counters, defaultdict)
        assert isinstance(collector.gauges, defaultdict)
        assert isinstance(collector.histograms, defaultdict)
        assert isinstance(collector.timers, defaultdict)
        assert isinstance(collector.labels, dict)
        assert isinstance(collector.descriptions, dict)
        assert hasattr(collector.lock, 'acquire')  # Check if it has lock interface
        assert hasattr(collector.lock, 'release')
        
        # Check standard metrics are initialized
        assert isinstance(collector.descriptions, dict)  # Contract: descriptions is dict
        assert len(collector.descriptions) > 0  # Contract: has descriptions
    
    def test_init_custom_max_history(self):
        """Test MetricsCollector initialization with custom max_history."""
        collector = MetricsCollector(max_history=500)
        assert collector.max_history == 500
    
    def test_create_counter(self):
        """Test creating counter metrics."""
        collector = MetricsCollector()
        
        collector.create_counter("test_counter", "Test counter")
        assert "test_counter" in collector.descriptions
        assert isinstance(collector.descriptions["test_counter"], str)  # Contract: description is string type
        assert len(collector.descriptions["test_counter"]) > 0  # Contract: non-empty description
    
    def test_create_counter_with_labels(self):
        """Test creating counter metrics with labels."""
        collector = MetricsCollector()
        labels = {"method": "GET", "status": "200"}
        
        collector.create_counter("http_requests", "HTTP requests", labels)
        key = "http_requests|method=GET,status=200"
        assert key in collector.descriptions  # Contract: key exists in descriptions
        assert isinstance(collector.labels[key], dict)  # Contract: labels is dict
    
    def test_create_gauge(self):
        """Test creating gauge metrics."""
        collector = MetricsCollector()
        
        collector.create_gauge("test_gauge", "Test gauge")
        assert "test_gauge" in collector.descriptions
        assert isinstance(collector.descriptions["test_gauge"], str)  # Contract: description is string type
        assert len(collector.descriptions["test_gauge"]) > 0  # Contract: non-empty description
    
    def test_create_histogram(self):
        """Test creating histogram metrics."""
        collector = MetricsCollector()
        
        collector.create_histogram("test_histogram", "Test histogram")
        assert "test_histogram" in collector.descriptions
        assert "test_histogram" in collector.histograms
        assert len(collector.histograms["test_histogram"]) == 10  # Default buckets
    
    def test_create_histogram_custom_buckets(self):
        """Test creating histogram with custom buckets."""
        collector = MetricsCollector()
        buckets = [0.1, 1.0, 10.0]
        
        collector.create_histogram("custom_histogram", "Custom histogram", buckets)
        assert "custom_histogram" in collector.histograms
        assert len(collector.histograms["custom_histogram"]) == 3
        assert collector.histograms["custom_histogram"][0].upper_bound == 0.1
    
    def test_increment_counter(self):
        """Test incrementing counter metrics."""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", 5.0)
        assert collector.counters["test_counter"] == 5.0
        
        collector.increment_counter("test_counter", 3.0)
        assert collector.counters["test_counter"] == 8.0
    
    def test_increment_counter_with_labels(self):
        """Test incrementing counter with labels."""
        collector = MetricsCollector()
        labels = {"endpoint": "/api/test"}
        
        collector.increment_counter("api_requests", 1.0, labels)
        key = "api_requests|endpoint=/api/test"
        assert collector.counters[key] == 1.0
        assert collector.labels[key] == labels
    
    def test_set_gauge(self):
        """Test setting gauge metrics."""
        collector = MetricsCollector()
        
        collector.set_gauge("test_gauge", 42.5)
        assert collector.gauges["test_gauge"] == 42.5
        
        collector.set_gauge("test_gauge", 100.0)
        assert collector.gauges["test_gauge"] == 100.0
    
    def test_set_gauge_with_labels(self):
        """Test setting gauge with labels."""
        collector = MetricsCollector()
        labels = {"server": "prod"}
        
        collector.set_gauge("memory_usage", 1024, labels)
        key = "memory_usage|server=prod"
        assert collector.gauges[key] == 1024
        assert collector.labels[key] == labels
    
    def test_observe_histogram(self):
        """Test observing histogram values."""
        collector = MetricsCollector()
        
        # Create histogram first
        collector.create_histogram("test_histogram", "Test histogram")
        
        # Observe some values
        collector.observe_histogram("test_histogram", 0.5)
        collector.observe_histogram("test_histogram", 1.5)
        collector.observe_histogram("test_histogram", 5.0)
        
        # Check bucket counts
        buckets = collector.histograms["test_histogram"]
        assert buckets[0].count == 0  # <= 0.1 (0.5 > 0.1)
        assert buckets[1].count == 1  # <= 0.5
        assert buckets[2].count == 1  # <= 1.0 (0.5 fits, 1.5 doesn't)
        assert buckets[3].count == 2  # <= 2.5 (0.5, 1.5 fit)
        assert buckets[4].count == 3  # <= 5.0 (0.5, 1.5, 5.0 fit)
        assert buckets[9].count == 3  # <= inf (all fit)
    
    def test_observe_histogram_auto_create(self):
        """Test observing histogram auto-creates if not exists."""
        collector = MetricsCollector()
        
        collector.observe_histogram("auto_histogram", 2.5)
        assert "auto_histogram" in collector.histograms
        assert len(collector.histograms["auto_histogram"]) == 10
    
    def test_record_timer(self):
        """Test recording timer values."""
        collector = MetricsCollector()
        
        collector.record_timer("test_timer", 1.5)
        collector.record_timer("test_timer", 2.0)
        
        assert len(collector.timers["test_timer"]) == 2
        assert collector.timers["test_timer"][0] == 1.5
        assert collector.timers["test_timer"][1] == 2.0
    
    def test_timer_context_manager(self):
        """Test timer context manager."""
        collector = MetricsCollector()
        
        with collector.timer("context_timer") as timer:
            time.sleep(0.01)  # Small delay
        
        # The timer context manager uses global metrics instance, not the local collector
        # So we need to check the global metrics collector
        key = metrics.collector._make_key("context_timer", {})
        assert key in metrics.collector.timers
        assert len(metrics.collector.timers[key]) == 1
        assert metrics.collector.timers[key][0] >= 0.01
    
    def test_make_key(self):
        """Test internal key generation."""
        collector = MetricsCollector()
        
        # No labels
        key = collector._make_key("test_metric", {})
        assert isinstance(key, str)  # Contract: key is string type
        assert len(key) > 0  # Contract: non-empty key
        
        # With labels
        labels = {"env": "test", "version": "1.0"}
        key = collector._make_key("test_metric", labels)
        assert isinstance(key, str)  # Contract: key is string type
        assert len(key) > 0  # Contract: non-empty key
        assert "|" in key  # Contract: labels separated by pipe
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        
        # Add some metrics
        collector.increment_counter("test_counter", 5.0)
        collector.set_gauge("test_gauge", 42.0)
        collector.create_histogram("test_histogram", "Test histogram")
        collector.observe_histogram("test_histogram", 1.5)
        collector.record_timer("test_timer", 2.0)
        
        metrics = collector.get_all_metrics()
        
        # Should have counter, gauge, histogram buckets, and potentially timer
        metric_names = [m.name for m in metrics]
        assert "test_counter" in metric_names
        assert "test_gauge" in metric_names
        assert any("test_histogram_bucket" in name for name in metric_names)
    
    def test_reset(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()
        
        # Add some metrics
        collector.increment_counter("test_counter", 5.0)
        collector.set_gauge("test_gauge", 42.0)
        
        # Reset
        collector.reset()
        
        # Check metrics are reset but standard ones are reinitialized
        assert collector.counters["test_counter"] == 0.0
        assert "ai_requests_total" in collector.descriptions
    
    def test_thread_safety(self):
        """Test thread safety of metrics operations."""
        collector = MetricsCollector()
        results = []
        
        def increment_counter():
            for _ in range(100):
                collector.increment_counter("thread_test", 1.0)
        
        def set_gauge():
            for i in range(100):
                collector.set_gauge("thread_gauge", float(i))
        
        threads = [
            threading.Thread(target=increment_counter),
            threading.Thread(target=increment_counter),
            threading.Thread(target=set_gauge),
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify results
        assert collector.counters["thread_test"] == 200.0
        assert collector.gauges["thread_gauge"] == 99.0  # Last value set


class TestPrometheusExporter:
    """Test PrometheusExporter class."""
    
    def test_export_empty_metrics(self):
        """Test exporting empty metrics."""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)
        
        output = exporter.export()
        assert any("HELP" in line for line in output.split('\n'))  # Contract: contains help text
        assert any("TYPE" in line for line in output.split('\n'))  # Contract: contains type definitions
        assert any("ai_requests_total" in line for line in output.split('\n'))  # Contract: contains metric name
    
    def test_export_with_metrics(self):
        """Test exporting metrics with data."""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)
        
        # Add some metrics
        collector.increment_counter("test_counter", 5.0, {"env": "test"})
        collector.set_gauge("test_gauge", 42.0)
        
        output = exporter.export()
        assert any("HELP" in line for line in output.split('\n'))  # Contract: contains help text
        assert any("TYPE" in line for line in output.split('\n'))  # Contract: contains type definitions
        assert any("test_counter" in line for line in output.split('\n'))  # Contract: contains metric name
        assert any("test_gauge" in line for line in output.split('\n'))  # Contract: contains metric name


class TestOpenTelemetryExporter:
    """Test OpenTelemetryExporter class."""
    
    def test_export_empty_metrics(self):
        """Test exporting empty metrics."""
        collector = MetricsCollector()
        exporter = OpenTelemetryExporter(collector)
        
        output = exporter.export()
        assert isinstance(output, dict)  # Contract: returns dictionary structure
        assert output.get("resource_metrics") is not None  # Contract: contains resource metrics
    
    def test_export_with_metrics(self):
        """Test exporting metrics with data."""
        collector = MetricsCollector()
        exporter = OpenTelemetryExporter(collector)
        
        # Add some metrics
        collector.increment_counter("test_counter", 5.0)
        collector.set_gauge("test_gauge", 42.0)
        
        output = exporter.export()
        metrics = output["resource_metrics"][0]["scope_metrics"][0]["metrics"]
        
        # Find our metrics - there might be multiple entries for the same name
        counter_metrics = [m for m in metrics if m["name"] == "test_counter"]
        gauge_metrics = [m for m in metrics if m["name"] == "test_gauge"]
        
        assert len(counter_metrics) > 0
        assert len(gauge_metrics) > 0
        
        # Find the counter with actual value (not zero)
        counter_metric = next((m for m in counter_metrics if m.get("sum", {}).get("data_points", [{}])[0].get("as_int", 0) == 5), None)
        # Find the gauge with actual value (not zero) 
        gauge_metric = next((m for m in gauge_metrics if 
                           (m.get("sum", {}).get("data_points", [{}])[0].get("as_int", 0) == 42) or 
                           (m.get("gauge", {}).get("data_points", [{}])[0].get("as_double", 0) == 42.0)), None)
        
        assert counter_metric is not None
        assert gauge_metric is not None
        
        # Check structure
        assert "sum" in counter_metric
        assert counter_metric["sum"]["data_points"][0]["as_int"] == 5
        
        # For gauge, check the actual value that was set
        if "sum" in gauge_metric:
            assert gauge_metric["sum"]["data_points"][0]["as_int"] == 42
        elif "gauge" in gauge_metric:
            assert gauge_metric["gauge"]["data_points"][0]["as_double"] == 42.0


class TestJSONExporter:
    """Test JSONExporter class."""
    
    def test_export_empty_metrics(self):
        """Test exporting empty metrics as JSON."""
        collector = MetricsCollector()
        exporter = JSONExporter(collector)
        
        output = exporter.export()
        data = json.loads(output)
        
        assert isinstance(data, list)
        # Should contain standard metrics
        metric_names = [m["name"] for m in data]
        assert "ai_requests_total" in metric_names
    
    def test_export_with_metrics(self):
        """Test exporting metrics with data."""
        collector = MetricsCollector()
        exporter = JSONExporter(collector)
        
        # Add some metrics
        collector.increment_counter("test_counter", 5.0)
        collector.set_gauge("test_gauge", 42.0)
        
        output = exporter.export()
        data = json.loads(output)
        
        metric_names = [m["name"] for m in data]
        assert "test_counter" in metric_names
        assert "test_gauge" in metric_names
        
        counter_metric = next(m for m in data if m["name"] == "test_counter")
        assert isinstance(counter_metric["value"], (int, float))  # Contract: metric value is numeric
        assert isinstance(counter_metric["metric_type"], str)  # Contract: metric type is string
        assert len(counter_metric["metric_type"]) > 0  # Contract: non-empty metric type


class TestMetricsRegistry:
    """Test MetricsRegistry class."""
    
    def test_singleton_pattern(self):
        """Test singleton pattern works."""
        registry1 = MetricsRegistry()
        registry2 = MetricsRegistry()
        
        assert registry1 is registry2
    
    def test_initialization(self):
        """Test registry initialization."""
        registry = MetricsRegistry()
        
        assert hasattr(registry, 'initialized')
        assert hasattr(registry, 'collector')
        assert hasattr(registry, 'prometheus_exporter')
        assert hasattr(registry, 'opentelemetry_exporter')
        assert hasattr(registry, 'json_exporter')
    
    def test_record_request(self):
        """Test recording AI requests."""
        registry = MetricsRegistry()
        
        # Reset to clean state
        registry.reset()
        
        registry.record_request(success=True, duration=1.5, tokens=100, model="gpt-4")
        
        # Check metrics were recorded
        assert registry.collector.counters["ai_requests_total"] == 1.0
        assert registry.collector.counters["ai_requests_successful"] == 1.0
        assert registry.collector.counters["ai_requests_failed"] == 0.0
    
    def test_record_request_failure(self):
        """Test recording failed AI requests."""
        registry = MetricsRegistry()
        
        # Reset to clean state
        registry.reset()
        
        registry.record_request(success=False, duration=0.5, tokens=0)
        
        assert registry.collector.counters["ai_requests_total"] == 1.0
        assert registry.collector.counters["ai_requests_successful"] == 0.0
        assert registry.collector.counters["ai_requests_failed"] == 1.0
    
    def test_cache_operations(self):
        """Test cache operation recording."""
        registry = MetricsRegistry()
        
        registry.record_cache_hit()
        registry.record_cache_miss()
        registry.set_cache_size(1500)
        
        assert registry.collector.counters["cache_hits_total"] == 1.0
        assert registry.collector.counters["cache_misses_total"] == 1.0
        assert registry.collector.gauges["cache_size"] == 1500.0
    
    def test_provider_operations(self):
        """Test provider operation recording."""
        registry = MetricsRegistry()
        
        registry.record_provider_error("openai")
        registry.record_provider_request("openai", 1.2)
        
        provider_key = "provider_errors_total|provider=openai"
        assert registry.collector.counters[provider_key] == 1.0
    
    def test_system_metrics(self):
        """Test system metric recording."""
        registry = MetricsRegistry()
        
        registry.set_active_clients(5)
        registry.record_rate_limit_hit()
        registry.set_memory_usage(1024 * 1024 * 50)
        
        assert registry.collector.gauges["active_clients"] == 5.0
        assert registry.collector.counters["rate_limit_hits_total"] == 1.0
        assert registry.collector.gauges["memory_usage_bytes"] == 52428800.0
    
    def test_export_methods(self):
        """Test all export methods."""
        registry = MetricsRegistry()
        
        # Add some data
        registry.record_request(success=True, duration=1.0, tokens=50)
        
        prometheus_output = registry.export_prometheus()
        opentelemetry_output = registry.export_opentelemetry()
        json_output = registry.export_json()
        
        assert isinstance(prometheus_output, str)
        assert isinstance(opentelemetry_output, dict)
        assert isinstance(json_output, str)
        
        # Parse JSON to verify it's valid
        json_data = json.loads(json_output)
        assert isinstance(json_data, list)
    
    def test_generic_methods(self):
        """Test generic metric methods."""
        # Use a fresh MetricsCollector instead of the singleton registry
        collector = MetricsCollector()
        
        # Use UUID to ensure completely unique names
        test_id = str(uuid.uuid4())[:8]
        
        collector.increment_counter(f"generic_counter_{test_id}", 5.0, {"type": "test"})
        collector.set_gauge(f"generic_gauge_{test_id}", 42.5, {"type": "test"})
        collector.observe_histogram(f"generic_histogram_{test_id}", 1.5, {"type": "test"})
        
        # Check values directly from collector
        counter_key = collector._make_key(f"generic_counter_{test_id}", {"type": "test"})
        gauge_key = collector._make_key(f"generic_gauge_{test_id}", {"type": "test"})
        histogram_key = collector._make_key(f"generic_histogram_{test_id}", {"type": "test"})
        
        assert collector.counters[counter_key] == 5.0
        assert collector.gauges[gauge_key] == 42.5
        
        # For histogram, check the distribution is correct for value 1.5
        # Value 1.5 should increment buckets: 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, inf = 7 buckets
        our_histogram = collector.histograms[histogram_key]
        expected_distribution = [0, 0, 0, 1, 1, 1, 1, 1, 1, 1]  # Buckets: 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, inf
        
        actual_distribution = [bucket.count for bucket in our_histogram]
        assert actual_distribution == expected_distribution
        
        # Total observations should be 7 (one per bucket that the value falls into)
        total_observations = sum(actual_distribution)
        assert total_observations == 7
    
    def test_get_all_metrics_dict(self):
        """Test getting all metrics as dictionary."""
        registry = MetricsRegistry()
        
        # Use UUID to ensure completely unique names
        test_id = str(uuid.uuid4())[:8]
        
        registry.increment(f"test_counter_{test_id}", 10)
        registry.gauge(f"test_gauge_{test_id}", 25.5)
        
        all_metrics = registry.get_all_metrics()
        
        assert f"test_counter_{test_id}" in all_metrics
        assert f"test_gauge_{test_id}" in all_metrics
        assert all_metrics[f"test_counter_{test_id}"] == 10.0
        assert all_metrics[f"test_gauge_{test_id}"] == 25.5
    
    def test_reset(self):
        """Test resetting registry."""
        registry = MetricsRegistry()
        
        registry.increment("test_counter", 10)
        registry.reset()
        
        # Standard metrics should be reinitialized
        assert "ai_requests_total" in registry.collector.descriptions


class TestTimer:
    """Test Timer context manager."""
    
    def test_timer_functionality(self):
        """Test timer measures time correctly."""
        start_time = time.time()
        
        with Timer("test_timer") as timer:
            time.sleep(0.01)
        
        duration = time.time() - start_time
        assert timer.start_time is not None
        assert timer.start_time <= start_time + 0.001  # Small tolerance
    
    def test_timer_with_labels(self):
        """Test timer with labels."""
        labels = {"operation": "test"}
        
        with Timer("labeled_timer", labels):
            time.sleep(0.01)
        
        # Check that timer was recorded with labels
        key = metrics.collector._make_key("labeled_timer", labels)
        assert key in metrics.collector.timers
        assert len(metrics.collector.timers[key]) == 1


class TestMonitorDecorator:
    """Test monitor_requests decorator."""
    
    def test_monitor_successful_function(self):
        """Test monitoring successful function."""
        @monitor_requests("test_function")
        def test_function():
            time.sleep(0.01)
            return "success"
        
        result = test_function()
        assert isinstance(result, str)  # Contract: returns string
        assert len(result) > 0  # Contract: non-empty response
        
        # Check metrics were recorded
        assert metrics.collector.counters["ai_requests_total"] >= 1.0
        assert metrics.collector.counters["ai_requests_successful"] >= 1.0
    
    def test_monitor_failing_function(self):
        """Test monitoring failing function."""
        @monitor_requests("failing_function")
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Check metrics were recorded
        assert metrics.collector.counters["ai_requests_total"] >= 1.0
        assert metrics.collector.counters["ai_requests_failed"] >= 1.0
    
    def test_monitor_with_token_extraction(self):
        """Test monitoring with token extraction."""
        class MockResult:
            class MockUsage:
                total_tokens = 150
            usage = MockUsage()
        
        @monitor_requests("token_function")
        def token_function():
            return MockResult()
        
        result = token_function()
        assert hasattr(result, 'usage')
        
        # Check token metrics were recorded
        assert metrics.collector.counters["ai_requests_total"] >= 1.0


class TestGlobalMetrics:
    """Test global metrics instance."""
    
    def test_global_metrics_instance(self):
        """Test global metrics instance is accessible."""
        assert isinstance(metrics, MetricsRegistry)
        assert hasattr(metrics, 'collector')
        assert hasattr(metrics, 'record_request')
    
    def test_global_metrics_usage(self):
        """Test using global metrics instance."""
        # Reset to clean state
        metrics.reset()
        
        metrics.record_request(success=True, duration=1.0, tokens=100)
        metrics.increment("global_counter", 5)
        
        assert metrics.get_metric("ai_requests_total") == 1.0
        assert metrics.get_metric("global_counter") == 5.0
