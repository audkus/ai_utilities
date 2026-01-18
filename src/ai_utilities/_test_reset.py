"""
Test isolation utilities for resetting global state.

This module provides functions to reset global state between tests
to prevent order-dependent test failures.
"""

import os
from typing import Any, Dict


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
            # Clear any cached settings
            if hasattr(AiSettings.model_config, '_env_file_cache'):
                AiSettings.model_config._env_file_cache.clear()
        
        # Reset class-level cached values
        if hasattr(AiSettings, '_cached_settings'):
            AiSettings._cached_settings.clear()
    except (ImportError, Exception):
        # Handle any exception gracefully
        pass


def _reset_provider_factory_state() -> None:
    """Reset provider factory singleton state."""
    try:
        from ai_utilities.providers.provider_factory import ProviderFactory
        
        # Reset factory singleton if it exists
        if hasattr(ProviderFactory, '_instance'):
            ProviderFactory._instance = None
        
        # Reset provider caches
        if hasattr(ProviderFactory, '_provider_cache'):
            ProviderFactory._provider_cache.clear()
            
    except ImportError:
        # Module might not exist
        pass


def _reset_config_resolver_caches() -> None:
    """Reset configuration resolver caches."""
    try:
        from ai_utilities.config_resolver import ConfigResolver
        
        # Reset resolver caches
        if hasattr(ConfigResolver, '_config_cache'):
            ConfigResolver._config_cache.clear()
        
        if hasattr(ConfigResolver, '_env_cache'):
            ConfigResolver._env_cache.clear()
            
    except ImportError:
        # Module might not exist
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
        state['contextvar_overrides'] = get_env_overrides()
    except (ImportError, Exception):
        # Handle any exception gracefully
        state['contextvar_overrides'] = {}
    
    return state


def _reset_metrics_registry() -> None:
    """Reset metrics registry to clean state."""
    try:
        from ai_utilities.metrics import metrics
        
        # Clear all metrics
        metrics._metrics.clear()
        
        # Reset any internal state
        if hasattr(metrics, '_counters'):
            metrics._counters.clear()
        if hasattr(metrics, '_gauges'):
            metrics._gauges.clear()
        if hasattr(metrics, '_histograms'):
            metrics._histograms.clear()
            
    except (ImportError, Exception):
        # Handle any exception gracefully
        pass
