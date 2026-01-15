"""
Metrics context management for dependency injection.

This module provides context management for metrics collection,
eliminating the need for global metrics registries.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from ..metrics import MetricsRegistry


class MetricsContext:
    """
    Context for metrics collection without global state.
    
    This context provides metrics collection capabilities that are
    isolated to the current context, enabling better testability
    and thread safety.
    """
    
    # Context variable for thread-local storage
    _metrics_context: contextvars.ContextVar[MetricsContext] = contextvars.ContextVar(
        "metrics_context",
        default=None
    )
    
    def __init__(self, registry: Optional[MetricsRegistry] = None):
        """
        Initialize metrics context.
        
        Args:
            registry: Metrics registry instance (creates new one if None)
        """
        self.registry = registry or MetricsRegistry()
        
        # Store previous context for restoration
        self._previous_context = None
        self._token = None
    
    def __enter__(self) -> MetricsContext:
        """Enter the metrics context."""
        # Store previous context
        self._previous_context = self._metrics_context.get()
        
        # Set this context as current
        self._token = self._metrics_context.set(self)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the metrics context."""
        # Restore previous context
        if self._token is not None:
            self._metrics_context.reset(self._token)
    
    def increment(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            tags: Optional tags for the metric
        """
        self.registry.increment(name, value, tags)
    
    def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags for the metric
        """
        self.registry.gauge(name, value, tags)
    
    def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram metric value.
        
        Args:
            name: Metric name
            value: Histogram value
            tags: Optional tags for the metric
        """
        self.registry.histogram(name, value, tags)
    
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Create a timer context manager.
        
        Args:
            name: Timer metric name
            tags: Optional tags for the metric
            
        Returns:
            Timer context manager
        """
        return self.registry.timer(name, tags)
    
    def get_metric(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """
        Get a metric value.
        
        Args:
            name: Metric name
            tags: Optional tags for the metric
            
        Returns:
            Metric value or None if not found
        """
        return self.registry.get_metric(name, tags)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics from this context.
        
        Returns:
            Dictionary of all metrics
        """
        return self.registry.get_all_metrics()
    
    def reset(self) -> None:
        """Reset all metrics in this context."""
        self.registry.reset()
    
    @classmethod
    def current(cls) -> Optional[MetricsContext]:
        """
        Get the current metrics context.
        
        Returns:
            Current MetricsContext or None if not set
        """
        return cls._metrics_context.get()
    
    @classmethod
    def require_current(cls) -> MetricsContext:
        """
        Get the current metrics context, raising an error if not set.
        
        Returns:
            Current MetricsContext
            
        Raises:
            RuntimeError: If no metrics context is set
        """
        current = cls.current()
        if current is None:
            raise RuntimeError(
                "No metrics context is set. Use MetricsContext() to create one."
            )
        return current


# Global default context (for backward compatibility)
_default_context: Optional[MetricsContext] = None


def get_default_metrics_context() -> MetricsContext:
    """
    Get the default metrics context.
    
    Returns:
        Default MetricsContext instance
    """
    global _default_context
    if _default_context is None:
        _default_context = MetricsContext()
    return _default_context


def set_default_metrics_context(context: MetricsContext) -> None:
    """
    Set the default metrics context.
    
    Args:
        context: Metrics context to use as default
    """
    global _default_context
    _default_context = context


@contextmanager
def metrics_context(registry: Optional[MetricsRegistry] = None) -> Generator[MetricsContext, None, None]:
    """
    Context manager for metrics collection.
    
    This is a convenience function that creates and manages a MetricsContext.
    
    Args:
        registry: Metrics registry instance
        
    Yields:
        MetricsContext instance
    """
    with MetricsContext(registry=registry) as context:
        yield context


# Backward compatibility functions
def increment_metric(name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
    """
    Increment a metric using current context or default.
    
    Args:
        name: Metric name
        value: Value to increment by
        tags: Optional tags for the metric
    """
    current = MetricsContext.current()
    if current is not None:
        current.increment(name, value, tags)
    else:
        # Fall back to default context
        get_default_metrics_context().increment(name, value, tags)


def gauge_metric(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """
    Set a gauge metric using current context or default.
    
    Args:
        name: Metric name
        value: Gauge value
        tags: Optional tags for the metric
    """
    current = MetricsContext.current()
    if current is not None:
        current.gauge(name, value, tags)
    else:
        # Fall back to default context
        get_default_metrics_context().gauge(name, value, tags)


def histogram_metric(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """
    Record a histogram metric using current context or default.
    
    Args:
        name: Metric name
        value: Histogram value
        tags: Optional tags for the metric
    """
    current = MetricsContext.current()
    if current is not None:
        current.histogram(name, value, tags)
    else:
        # Fall back to default context
        get_default_metrics_context().histogram(name, value, tags)


def timer_metric(name: str, tags: Optional[Dict[str, str]] = None):
    """
    Create a timer using current context or default.
    
    Args:
        name: Timer metric name
        tags: Optional tags for the metric
        
    Returns:
        Timer context manager
    """
    current = MetricsContext.current()
    if current is not None:
        return current.timer(name, tags)
    else:
        # Fall back to default context
        return get_default_metrics_context().timer(name, tags)


def get_metric(name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
    """
    Get a metric value using current context or default.
    
    Args:
        name: Metric name
        tags: Optional tags for the metric
        
    Returns:
        Metric value or None if not found
    """
    current = MetricsContext.current()
    if current is not None:
        return current.get_metric(name, tags)
    else:
        # Fall back to default context
        return get_default_metrics_context().get_metric(name, tags)


def get_all_metrics() -> Dict[str, Any]:
    """
    Get all metrics using current context or default.
    
    Returns:
        Dictionary of all metrics
    """
    current = MetricsContext.current()
    if current is not None:
        return current.get_all_metrics()
    else:
        # Fall back to default context
        return get_default_metrics_context().get_all_metrics()
