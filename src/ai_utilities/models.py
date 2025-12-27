"""Shared models for sync and async AI clients."""

from typing import Any, Dict, Optional, Union

from pydantic import BaseModel


class AskResult(BaseModel):
    """Result of a single AI request."""
    
    # Required fields
    prompt: str
    response: Optional[Union[str, Dict[str, Any]]]
    error: Optional[str]
    duration_s: float
    
    # Optional fields
    tokens_used: Optional[int] = None
    model: Optional[str] = None
