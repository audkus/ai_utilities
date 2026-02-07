"""
Tests for metrics module.
"""

import json
import time
import pytest
import threading
from unittest.mock import patch, MagicMock
from collections import defaultdict, deque

from ai_utilities.metrics import (
    MetricType,
    MetricValue,
    HistogramBucket,
    MetricsCollector,
    PrometheusExporter,
    OpenTelemetryExporter,
    JSONExporter,
    MetricsRegistry,
    Timer,
    monitor_requests,
    metrics
)


class TestMetricType:
    """Test MetricType enum."""
    
    def test_metric_type_values(self):
        """Test that MetricType has correct values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.TIMER.value == "timer"


class TestMetricValue:
    """Test MetricValue dataclass."""
    
    def test_metric_value_creation(self):
        """Test MetricValue creation."""
        timestamp = time.time()
        metric = MetricValue(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            labels={"env": "test"},
            unit="count",
            description="Test metric"
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.COUNTER
        assert metric.timestamp == timestamp
        assert metric.labels == {"env": "test"}
        assert metric.unit == "count"
        assert metric.description == "Test metric"


class TestHistogramBucket:
    """Test HistogramBucket dataclass."""
    
    def test_histogram_bucket_creation(self):
        """Test HistogramBucket creation."""
        bucket = HistogramBucket(upper_bound=1.0, count=5)
        
        assert bucket.upper_bound == 1.0
        assert bucket.count == 5


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector(max_history=100)
        
        assert collector.max_history == 100
        assert isinstance(collector.counters, defaultdict)
        assert isinstance(collector.gauges, defaultdict)
        assert isinstance(collector.histograms, defaultdict)
        assert isinstance(collector.timers, defaultdict)
        assert isinstance(collector.labels, dict)
        assert isinstance(collector.lock, type(threading.Lock()))
    
    def test_increment_counter(self):
        """Test incrementing a counter."""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", 1.0)
        assert collector.counters["test_counter"] == 1.0
        
        collector.increment_counter("test_counter", 2.5)
        assert collector.counters["test_counter"] == 3.5
    
    def test_set_gauge(self):
        """Test setting a gauge value."""
        collector = MetricsCollector()
        
        collector.set_gauge("test_gauge", 42.5)
        assert collector.gauges["test_gauge"] == 42.5
        
        collector.set_gauge("test_gauge", 100.0)
        assert collector.gauges["test_gauge"] == 100.0
    
    def test_create_histogram_default_buckets(self):
        """Test creating a histogram with default buckets."""
        collector = MetricsCollector()
        
        collector.create_histogram("test_histogram", "Test histogram")
        
        key = "test_histogram"
        assert key in collector.histograms
        buckets = collector.histograms[key]
        
        # Check default buckets
        expected_bounds = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, float('inf')]
        assert len(buckets) == len(expected_bounds)
        for i, bound in enumerate(expected_bounds):
            assert buckets[i].upper_bound == bound
            assert buckets[i].count == 0
    
    def test_observe_histogram(self):
        """Test observing histogram values."""
        collector = MetricsCollector()
        collector.create_histogram("test_histogram", "Test", [1.0, 5.0, 10.0])
        
        # Observe value 2.5 (should increment buckets 5.0 and 10.0, but not 1.0)
        collector.observe_histogram("test_histogram", 2.5)
        
        buckets = collector.histograms["test_histogram"]
        assert buckets[0].count == 0  # 1.0 bucket (2.5 > 1.0)
        assert buckets[1].count == 1  # 5.0 bucket (2.5 <= 5.0)
        assert buckets[2].count == 1  # 10.0 bucket (2.5 <= 10.0)
    
    def test_record_timer(self):
        """Test recording timer values."""
        collector = MetricsCollector(max_history=3)
        
        collector.record_timer("test_timer", 1.5)
        collector.record_timer("test_timer", 2.0)
        collector.record_timer("test_timer", 0.8)
        
        timer_values = list(collector.timers["test_timer"])
        assert timer_values == [1.5, 2.0, 0.8]
        
        # Test max_history limit
        collector.record_timer("test_timer", 3.0)
        timer_values = list(collector.timers["test_timer"])
        assert len(timer_values) == 3
        assert timer_values == [2.0, 0.8, 3.0]  # 1.5 should be dropped
    
    def test_get_all_metrics(self):
        """Test getting all metrics as MetricValue objects."""
        collector = MetricsCollector()
        
        # Add some metrics
        collector.increment_counter("test_counter", 5.0, {"env": "test"})
        collector.set_gauge("test_gauge", 42.5, {"env": "test"})
        collector.create_histogram("test_histogram", "Test", [1.0, 5.0])
        collector.observe_histogram("test_histogram", 2.0, {"env": "test"})
        collector.record_timer("test_timer", 1.5, {"env": "test"})
        
        metrics = collector.get_all_metrics()
        
        # Should include our metrics plus standard ones
        metric_names = [m.name for m in metrics]
        assert "test_counter" in metric_names
        assert "test_gauge" in metric_names
        assert "test_histogram_bucket" in metric_names  # Histogram buckets
        
        # Check metric types and values
        counter_metrics = [m for m in metrics if m.name == "test_counter" and m.labels.get("env") == "test"]
        gauge_metrics = [m for m in metrics if m.name == "test_gauge" and m.labels.get("env") == "test"]
        
        # Find the correct metric types
        counter_metric = next(m for m in counter_metrics if m.metric_type == MetricType.COUNTER)
        gauge_metric = next(m for m in gauge_metrics if m.metric_type == MetricType.GAUGE)
        
        assert counter_metric.metric_type == MetricType.COUNTER
        assert counter_metric.value == 5.0
        
        assert gauge_metric.metric_type == MetricType.GAUGE
        assert gauge_metric.value == 42.5
    
    def test_reset(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()
        
        # Add some metrics
        collector.increment_counter("test_counter", 5.0)
        collector.set_gauge("test_gauge", 42.5)
        
        # Reset
        collector.reset()
        
        # Check that custom metrics are cleared
        assert "test_counter" not in collector.counters
        assert "test_gauge" not in collector.gauges


class TestPrometheusExporter:
    """Test PrometheusExporter class."""
    
    def test_export_empty_metrics(self):
        """Test exporting empty metrics."""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)
        
        output = exporter.export()
        
        # Should contain standard metrics with HELP and TYPE
        assert any("HELP" in line for line in output.split('\n'))  # Contract: contains help text
        assert any("TYPE" in line for line in output.split('\n'))  # Contract: contains type definitions
        assert any("ai_requests_total" in line for line in output.split('\n'))  # Contract: contains metric name


class TestMetricsRegistry:
    """Test MetricsRegistry class."""
    
    def test_singleton_pattern(self):
        """Test that MetricsRegistry follows singleton pattern."""
        registry1 = MetricsRegistry()
        registry2 = MetricsRegistry()
        
        assert registry1 is registry2
    
    def test_record_request(self):
        """Test recording an AI request."""
        registry = MetricsRegistry()
        
        registry.record_request(success=True, duration=1.5, tokens=100, model="gpt-4")
        
        metrics = registry.collector.get_all_metrics()
        metric_names = [m.name for m in metrics]
        
        assert "ai_requests_total" in metric_names
        assert "ai_requests_successful" in metric_names
        
        # Check that failed requests metric exists but has zero value (for successful request)
        failed_metrics = [m for m in metrics if m.name == "ai_requests_failed" and m.value > 0]
        assert len(failed_metrics) == 0  # Should not have any failed requests with value > 0
        
        # Check token metric with model label
        token_metric = next((m for m in metrics if m.name == "tokens_used_total" and m.labels.get("model") == "gpt-4"), None)
        assert token_metric is not None
        assert token_metric.value == 100.0
    
    def test_export_methods(self):
        """Test export methods."""
        registry = MetricsRegistry()
        
        # Add some data
        registry.record_request(success=True, duration=1.5, tokens=100)
        
        prometheus_output = registry.export_prometheus()
        opentelemetry_output = registry.export_opentelemetry()
        json_output = registry.export_json()
        
        assert isinstance(prometheus_output, str)
        assert isinstance(opentelemetry_output, dict)
        assert isinstance(json_output, str)
        
        # JSON should be parseable
        data = json.loads(json_output)
        assert isinstance(data, list)


class TestTimer:
    """Test Timer context manager."""
    
    def test_timer_context_manager(self):
        """Test Timer context manager functionality."""
        collector = MetricsCollector()
        
        # Import and patch the metrics module directly
        from ai_utilities.metrics import metrics
        original_collector = metrics.collector
        
        try:
            # Use our test collector
            metrics.collector = collector
            timer = Timer("test_timer", {"env": "test"})
            
            with timer:
                time.sleep(0.01)  # Reduced sleep time
        
        # Check that timer was recorded
            key = "test_timer|env=test"  # Internal key format uses | not {}
            assert key in collector.timers
            assert len(collector.timers[key]) == 1
            assert collector.timers[key][0] > 0.01  # Should be at least the sleep time
            assert collector.timers[key][0] >= 0.01  # Should be at least 0.01 seconds
        
        finally:
            # Restore original collector
            metrics.collector = original_collector


class TestGlobalMetrics:
    """Test global metrics instance."""
    
    def test_global_metrics_instance(self):
        """Test that global metrics instance is available."""
        from ai_utilities.metrics import metrics
        
        assert isinstance(metrics, MetricsRegistry)
        
        # Should be able to use it
        metrics.record_request(success=True, duration=1.0, tokens=50)
        
        prometheus_output = metrics.export_prometheus()
        assert isinstance(prometheus_output, str)
        assert "ai_requests_total" in prometheus_output


class TestIntegration:
    """Integration tests for the metrics system."""
    
    def test_complete_workflow(self):
        """Test a complete metrics workflow."""
        collector = MetricsCollector()
        
        # Simulate AI operations using basic collector methods
        collector.increment_counter("ai_requests_total", 2.0)
        collector.increment_counter("ai_requests_successful", 1.0)
        collector.increment_counter("ai_requests_failed", 1.0)
        collector.increment_counter("cache_hits_total", 1.0)
        collector.increment_counter("cache_misses_total", 1.0)
        collector.set_gauge("cache_size", 1500.0)
        collector.increment_counter("provider_errors_total", 1.0, {"provider": "openai"})
        collector.set_gauge("active_clients", 3.0)
        
        # Export in different formats
        prometheus_exporter = PrometheusExporter(collector)
        prometheus = prometheus_exporter.export()
        
        json_exporter = JSONExporter(collector)
        json_output = json_exporter.export()
        
        # Verify exports contain expected data
        assert "ai_requests_total 2.0" in prometheus
        assert "ai_requests_successful 1.0" in prometheus
        assert "ai_requests_failed 1.0" in prometheus
        assert "cache_hits_total 1.0" in prometheus
        assert "cache_misses_total 1.0" in prometheus
        assert "cache_size 1500.0" in prometheus
        assert 'provider_errors_total{provider="openai"} 1.0' in prometheus
        assert "active_clients 3.0" in prometheus
        
        # Verify JSON export
        assert isinstance(json_output, str)
        json_data = json.loads(json_output)
        assert isinstance(json_data, list)
        assert len(json_data) > 0
        
        # Check specific metrics in JSON
        request_metric = next((m for m in json_data if m["name"] == "ai_requests_total"), None)
        assert request_metric is not None
        assert request_metric["value"] == 2.0
