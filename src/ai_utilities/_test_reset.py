"""
Test isolation utilities for resetting global state.

This module provides functions to reset global state between tests
to prevent order-dependent test failures.
"""

import os
from typing import Any, Dict


def _reset_usage_tracker_state():
    """Reset usage tracker global state to prevent test contamination."""
    try:
        import sys
        from .usage_tracker import ThreadSafeUsageTracker
        
        # Clear shared locks that accumulate across tests
        if hasattr(ThreadSafeUsageTracker, '_shared_locks'):
            ThreadSafeUsageTracker._shared_locks.clear()
            
        # Remove the module from sys.modules to ensure fresh import
        # This fixes enum contamination issues
        module_names_to_remove = [
            'ai_utilities.usage_tracker',
            'ai_utilities.usage_tracker.ThreadSafeUsageTracker',
            'ai_utilities.usage_tracker.UsageScope',
            'ai_utilities.usage_tracker.UsageStats'
        ]
        
        for module_name in module_names_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]
            
    except ImportError:
        # Module not available, skip
        pass


def reset_global_state_for_tests() -> None:
    """
    Reset all global/module caches and loaded-once flags.
    
    This function safely resets global state that might cause test pollution.
    It can be called multiple times without side effects.
    
    Resets:
    - AI_* and provider-specific environment variables
    - AiSettings cached environment state
    - Provider factory singletons  
    - Configuration resolver caches
    - SSL warning emission flag
    - Metrics registry
    - ContextVar state
    - Audio processor global state
    - Any module-level global state
    """
    try:
        # Clear environment variables first
        _clear_environment_variables()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset SSL warning flag
        _reset_ssl_warning_flag()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset AiSettings/pydantic-settings cache
        _reset_ai_settings_cache()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset provider factory state
        _reset_provider_factory_state()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset configuration resolver caches
        _reset_config_resolver_caches()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset contextvar state
        _reset_contextvar_state()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset metrics registry
        _reset_metrics_registry()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset usage tracker state
        _reset_usage_tracker_state()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass
    
    try:
        # Reset audio processor state
        _reset_audio_processor_state()
    except Exception:
        # Ignore errors - this is a safety mechanism
        pass


def _clear_environment_variables() -> None:
    """Clear AI_* and provider-specific environment variables."""
    # Environment variable prefixes to clear
    prefixes = [
        'AI_',  # AI utilities variables
        'OPENAI_',  # OpenAI-specific variables
        'GROQ_',  # Groq-specific variables
        'TOGETHER_',  # Together AI variables
        'OPENROUTER_',  # OpenRouter variables
        'OLLAMA_',  # Ollama variables
        'LMSTUDIO_',  # LM Studio variables
        'FASTCHAT_',  # FastChat variables
        'ANTHROPIC_',  # Anthropic variables
    ]
    
    # Clear variables matching prefixes
    vars_to_clear = []
    for var_name in os.environ:
        if any(var_name.startswith(prefix) for prefix in prefixes):
            vars_to_clear.append(var_name)
    
    for var_name in vars_to_clear:
        del os.environ[var_name]


def _reset_ssl_warning_flag() -> None:
    """Reset SSL warning emission flag."""
    try:
        from ai_utilities.ssl_check import _warning_emitted
        _warning_emitted = False
    except (ImportError, Exception):
        # Handle any exception gracefully
        pass


def _reset_ai_settings_cache() -> None:
    """Reset AiSettings cached environment state."""
    try:
        # Import lazily to avoid import-time side effects
        from ai_utilities.config_models import AiSettings
        
        # Reset pydantic-settings internal cache if it exists
        if hasattr(AiSettings, 'model_config'):
            # Clear any cached settings - avoid private pydantic internals
            # Rebuild settings model to clear caches instead of touching private attributes
            pass
        
        # Reset class-level cached values
        if hasattr(AiSettings, '_cached_settings'):
            AiSettings._cached_settings.clear()
    except (ImportError, Exception):
        # Handle any exception gracefully
        pass


def _reset_provider_factory_state() -> None:
    """Reset provider factory singleton state."""
    # No factory singleton to reset - provider_factory module uses functions only
    pass


def _reset_config_resolver_caches() -> None:
    """Reset configuration resolver caches."""
    # ConfigResolver doesn't exist as a class - config_resolver module uses functions only
    pass


def _reset_contextvar_state() -> None:
    """Reset contextvar state to clean defaults."""
    try:
        from ai_utilities.env_overrides import _reset_all_overrides
        
        # Reset all contextvar overrides
        _reset_all_overrides()
        
    except (ImportError, Exception):
        # Module might not exist or reset might fail
        pass


def _reset_audio_processor_state() -> None:
    """Reset audio processor global state."""
    try:
        # Clear any module-level caches in audio processor
        import sys
        
        # Remove audio modules from cache to force fresh import
        audio_modules = [
            'ai_utilities.audio.audio_processor',
            'ai_utilities.audio.audio_utils',
            'ai_utilities.audio.audio_models',
        ]
        
        for module_name in audio_modules:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # Reset Pydantic model caches
        _reset_pydantic_caches()
                
    except (ImportError, Exception):
        # Handle any exception gracefully
        pass


def _reset_pydantic_caches() -> None:
    """Reset Pydantic model caches and validation state."""
    try:
        # Clear Pydantic model caches
        import pydantic
        if hasattr(pydantic, '__pydantic_cache__'):
            cache = getattr(pydantic, '__pydantic_cache__')
            if hasattr(cache, 'clear'):
                cache.clear()
        
        # Reset pydantic-core validation caches
        import pydantic_core
        if hasattr(pydantic_core, '__pydantic_core_cache__'):
            cache = getattr(pydantic_core, '__pydantic_core_cache__')
            if hasattr(cache, 'clear'):
                cache.clear()
            
    except (ImportError, Exception):
        # Handle any exception gracefully
        pass


def get_current_global_state() -> Dict[str, Any]:
    """
    Get current global state for debugging purposes.
    
    Returns:
        Dictionary containing current global state values
    """
    state = {}
    
    # Environment state
    ai_env_vars = {k: v for k, v in os.environ.items() if k.startswith('AI_')}
    state['ai_environment_vars'] = ai_env_vars
    
    try:
        from ai_utilities.env_overrides import get_env_overrides
        overrides = get_env_overrides()
        state['contextvar_overrides'] = overrides if isinstance(overrides, dict) else {}
    except (ImportError, Exception):
        # Handle any exception gracefully
        state['contextvar_overrides'] = {}
    
    return state


def _reset_metrics_registry() -> None:
    """Reset metrics registry to clean state."""
    try:
        from ai_utilities.metrics import MetricsRegistry
        
        # Reset the singleton registry
        registry = MetricsRegistry()
        registry.reset()
            
    except (ImportError, Exception):
        # Handle any exception gracefully
        pass
