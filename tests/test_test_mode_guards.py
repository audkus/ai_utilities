"""Tests for test-mode guards functionality."""

import os
import warnings
import pytest

from ai_utilities.env_overrides import (
    override_env, 
    is_test_mode, 
    get_safe_env
)
from ai_utilities.env_overrides import test_mode_guard as _test_mode_guard


def test_is_test_mode_detects_pytest():
    """Test that is_test_mode correctly detects pytest execution."""
    # Should be True when running under pytest
    assert is_test_mode() is True


def test_test_mode_guard_context():
    """Test that test_mode_guard context works correctly."""
    # Should already be True in pytest, but test the context anyway
    initial_state = is_test_mode()
    
    with _test_mode_guard():
        assert is_test_mode() is True
    
    # Should return to previous state
    assert is_test_mode() is initial_state


def test_nested_override_warning():
    """Test that nested environment overrides generate warnings in test mode."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Create nested overrides with conflicting keys
        with override_env({"AI_MODEL": "outer"}):
            with override_env({"AI_MODEL": "inner"}):
                pass  # Should trigger warning
        
        # Check that warning was issued
        assert len(w) > 0
        warning_messages = [str(warning.message) for warning in w]
        assert any("Nested environment overrides detected" in msg for msg in warning_messages)
        assert any("AI_MODEL" in msg for msg in warning_messages)


def test_safe_env_warns_about_direct_access():
    """Test that get_safe_env warns about direct environment access in test mode."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # This should generate a warning about direct access
        result = get_safe_env("PATH")
        
        # Should still return the value but with a warning
        assert result is not None
        assert len(w) > 0
        warning_messages = [str(warning.message) for warning in w]
        assert any("Direct os.environ access detected" in msg for msg in warning_messages)
        assert any("PATH" in msg for msg in warning_messages)


def test_safe_env_respects_overrides():
    """Test that get_safe_env respects contextvar overrides."""
    # Set up an override
    with override_env({"AI_TEST_VAR": "override_value"}):
        # This should not generate a warning since we're using override_env
        result = get_safe_env("AI_TEST_VAR", "default")
        assert result == "override_value"
    
    # Outside the override, should get default and generate warning
    with pytest.warns(UserWarning, match="Direct os.environ access detected"):
        result = get_safe_env("AI_TEST_VAR", "default")
        assert result == "default"


def test_no_warning_for_non_nested_overrides():
    """Test that non-nested overrides don't generate warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Non-nested overrides should not warn
        with override_env({"AI_MODEL": "test"}):
            pass
        
        with override_env({"AI_TEMPERATURE": "0.5"}):
            pass
        
        # Should not have nested override warnings
        warning_messages = [str(warning.message) for warning in w]
        nested_warnings = [msg for msg in warning_messages if "Nested environment overrides" in msg]
        assert len(nested_warnings) == 0


def test_no_warning_for_different_keys():
    """Test that nested overrides with different keys don't warn."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Nested overrides with different keys should not warn
        with override_env({"AI_MODEL": "test"}):
            with override_env({"AI_TEMPERATURE": "0.5"}):
                pass
        
        # Should not have nested override warnings
        warning_messages = [str(warning.message) for warning in w]
        nested_warnings = [msg for msg in warning_messages if "Nested environment overrides" in msg]
        assert len(nested_warnings) == 0
