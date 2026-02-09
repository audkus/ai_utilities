"""Corrected extended tests for metrics.py based on actual API."""

import pytest
import time
import json
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional, List, Union

from ai_utilities.metrics import (
    MetricType, MetricValue, HistogramBucket, MetricsCollector,
    PrometheusExporter, OpenTelemetryExporter, JSONExporter, Timer
)


class TestMetricsCorrected:
    """Corrected test cases for metrics based on actual API."""

    def test_metric_type_enum_values(self):
        """Test MetricType enum values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.TIMER.value == "timer"

    def test_metric_value_dataclass(self):
        """Test MetricValue dataclass functionality."""
        timestamp = time.time()
        labels = {"provider": "openai", "model": "gpt-4"}
        
        metric = MetricValue(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            labels=labels,
            unit="requests",
            description="Test metric for unit testing"
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.COUNTER
        assert metric.timestamp == timestamp
        assert metric.labels == labels
        assert metric.unit == "requests"
        assert metric.description == "Test metric for unit testing"

    def test_histogram_bucket_dataclass(self):
        """Test HistogramBucket dataclass functionality."""
        bucket = HistogramBucket(upper_bound=100.0, count=5)
        
        assert bucket.upper_bound == 100.0
        assert bucket.count == 5

    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization with custom max_history."""
        collector = MetricsCollector(max_history=500)
        
        assert collector.max_history == 500
        assert hasattr(collector, 'counters')
        assert hasattr(collector, 'gauges')
        assert hasattr(collector, 'histograms')
        assert hasattr(collector, 'timers')
        assert hasattr(collector, 'lock')

    def test_metrics_collector_standard_metrics_initialization(self):
        """Test that standard metrics are initialized."""
        collector = MetricsCollector()
        
        # Should have standard metrics created
        assert "ai_requests_total" in collector.descriptions
        assert "ai_requests_successful" in collector.descriptions
        assert "ai_response_duration_seconds" in collector.descriptions
        assert "cache_hits_total" in collector.descriptions

    def test_create_counter(self):
        """Test creating a counter metric."""
        collector = MetricsCollector()
        
        # Create counter with description and labels
        collector.create_counter("test_counter", "Test counter", {"provider": "openai"})
        
        # Check that description and labels are stored
        key = collector._make_key("test_counter", {"provider": "openai"})
        assert key in collector.descriptions
        assert collector.descriptions[key] == "Test counter"
        assert key in collector.labels
        assert collector.labels[key] == {"provider": "openai"}

    def test_create_gauge(self):
        """Test creating a gauge metric."""
        collector = MetricsCollector()
        
        # Create gauge with description
        collector.create_gauge("test_gauge", "Test gauge")
        
        # Check that description is stored
        key = collector._make_key("test_gauge", {})
        assert key in collector.descriptions
        assert collector.descriptions[key] == "Test gauge"

    def test_create_histogram(self):
        """Test creating a histogram metric."""
        collector = MetricsCollector()
        
        # Create histogram with custom buckets
        custom_buckets = [0.1, 1.0, 10.0, float('inf')]
        collector.create_histogram("test_histogram", "Test histogram", custom_buckets)
        
        # Check that histogram is created with correct buckets
        key = collector._make_key("test_histogram", {})
        assert key in collector.histograms
        assert len(collector.histograms[key]) == len(custom_buckets)
        assert collector.histograms[key][0].upper_bound == 0.1
        assert collector.histograms[key][-1].upper_bound == float('inf')

    def test_increment_counter(self):
        """Test incrementing a counter metric."""
        collector = MetricsCollector()
        
        # Increment counter
        collector.increment_counter("test_counter", value=5, labels={"provider": "openai"})
        
        # Check that counter was incremented
        key = collector._make_key("test_counter", {"provider": "openai"})
        assert collector.counters[key] == 5.0

    def test_increment_counter_default_value(self):
        """Test incrementing counter with default value."""
        collector = MetricsCollector()
        
        # Increment counter without specifying value
        collector.increment_counter("test_counter", labels={"provider": "openai"})
        
        # Check that counter was incremented by 1.0
        key = collector._make_key("test_counter", {"provider": "openai"})
        assert collector.counters[key] == 1.0

    def test_set_gauge(self):
        """Test setting a gauge metric value."""
        collector = MetricsCollector()
        
        # Set gauge value
        collector.set_gauge("test_gauge", 42.5, labels={"component": "cache"})
        
        # Check that gauge was set
        key = collector._make_key("test_gauge", {"component": "cache"})
        assert collector.gauges[key] == 42.5

    def test_observe_histogram(self):
        """Test observing a histogram value."""
        collector = MetricsCollector()
        collector.reset()  # Clear any existing metrics
        
        # Observe histogram values
        collector.observe_histogram("test_histogram", 0.5, labels={"provider": "openai"})
        collector.observe_histogram("test_histogram", 2.5, labels={"provider": "openai"})
        collector.observe_histogram("test_histogram", 15.0, labels={"provider": "openai"})
        
        # Check that histogram buckets were updated
        key = collector._make_key("test_histogram", {"provider": "openai"})
        assert key in collector.histograms
        
        # Count observations (last bucket count should equal total observations)
        total_observations = collector.histograms[key][-1].count
        assert total_observations == 3

    def test_observe_histogram_inline_creation(self):
        """Test observing histogram creates it inline if not exists."""
        collector = MetricsCollector()
        
        # Observe value without creating histogram first
        collector.observe_histogram("new_histogram", 1.5, labels={"provider": "openai"})
        
        # Check that histogram was created inline
        key = collector._make_key("new_histogram", {"provider": "openai"})
        assert key in collector.histograms
        assert key in collector.labels
        assert collector.labels[key] == {"provider": "openai"}

    def test_record_timer(self):
        """Test recording a timer metric."""
        collector = MetricsCollector()
        
        # Record timer values
        collector.record_timer("test_timer", 1.5, labels={"operation": "inference"})
        collector.record_timer("test_timer", 2.3, labels={"operation": "inference"})
        
        # Check that timer values were recorded
        key = collector._make_key("test_timer", {"operation": "inference"})
        assert key in collector.timers
        assert len(collector.timers[key]) == 2
        assert 1.5 in collector.timers[key]
        assert 2.3 in collector.timers[key]

    def test_timer_context_manager(self):
        """Test Timer context manager."""
        collector = MetricsCollector()
        
        # Use timer context manager
        with collector.timer("test_operation", {"component": "api"}):
            time.sleep(0.01)  # Small delay
        
        # Check that timer was recorded in global metrics collector
        from ai_utilities.metrics import metrics
        key = metrics.collector._make_key("test_operation", {"component": "api"})
        assert key in metrics.collector.timers
        assert len(metrics.collector.timers[key]) == 1
        assert metrics.collector.timers[key][0] > 0.01  # Should be at least the sleep time

    def test_make_key(self):
        """Test _make_key method."""
        collector = MetricsCollector()
        
        # Test key without labels
        key1 = collector._make_key("test_metric", {})
        assert key1 == "test_metric"
        
        # Test key with labels
        labels = {"provider": "openai", "model": "gpt-4"}
        key2 = collector._make_key("test_metric", labels)
        expected = "test_metric|model=gpt-4,provider=openai"  # Labels should be sorted
        assert key2 == expected

    def test_get_all_metrics(self):
        """Test getting all metrics as MetricValue objects."""
        collector = MetricsCollector()
        
        # Add different types of metrics
        collector.increment_counter("counter1", value=10, labels={"type": "api"})
        collector.set_gauge("gauge1", 100, labels={"type": "memory"})
        collector.observe_histogram("histogram1", 50, labels={"type": "response"})
        collector.record_timer("timer1", 2.5, labels={"type": "duration"})
        
        # Get all metrics
        all_metrics = collector.get_all_metrics()
        
        # Should include our metrics plus standard metrics
        # Note: Histograms are exported as {name}_bucket metrics
        metric_names = {m.name for m in all_metrics}
        assert "counter1" in metric_names
        assert "gauge1" in metric_names
        assert "histogram1_bucket" in metric_names  # Histograms exported as bucket metrics
        assert "timer1" in metric_names
        assert "ai_requests_total" in metric_names  # Standard metric

    def test_get_all_metrics_thread_safety(self):
        """Test thread safety of get_all_metrics."""
        collector = MetricsCollector()
        results = []
        
        def worker_thread(thread_id):
            for i in range(10):
                collector.increment_counter(f"counter_{thread_id}", value=1)
                metrics = collector.get_all_metrics()
                results.append(len(metrics))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed
        assert len(results) == 30  # 3 threads * 10 operations each
        
        # Verify metrics were collected
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) > 0

    def test_prometheus_exporter_initialization(self):
        """Test PrometheusExporter initialization."""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)
        
        assert hasattr(exporter, 'export')
        assert exporter.collector == collector

    def test_prometheus_exporter_export(self):
        """Test Prometheus metrics export."""
        collector = MetricsCollector()
        collector.increment_counter("test_requests", value=42, labels={"method": "POST"})
        collector.set_gauge("active_connections", 10, labels={"service": "api"})
        
        exporter = PrometheusExporter(collector)
        exported = exporter.export()
        
        # Should contain Prometheus format
        assert "# HELP" in exported
        assert "# TYPE" in exported
        assert "test_requests" in exported
        assert "active_connections" in exported
        assert 'method="POST"' in exported
        assert 'service="api"' in exported

    def test_json_exporter_initialization(self):
        """Test JSONExporter initialization."""
        collector = MetricsCollector()
        exporter = JSONExporter(collector)
        
        assert hasattr(exporter, 'export')
        assert exporter.collector == collector

    def test_json_exporter_export(self):
        """Test JSON metrics export."""
        collector = MetricsCollector()
        collector.increment_counter("test_counter", value=42, labels={"provider": "openai"})
        collector.set_gauge("test_gauge", 85.5, labels={"component": "cache"})
        
        exporter = JSONExporter(collector)
        exported = exporter.export()
        
        # Parse and verify JSON
        data = json.loads(exported)
        assert isinstance(data, list)
        assert len(data) >= 2  # At least our two metrics plus standard ones
        
        # Find our metrics in the export
        counter_metrics = [m for m in data if m["name"] == "test_counter"]
        gauge_metrics = [m for m in data if m["name"] == "test_gauge"]
        
        assert len(counter_metrics) >= 1
        assert len(gauge_metrics) >= 1
        
        # Verify metric structure
        for metric_data in counter_metrics:
            assert "name" in metric_data
            assert "value" in metric_data
            assert "metric_type" in metric_data
            assert "timestamp" in metric_data
            assert "labels" in metric_data

    def test_metrics_collector_with_labels(self):
        """Test metrics collection with various label combinations."""
        collector = MetricsCollector()
        
        # Test with different label combinations
        collector.increment_counter("api_requests", value=5, labels={"method": "POST", "status": "200"})
        collector.increment_counter("api_requests", value=3, labels={"method": "GET", "status": "200"})
        collector.set_gauge("active_connections", 10, labels={"service": "api"})
        collector.set_gauge("active_connections", 5, labels={"service": "database"})
        
        # Get all metrics
        all_metrics = collector.get_all_metrics()
        
        # Find metrics with our labels
        api_metrics = [m for m in all_metrics if m.name == "api_requests"]
        connection_metrics = [m for m in all_metrics if m.name == "active_connections"]
        
        assert len(api_metrics) >= 2
        assert len(connection_metrics) >= 2
        
        # Verify labels are preserved
        api_labels = [m.labels for m in api_metrics]
        assert {"method": "POST", "status": "200"} in api_labels
        assert {"method": "GET", "status": "200"} in api_labels

    def test_metrics_collector_special_characters_in_labels(self):
        """Test metrics with special characters in label values."""
        collector = MetricsCollector()
        
        special_labels = {
            "special-chars": "test-value-with-dashes",
            "unicode": "test-ñáéíóú",
            "spaces": "value with spaces"
        }
        
        collector.increment_counter("test_counter", value=1, labels=special_labels)
        
        metrics = collector.get_all_metrics()
        counter_metrics = [m for m in metrics if m.name == "test_counter"]
        
        assert len(counter_metrics) >= 1
        assert counter_metrics[0].labels == special_labels

    def test_metrics_collector_negative_values(self):
        """Test metrics with negative values."""
        collector = MetricsCollector()
        
        # Gauge can have negative values
        collector.set_gauge("temperature", -10.5)
        
        metrics = collector.get_all_metrics()
        # Filter for our specific test metric (exclude standard metrics)
        temp_metrics = [m for m in metrics if m.name == "temperature" and m.labels == {} and m.value == -10.5]
        assert len(temp_metrics) >= 1
        assert temp_metrics[0].value == -10.5

    def test_metrics_collector_zero_values(self):
        """Test metrics with zero values."""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", value=0)
        collector.set_gauge("test_gauge", 0)
        
        metrics = collector.get_all_metrics()
        counter_metrics = [m for m in metrics if m.name == "test_counter"]
        gauge_metrics = [m for m in metrics if m.name == "test_gauge"]
        
        assert len(counter_metrics) >= 1
        assert len(gauge_metrics) >= 1
        
        assert counter_metrics[0].value == 0
        assert gauge_metrics[0].value == 0

    def test_metrics_collector_float_precision(self):
        """Test metrics with high precision float values."""
        collector = MetricsCollector()
        
        precise_value = 3.14159265359
        collector.set_gauge("pi_value", precise_value)
        
        metrics = collector.get_all_metrics()
        # Filter for our specific test metric (exclude standard metrics)
        pi_metrics = [m for m in metrics if m.name == "pi_value" and m.labels == {} and m.value == precise_value]
        assert len(pi_metrics) >= 1
        assert pi_metrics[0].value == precise_value

    def test_metrics_collector_large_values(self):
        """Test metrics with large integer values."""
        collector = MetricsCollector()
        
        large_value = 2**63 - 1  # Max 64-bit integer
        collector.increment_counter("large_counter", value=large_value)
        
        metrics = collector.get_all_metrics()
        # Filter for our specific test metric (exclude standard metrics)
        # Note: Large integers are converted to float in metrics
        large_metrics = [m for m in metrics if m.name == "large_counter" and m.labels == {} and m.value == float(large_value)]
        assert len(large_metrics) >= 1
        assert large_metrics[0].value == float(large_value)

    def test_timer_class(self):
        """Test Timer class directly."""
        collector = MetricsCollector()
        
        # Create timer directly
        timer = Timer("test_operation", {"component": "test"})
        
        # Simulate timer usage
        with patch('time.time', side_effect=[0.0, 1.5]):  # Mock start and end time
            with timer:
                pass
        
        # Check that timer was recorded in global metrics collector
        from ai_utilities.metrics import metrics
        key = metrics.collector._make_key("test_operation", {"component": "test"})
        assert key in metrics.collector.timers
        assert metrics.collector.timers[key][0] == 1.5

    def test_open_telemetry_exporter_initialization(self):
        """Test OpenTelemetryExporter initialization."""
        collector = MetricsCollector()
        exporter = OpenTelemetryExporter(collector)
        
        assert hasattr(exporter, 'export')
        assert exporter.collector == collector

    def test_metrics_collector_history_limit(self):
        """Test metrics collector history limit for timers."""
        collector = MetricsCollector(max_history=5)
        
        # Add more timer values than the limit
        for i in range(10):
            collector.record_timer("test_timer", float(i))
        
        # Should only keep the most recent values
        key = collector._make_key("test_timer", {})
        assert len(collector.timers[key]) == 5  # Limited to max_history
        
        # Should keep the most recent values (5-9)
        expected_values = [5.0, 6.0, 7.0, 8.0, 9.0]
        actual_values = list(collector.timers[key])
        assert actual_values == expected_values
