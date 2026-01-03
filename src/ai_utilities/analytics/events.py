"""Analytics event types for request/response telemetry.

This module defines Pydantic models for capturing AI request/response events
without affecting existing behavior or introducing import-time side effects.
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AiEventBase(BaseModel):
    """Base class for all AI analytics events."""
    
    event_type: Literal["request", "response", "error"]
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    provider: str
    model: Optional[str] = None
    operation: Literal["ask"] = "ask"
    cache: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class AiRequestEvent(AiEventBase):
    """Event emitted before an AI request is sent to the provider."""
    
    event_type: Literal["request"] = "request"
    success: bool = True  # Request events are always successful (just starting)


class AiResponseEvent(AiEventBase):
    """Event emitted after a successful AI response is received."""
    
    event_type: Literal["response"] = "response"
    success: bool = True
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    latency_ms: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class AiErrorEvent(AiEventBase):
    """Event emitted when an AI request fails."""
    
    event_type: Literal["error"] = "error"
    success: bool = False
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    latency_ms: Optional[int] = None
    error_type: str
    error_message: Optional[str] = None


# Type alias for any analytics event
AiEvent = AiRequestEvent | AiResponseEvent | AiErrorEvent
