"""Metrics collection and export for AI Utilities.

This module provides standardized metrics collection for monitoring AI Utilities
in production environments with support for Prometheus, OpenTelemetry, and custom backends.
"""

import time
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import logging

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics supported."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """A single metric value with timestamp."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: float
    labels: Dict[str, str]
    unit: str = ""
    description: str = ""


@dataclass
class HistogramBucket:
    """Histogram bucket for distribution metrics."""
    upper_bound: float
    count: int


class MetricsCollector:
    """Collects and manages metrics for AI Utilities."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[HistogramBucket]] = defaultdict(list)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.labels: Dict[str, Dict[str, str]] = {}
        self.descriptions: Dict[str, str] = {}  # Store metric descriptions
        self.lock = threading.Lock()
        
        # Initialize standard metrics
        self._init_standard_metrics()
    
    def _init_standard_metrics(self):
        """Initialize standard AI Utilities metrics."""
        # Request metrics
        self.create_counter("ai_requests_total", "Total number of AI requests")
        self.create_counter("ai_requests_successful", "Total successful AI requests")
        self.create_counter("ai_requests_failed", "Total failed AI requests")
        
        # Response metrics
        self.create_histogram("ai_response_duration_seconds", "AI response duration in seconds")
        self.create_histogram("ai_response_tokens", "AI response token count")
        
        # Cache metrics
        self.create_counter("cache_hits_total", "Total cache hits")
        self.create_counter("cache_misses_total", "Total cache misses")
        self.create_gauge("cache_size", "Current cache size")
        
        # Provider metrics
        self.create_counter("provider_errors_total", "Total provider errors", {"provider": ""})
        self.create_histogram("provider_request_duration_seconds", "Provider request duration", {"provider": ""})
        
        # Usage metrics
        self.create_counter("tokens_used_total", "Total tokens used", {"model": ""})
        self.create_gauge("active_clients", "Number of active clients")
        
        # System metrics
        self.create_gauge("memory_usage_bytes", "Memory usage in bytes")
        self.create_counter("rate_limit_hits_total", "Total rate limit hits")
    
    def create_counter(self, name: str, description: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Create a counter metric."""
        with self.lock:
            key = self._make_key(name, labels or {})
            self.descriptions[key] = description
            if labels:
                self.labels[key] = labels
    
    def create_gauge(self, name: str, description: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Create a gauge metric."""
        with self.lock:
            key = self._make_key(name, labels or {})
            self.descriptions[key] = description
            if labels:
                self.labels[key] = labels
    
    def create_histogram(self, name: str, description: str, buckets: Optional[List[float]] = None, labels: Optional[Dict[str, str]] = None) -> None:
        """Create a histogram metric."""
        if buckets is None:
            buckets = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, float('inf')]
        
        with self.lock:
            key = self._make_key(name, labels or {})
            self.histograms[key] = [HistogramBucket(bound, 0) for bound in buckets]
            self.descriptions[key] = description
            if labels:
                self.labels[key] = labels
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels or {})
        with self.lock:
            # Store labels if this is the first time we see this metric
            if key not in self.labels and labels:
                self.labels[key] = labels
            # Store description if not present (use a default)
            if key not in self.descriptions:
                self.descriptions[key] = f"Counter metric {name}"
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        key = self._make_key(name, labels or {})
        with self.lock:
            # Store labels if this is the first time we see this metric
            if key not in self.labels and labels:
                self.labels[key] = labels
            # Store description if not present (use a default)
            if key not in self.descriptions:
                self.descriptions[key] = f"Gauge metric {name}"
            self.gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value for a histogram metric."""
        key = self._make_key(name, labels or {})
        with self.lock:
            if key not in self.histograms:
                # Create histogram inline without calling create_histogram to avoid deadlock
                if labels:
                    self.labels[key] = labels
                self.histograms[key] = [HistogramBucket(bound, 0) for bound in [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, float('inf')]]
            
            for bucket in self.histograms[key]:
                if value <= bucket.upper_bound:
                    bucket.count += 1
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a timer metric."""
        key = self._make_key(name, labels or {})
        with self.lock:
            self.timers[key].append(duration)
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key from name and labels for internal storage."""
        if not labels:
            return name
        
        # Use a separator that won't appear in metric names for internal storage
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}|{label_str}"
    
    def get_all_metrics(self) -> List[MetricValue]:
        """Get all current metrics as MetricValue objects."""
        metrics = []
        timestamp = time.time()
        
        with self.lock:
            # Counters - include all, even zero-valued ones
            all_counter_keys = set(self.counters.keys()) | set(self.descriptions.keys())
            for key in all_counter_keys:
                value = self.counters.get(key, 0.0)
                labels = self.labels.get(key, {})
                description = self.descriptions.get(key, "")
                
                # Extract name from internal key
                if "|" in key:
                    name, _ = key.split("|", 1)
                else:
                    name = key
                
                metrics.append(MetricValue(
                    name=name,
                    value=value,
                    metric_type=MetricType.COUNTER,
                    timestamp=timestamp,
                    labels=labels,
                    description=description
                ))
            
            # Gauges - include all, even zero-valued ones
            all_gauge_keys = set(self.gauges.keys()) | set(self.descriptions.keys())
            for key in all_gauge_keys:
                value = self.gauges.get(key, 0.0)
                labels = self.labels.get(key, {})
                description = self.descriptions.get(key, "")
                
                # Extract name from internal key
                if "|" in key:
                    name, _ = key.split("|", 1)
                else:
                    name = key
                
                metrics.append(MetricValue(
                    name=name,
                    value=value,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    labels=labels,
                    description=description
                ))
            
            # Histograms - only include buckets with counts > 0
            for key, buckets in self.histograms.items():
                labels = self.labels.get(key, {})
                description = self.descriptions.get(key, "")
                
                # Extract name from internal key
                if "|" in key:
                    name, _ = key.split("|", 1)
                else:
                    name = key
                
                for bucket in buckets:
                    if bucket.count > 0:
                        metrics.append(MetricValue(
                            name=f"{name}_bucket",
                            value=bucket.count,
                            metric_type=MetricType.COUNTER,
                            timestamp=timestamp,
                            labels={**labels, "le": str(bucket.upper_bound)},
                            description=description
                        ))
        
        return metrics
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
        
        # Initialize standard metrics outside of lock to avoid deadlock
        self._init_standard_metrics()


class PrometheusExporter:
    """Export metrics in Prometheus format."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def export(self) -> str:
        """Export metrics in Prometheus text format."""
        metrics = self.collector.get_all_metrics()
        output = []
        
        # Group metrics by name
        grouped = defaultdict(list)
        for metric in metrics:
            grouped[metric.name].append(metric)
        
        for name, metric_list in grouped.items():
            # Add HELP and TYPE lines
            if metric_list:
                metric_type = metric_list[0].metric_type.value
                description = metric_list[0].description or f"Metric {name}"
                output.append(f"# HELP {name} {description}")
                output.append(f"# TYPE {name} {metric_type}")
            
            # Add metric values
            for metric in metric_list:
                if metric.labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                    output.append(f"{name}{{{label_str}}} {metric.value}")
                else:
                    output.append(f"{name} {metric.value}")
        
        return "\n".join(output)


class OpenTelemetryExporter:
    """Export metrics in OpenTelemetry format."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def export(self) -> Dict[str, Any]:
        """Export metrics in OpenTelemetry JSON format."""
        metrics = self.collector.get_all_metrics()
        
        return {
            "resource_metrics": [{
                "resource": {},
                "scope_metrics": [{
                    "scope": {"name": "ai-utilities"},
                    "metrics": [self._convert_metric(m) for m in metrics]
                }]
            }]
        }
    
    def _convert_metric(self, metric: MetricValue) -> Dict[str, Any]:
        """Convert MetricValue to OpenTelemetry format."""
        base_metric: Dict[str, Any] = {
            "name": metric.name,
            "description": metric.description,
            "unit": metric.unit
        }
        
        if metric.metric_type == MetricType.COUNTER:
            base_metric["sum"] = {
                "data_points": [{
                    "as_int": int(metric.value),
                    "time_unix_nano": int(metric.timestamp * 1e9)
                }]
            }
        elif metric.metric_type == MetricType.GAUGE:
            base_metric["gauge"] = {
                "data_points": [{
                    "as_double": metric.value,
                    "time_unix_nano": int(metric.timestamp * 1e9)
                }]
            }
        
        return base_metric


class JSONExporter:
    """Export metrics in JSON format."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def export(self) -> str:
        """Export metrics as JSON."""
        metrics = self.collector.get_all_metrics()
        # Convert MetricType enum to string for JSON serialization
        serializable_metrics = []
        for m in metrics:
            metric_dict = asdict(m)
            metric_dict['metric_type'] = m.metric_type.value
            serializable_metrics.append(metric_dict)
        return json.dumps(serializable_metrics, indent=2)


class MetricsRegistry:
    """Global metrics registry for AI Utilities."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.collector = MetricsCollector()
            self.prometheus_exporter = PrometheusExporter(self.collector)
            self.opentelemetry_exporter = OpenTelemetryExporter(self.collector)
            self.json_exporter = JSONExporter(self.collector)
            self.initialized = True
    
    def record_request(self, success: bool, duration: float, tokens: int, model: str = ""):
        """Record an AI request."""
        self.collector.increment_counter("ai_requests_total")
        if success:
            self.collector.increment_counter("ai_requests_successful")
        else:
            self.collector.increment_counter("ai_requests_failed")
        
        self.collector.observe_histogram("ai_response_duration_seconds", duration)
        self.collector.observe_histogram("ai_response_tokens", tokens)
        
        if model:
            self.collector.increment_counter("tokens_used_total", tokens, {"model": model})
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.collector.increment_counter("cache_hits_total")
    
    def record_cache_miss(self):
        """Record a cache miss."""
        self.collector.increment_counter("cache_misses_total")
    
    def set_cache_size(self, size: int):
        """Set current cache size."""
        self.collector.set_gauge("cache_size", size)
    
    def record_provider_error(self, provider: str):
        """Record a provider error."""
        self.collector.increment_counter("provider_errors_total", 1.0, {"provider": provider})
    
    def record_provider_request(self, provider: str, duration: float):
        """Record a provider request."""
        self.collector.observe_histogram("provider_request_duration_seconds", duration, {"provider": provider})
    
    def set_active_clients(self, count: int):
        """Set number of active clients."""
        self.collector.set_gauge("active_clients", count)
    
    def record_rate_limit_hit(self):
        """Record a rate limit hit."""
        self.collector.increment_counter("rate_limit_hits_total")
    
    def set_memory_usage(self, bytes_used: int):
        """Set memory usage."""
        self.collector.set_gauge("memory_usage_bytes", bytes_used)
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        return self.prometheus_exporter.export()
    
    def export_opentelemetry(self) -> Dict[str, Any]:
        """Export metrics in OpenTelemetry format."""
        return self.opentelemetry_exporter.export()
    
    def export_json(self) -> str:
        """Export metrics in JSON format."""
        return self.json_exporter.export()
    
    def reset(self):
        """Reset all metrics."""
        self.collector.reset()


# Global metrics instance
metrics = MetricsRegistry()


# Decorator for automatic metrics collection
def monitor_requests(metric_name: Optional[str] = None):
    """Decorator to automatically monitor function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            tokens = 0
            
            try:
                result = func(*args, **kwargs)
                success = True
                
                # Try to extract token count from result
                if hasattr(result, 'usage') and hasattr(result.usage, 'total_tokens'):
                    tokens = result.usage.total_tokens
                
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                name = metric_name or f"{func.__module__}.{func.__name__}"
                metrics.record_request(success, duration, tokens)
        
        return wrapper
    return decorator


# Context manager for timing operations
class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            metrics.collector.record_timer(self.metric_name, duration, self.labels)


# Example usage
def example_usage():
    """Example of how to use the metrics system."""
    
    # Record a request
    metrics.record_request(success=True, duration=1.5, tokens=100, model="gpt-4")
    
    # Record cache operations
    metrics.record_cache_hit()
    metrics.record_cache_miss()
    metrics.set_cache_size(1500)
    
    # Record provider errors
    metrics.record_provider_error("openai")
    metrics.record_provider_request("openai", 1.2)
    
    # Set system metrics
    metrics.set_active_clients(5)
    metrics.record_rate_limit_hit()
    metrics.set_memory_usage(1024 * 1024 * 50)  # 50MB
    
    # Export metrics
    prometheus_output = metrics.export_prometheus()
    json_output = metrics.export_json()
    
    print("Prometheus format:")
    print(prometheus_output[:500] + "...")
    
    print("\nJSON format:")
    print(json_output[:500] + "...")
    
    # Use decorator for automatic monitoring
    @monitor_requests("my_ai_function")
    def my_ai_function(prompt: str):
        # Simulate AI work
        time.sleep(0.1)
        return "response"


if __name__ == "__main__":
    example_usage()
