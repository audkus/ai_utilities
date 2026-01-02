"""
Environment variable utilities to prevent contamination in application code.

This module provides utilities for managing environment variables in a way that
prevents contamination between different parts of the application.
"""

import os
from contextlib import contextmanager
from typing import Dict, Optional


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
        if key in known_vars:
            valid_vars[key] = value
    
    return valid_vars


@contextmanager
def isolated_env_context(env_vars: Optional[Dict[str, str]] = None):
    """
    Context manager for isolated environment variable manipulation.
    
    Temporarily sets environment variables and restores them after the context.
    This is safer than direct os.environ manipulation.
    
    Args:
        env_vars: Dictionary of environment variables to set temporarily
    
    Yields:
        None
    
    Example:
        with isolated_env_context({'AI_MODEL': 'test-model'}):
            # AI_MODEL is set to 'test-model' here
            config = AIConfig()
        # Original environment is restored here
    """
    # Store original environment variables that we'll modify
    original_env = {}
    
    if env_vars:
        for key, value in env_vars.items():
            # Store original value if it exists
            if key in os.environ:
                original_env[key] = os.environ[key]
            # Set new value
            os.environ[key] = value
    
    try:
        yield
    finally:
        # Restore original environment
        for key, value in original_env.items():
            os.environ[key] = value
        
        # Remove any variables that didn't exist originally
        if env_vars:
            for key in env_vars:
                if key not in original_env and key in os.environ:
                    del os.environ[key]
