"""Analytics hooks for processing AI telemetry events.

This module provides interfaces and implementations for handling analytics
events without affecting existing behavior.
"""

from typing import Any, Callable, List, Protocol

from .events import AiEventBase


class AnalyticsHook(Protocol):
    """Protocol for analytics event handlers."""
    
    def handle(self, event: AiEventBase) -> None:
        """Handle an analytics event.
        
        Args:
            event: The analytics event to process.
        """
        ...


class NullAnalyticsHook:
    """No-op analytics hook that does nothing.
    
    Useful as default or when analytics are disabled.
    """
    
    def handle(self, event: AiEventBase) -> None:
        """Do nothing with the event."""
        pass


class CompositeAnalyticsHook:
    """Analytics hook that fans out events to multiple hooks.
    
    Allows multiple analytics handlers to be used simultaneously.
    """
    
    def __init__(self, hooks: List[AnalyticsHook]) -> None:
        """Initialize with a list of hooks.
        
        Args:
            hooks: List of analytics hooks to call.
        """
        self._hooks = hooks
    
    def handle(self, event: AiEventBase) -> None:
        """Handle event by calling all child hooks.
        
        Args:
            event: The analytics event to process.
        """
        for hook in self._hooks:
            try:
                hook.handle(event)
            except Exception:
                # Swallow hook errors to prevent breaking user code
                pass


# Type alias for analytics hook functions
AnalyticsHookFunction = Callable[[AiEventBase], None]
