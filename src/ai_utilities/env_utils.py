"""
Environment variable utilities to prevent contamination in application code.

This module provides utilities for managing environment variables in a way that
prevents contamination between different parts of the application.
"""

import os
import contextlib
from typing import Dict, Optional, Any


def cleanup_ai_env_vars() -> None:
    """Clean up all AI environment variables to prevent contamination."""
    env_vars_to_clear = [k for k in os.environ.keys() if k.startswith('AI_')]
    for var in env_vars_to_clear:
        if var in os.environ:
            del os.environ[var]


def get_ai_env_vars() -> Dict[str, str]:
    """
    Get all AI environment variables.
    
    Returns:
        Dictionary of AI environment variables
    """
    return {k: v for k, v in os.environ.items() if k.startswith('AI_')}


def validate_ai_env_vars() -> Dict[str, str]:
    """
    Validate and clean AI environment variables.
    
    Returns:
        Dictionary of valid AI environment variables
    """
    valid_vars = {}
    
    # Known AI environment variables
    known_vars = {
        'AI_API_KEY', 'AI_MODEL', 'AI_TEMPERATURE', 'AI_MAX_TOKENS',
        'AI_BASE_URL', 'AI_TIMEOUT', 'AI_UPDATE_CHECK_DAYS', 'AI_USE_AI',
        'AI_MEMORY_THRESHOLD', 'AI_MODEL_RPM', 'AI_MODEL_TPM', 'AI_MODEL_TPD',
        'AI_GPT_4_RPM', 'AI_GPT_4_TPM', 'AI_GPT_4_TPD',
        'AI_GPT_3_5_TURBO_RPM', 'AI_GPT_3_5_TURBO_TPM', 'AI_GPT_3_5_TURBO_TPD',
        'AI_GPT_4_TURBO_RPM', 'AI_GPT_4_TURBO_TPM', 'AI_GPT_4_TURBO_TPD',
        'AI_USAGE_SCOPE', 'AI_USAGE_CLIENT_ID'
    }
    
    for key, value in os.environ.items():
        if key.startswith('AI_') and key in known_vars:
            valid_vars[key] = value
    
    return valid_vars
