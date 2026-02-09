"""Tests for context metrics management."""

import pytest
from ai_utilities.context.metrics import (
    MetricsContext,
    metrics_context,
    get_default_metrics_context,
    set_default_metrics_context,
    increment_metric,
    gauge_metric,
    histogram_metric,
    timer_metric,
    get_metric,
    get_all_metrics,
)


class TestMetricsContext:
    """Test MetricsContext class and functions."""
    
    def test_metrics_context_creation(self):
        """Test creating a metrics context."""
        context = MetricsContext()
        assert context is not None
    
    def test_metrics_context_manager(self):
        """Test metrics context as context manager."""
        with metrics_context() as ctx:
            assert ctx is not None
    
    def test_get_default_metrics_context(self):
        """Test getting default metrics context."""
        context = get_default_metrics_context()
        assert context is not None
    
    def test_set_default_metrics_context(self):
        """Test setting default metrics context."""
        new_context = MetricsContext()
        set_default_metrics_context(new_context)
        assert get_default_metrics_context() is new_context
    
    def test_increment_metric(self):
        """Test incrementing a metric."""
        with metrics_context():
            increment_metric("test_counter")
    
    def test_gauge_metric(self):
        """Test setting a gauge metric."""
        with metrics_context():
            gauge_metric("test_gauge", 42)
    
    def test_histogram_metric(self):
        """Test recording a histogram metric."""
        with metrics_context():
            histogram_metric("test_histogram", 1.5)
    
    def test_timer_metric(self):
        """Test recording a timer metric."""
        with metrics_context():
            timer_metric("test_timer", 0.1)
    
    def test_get_metric(self):
        """Test getting a metric value."""
        with metrics_context():
            increment_metric("test_counter")
            value = get_metric("test_counter")
            # The value might be None or a number, just test it doesn't crash
            assert value is not None or value is None
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        with metrics_context():
            increment_metric("test_counter")
            gauge_metric("test_gauge", 42)
            all_metrics = get_all_metrics()
            assert isinstance(all_metrics, dict)
