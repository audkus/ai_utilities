"""
Context management for dependency injection.

This package provides context managers for configuration, metrics,
and other services that eliminate global state dependencies.
"""

from .configuration import (
    ConfigurationContext,
    configuration_context,
    get_default_context,
    set_default_context,
    get_current_ai_settings,
    get_current_environment_provider,
    get_current_config_manager,
)

from .metrics import (
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

__all__ = [
    # Configuration context
    "ConfigurationContext",
    "configuration_context",
    "get_default_context",
    "set_default_context",
    "get_current_ai_settings",
    "get_current_environment_provider",
    "get_current_config_manager",
    
    # Metrics context
    "MetricsContext",
    "metrics_context",
    "get_default_metrics_context",
    "set_default_metrics_context",
    "increment_metric",
    "gauge_metric",
    "histogram_metric",
    "timer_metric",
    "get_metric",
    "get_all_metrics",
]
