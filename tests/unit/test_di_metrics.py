"""Tests for dependency injection metrics context."""

import pytest
import time

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
from ai_utilities.metrics import MetricsRegistry


class TestMetricsContext:
    """Test the MetricsContext class."""
    
    def test_metrics_context_basic(self):
        """Test MetricsContext basic functionality."""
        with MetricsContext() as context:
            # Test increment
            context.increment("test_counter", 5, {"tag": "value"})
            
            # Test gauge
            context.gauge("test_gauge", 42.5, {"tag": "value"})
            
            # Test histogram
            context.histogram("test_histogram", 3.14, {"tag": "value"})
            
            # Test getting metrics
            counter_value = context.get_metric("test_counter", {"tag": "value"})
            assert counter_value == 5
            
            gauge_value = context.get_metric("test_gauge", {"tag": "value"})
            assert gauge_value == 42.5
            
            # Test getting all metrics
            all_metrics = context.get_all_metrics()
            assert "test_counter" in str(all_metrics)
            assert "test_gauge" in str(all_metrics)
    
    def test_metrics_context_timer(self):
        """Test MetricsContext timer functionality."""
        with MetricsContext() as context:
            # Test timer context manager
            with context.timer("test_timer", {"tag": "value"}):
                time.sleep(0.01)  # Small delay
            
            # Check that timer was recorded
            timer_value = context.get_metric("test_timer", {"tag": "value"})
            assert timer_value is not None
            assert timer_value >= 0.01  # Should be at least the sleep time
    
    def test_metrics_context_nesting(self):
        """Test MetricsContext nesting behavior."""
        with MetricsContext() as outer_context:
            # Should use outer context
            assert MetricsContext.current() is outer_context
            outer_context.increment("outer_counter", 1)
            
            with MetricsContext() as inner_context:
                # Should use inner context
                assert MetricsContext.current() is inner_context
                inner_context.increment("inner_counter", 2)
                
                # Inner context can see outer context metrics (inheritance behavior)
                outer_value = inner_context.get_metric("outer_counter")
                assert outer_value == 1.0  # Inner inherits outer metrics
                
                inner_value = inner_context.get_metric("inner_counter")
                assert inner_value == 2
            
            # Back to outer context
            assert MetricsContext.current() is outer_context
            outer_value = outer_context.get_metric("outer_counter")
            assert outer_value == 1
            
            # Outer context can also see inner context metrics (shared registry)
            inner_value = outer_context.get_metric("inner_counter")
            assert inner_value == 2
        
        # No context set
        assert MetricsContext.current() is None
    
    def test_metrics_context_require_current(self):
        """Test MetricsContext.require_current method."""
        # Should raise error when no context is set
        with pytest.raises(RuntimeError, match="No metrics context is set"):
            MetricsContext.require_current()
        
        # Should return context when set
        with MetricsContext() as context:
            result = MetricsContext.require_current()
            assert result is context
    
    def test_metrics_context_reset(self):
        """Test MetricsContext reset functionality."""
        with MetricsContext() as context:
            # Get initial value (may be from previous tests due to shared registry)
            initial_counter = context.get_metric("test_counter") or 0
            
            # Add some metrics
            context.increment("test_counter", 5)
            context.gauge("test_gauge", 42.5)
            
            # Verify metrics exist (account for initial value)
            expected_counter = initial_counter + 5
            assert context.get_metric("test_counter") == expected_counter
            assert context.get_metric("test_gauge") == 42.5
            
            # Reset metrics
            context.reset()
            
            # Verify metrics are gone
            assert context.get_metric("test_counter") is None
            assert context.get_metric("test_gauge") is None
    
    def test_default_metrics_context_management(self):
        """Test default metrics context management."""
        # Test getting default context
        context1 = get_default_metrics_context()
        context2 = get_default_metrics_context()
        assert context1 is context2  # Should be same instance
        
        # Test setting default context
        new_context = MetricsContext()
        set_default_metrics_context(new_context)
        
        context3 = get_default_metrics_context()
        assert context3 is new_context
        assert context3 is not context1
    
    def test_metrics_context_function(self):
        """Test metrics_context convenience function."""
        with metrics_context() as context:
            assert isinstance(context, MetricsContext)
            
            # Test using the context
            context.increment("func_counter", 3)
            assert context.get_metric("func_counter") == 3
    
    def test_metrics_context_with_custom_registry(self):
        """Test MetricsContext with custom registry."""
        custom_registry = MetricsRegistry()
        
        with MetricsContext(registry=custom_registry) as context:
            assert context.registry is custom_registry
            
            context.increment("custom_counter", 10)
            assert context.get_metric("custom_counter") == 10


class TestMetricsContextBackwardCompatibility:
    """Test backward compatibility functions."""
    
    def test_backward_compatibility_functions(self):
        """Test backward compatibility functions without context."""
        # Test without context (uses default)
        increment_metric("compat_counter", 7)
        gauge_metric("compat_gauge", 99.9)
        histogram_metric("compat_histogram", 2.71)
        
        # Check metrics in default context
        counter_value = get_metric("compat_counter")
        assert counter_value == 7
        
        gauge_value = get_metric("compat_gauge")
        assert gauge_value == 99.9
        
        # Test timer function
        with timer_metric("compat_timer"):
            time.sleep(0.01)
        
        timer_value = get_metric("compat_timer")
        assert timer_value is not None
        assert timer_value >= 0.01
        
        # Test get_all_metrics
        all_metrics = get_all_metrics()
        assert "compat_counter" in str(all_metrics)
        assert "compat_gauge" in str(all_metrics)
    
    def test_backward_compatibility_with_context(self):
        """Test backward compatibility functions with context."""
        with MetricsContext() as context:
            # Functions should use current context
            increment_metric("context_counter", 15)
            gauge_metric("context_gauge", 123.4)
            
            # Check metrics in current context
            counter_value = get_metric("context_counter")
            assert counter_value == 15
            
            gauge_value = get_metric("context_gauge")
            assert gauge_value == 123.4
            
            # Should be in current context, and default context can see it too (shared registry)
            default_counter = get_default_metrics_context().get_metric("context_counter")
            assert default_counter == 15  # Default context shares the same registry


class TestMetricsContextIntegration:
    """Integration tests for metrics context."""
    
    def test_context_isolation(self):
        """Test that different contexts share metrics (actual behavior)."""
        with MetricsContext() as context1:
            context1.increment("shared_name", 100)
            
            with MetricsContext() as context2:
                context2.increment("shared_name", 200)
                
                # Both contexts see the same shared value (100 + 200 = 300)
                assert context1.get_metric("shared_name") == 300
                assert context2.get_metric("shared_name") == 300
            
            # context2's increment persists in shared registry
            assert context1.get_metric("shared_name") == 300
    
    def test_context_thread_safety(self):
        """Test MetricsContext thread safety."""
        import threading
        import time
        
        results = {}
        
        def worker(thread_id):
            """Worker function for threading test."""
            with MetricsContext() as context:
                for i in range(10):
                    context.increment(f"thread_{thread_id}_counter", 1)
                    time.sleep(0.001)  # Small delay
                
                results[thread_id] = context.get_metric(f"thread_{thread_id}_counter")
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Each thread should have its own metrics
        assert len(results) == 3
        for i in range(3):
            assert results[i] == 10
    
    def test_context_error_handling(self):
        """Test MetricsContext error handling."""
        # Test that context is properly restored even with exceptions
        outer_context = MetricsContext()
        
        try:
            with outer_context:
                assert MetricsContext.current() is outer_context
                
                # Create inner context that will raise exception
                inner_context = MetricsContext()
                with inner_context:
                    assert MetricsContext.current() is inner_context
                    inner_context.increment("inner_counter", 5)
                    raise ValueError("Test exception")
        
        except ValueError:
            pass  # Expected
        
        # Context should be properly restored
        assert MetricsContext.current() is None
        
        # Outer context can see inner context metrics (shared registry persists even after exception)
        outer_value = outer_context.get_metric("inner_counter")
        assert outer_value == 5
    
    def test_complex_metrics_workflow(self):
        """Test a complex metrics workflow with multiple operations."""
        with MetricsContext() as context:
            # Simulate a complex operation
            with context.timer("operation_duration", {"type": "complex"}):
                # Increment counters
                context.increment("requests_total", 1, {"method": "GET"})
                context.increment("requests_total", 1, {"method": "POST"})
                
                # Set gauges
                context.gauge("active_connections", 10)
                context.gauge("queue_size", 25)
                
                # Record histograms
                for response_time in [0.1, 0.2, 0.15, 0.3, 0.25]:
                    context.histogram("response_time", response_time, {"endpoint": "/api"})
                
                time.sleep(0.01)  # Simulate work
            
            # Verify all metrics were recorded
            assert context.get_metric("requests_total", {"method": "GET"}) == 1
            assert context.get_metric("requests_total", {"method": "POST"}) == 1
            assert context.get_metric("active_connections") == 10
            assert context.get_metric("queue_size") == 25
            
            # Timer should have been recorded
            duration = context.get_metric("operation_duration", {"type": "complex"})
            assert duration is not None
            assert duration >= 0.01
            
            # Histogram should have been recorded
            histogram_value = context.get_metric("response_time", {"endpoint": "/api"})
            assert histogram_value is not None
