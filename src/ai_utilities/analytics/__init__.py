"""Analytics module for AI telemetry and event processing.

This module provides analytics capabilities without affecting existing behavior.
"""

from .events import AiErrorEvent, AiEvent, AiEventBase, AiRequestEvent, AiResponseEvent
from .hooks import (
    AnalyticsHook,
    AnalyticsHookFunction,
    CompositeAnalyticsHook,
    NullAnalyticsHook,
)

__all__ = [
    "AiEvent",
    "AiEventBase", 
    "AiRequestEvent",
    "AiResponseEvent",
    "AiErrorEvent",
    "AnalyticsHook",
    "AnalyticsHookFunction",
    "CompositeAnalyticsHook",
    "NullAnalyticsHook",
]
