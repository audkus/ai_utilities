"""
Simple tests for metrics module.
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
        
        # Clear any existing metrics to ensure test isolation
        registry.collector.reset()
        
        registry.record_request(success=True, duration=1.5, tokens=100, model="gpt-4")
        
        metrics = registry.collector.get_all_metrics()
        metric_names = [m.name for m in metrics]
        metric_values = {m.name: m.value for m in metrics if m.name == "ai_requests_failed"}
        
        assert "ai_requests_total" in metric_names
        assert "ai_requests_successful" in metric_names
        # ai_requests_failed counter should exist but have value 0 for successful requests
        assert "ai_requests_failed" in metric_names
        assert metric_values.get("ai_requests_failed", 0) == 0
        # Check for tokens metric (format might be different)
        assert any("tokens_used_total" in name for name in metric_names)
    
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
        registry = MetricsRegistry()
        
        # Reset to ensure clean state for integration test
        registry.reset()
        
        # Simulate AI operations
        registry.record_request(success=True, duration=1.2, tokens=100, model="gpt-4")
        registry.record_request(success=False, duration=0.8, tokens=0, model="gpt-3.5")
        registry.record_cache_hit()
        registry.record_cache_miss()
        registry.set_cache_size(1500)
        registry.record_provider_error("openai")
        registry.set_active_clients(3)
        
        # Export in different formats
        prometheus = registry.export_prometheus()
        opentelemetry = registry.export_opentelemetry()
        json_output = registry.export_json()
        
        # Verify exports contain expected data
        assert "ai_requests_total 2.0" in prometheus
        assert "ai_requests_successful 1.0" in prometheus
        assert "ai_requests_failed 1.0" in prometheus
        assert "cache_hits_total 1.0" in prometheus
        assert "cache_misses_total 1.0" in prometheus
        assert "cache_size 1500" in prometheus  # Note: no .0 for cache_size
        assert "provider_errors_total{provider=\"openai\"} 1.0" in prometheus
        assert "active_clients 3" in prometheus  # Note: no .0 for active_clients
        
        # OpenTelemetry structure
        assert "resource_metrics" in opentelemetry
        metrics_data = opentelemetry["resource_metrics"][0]["scope_metrics"][0]["metrics"]
        metric_names = [m["name"] for m in metrics_data]
        assert "ai_requests_total" in metric_names
        
        # JSON structure
        json_data = json.loads(json_output)
        json_metric_names = [m["name"] for m in json_data]
        assert "ai_requests_total" in json_metric_names
