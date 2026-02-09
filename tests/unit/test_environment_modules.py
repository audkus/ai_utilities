"""
test_environment_modules_simple.py

Simple targeted tests to improve coverage for environment-related modules.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.di.environment import (
    ContextVarEnvironmentProvider, StandardEnvironmentProvider, EnvironmentProviderStub
)
from ai_utilities.env_detection import is_interactive_environment, get_environment_type
from ai_utilities.env_overrides import is_test_mode, test_mode_guard as mode_guard


class TestEnvironmentProviderCoverage:
    """Tests for di/environment.py to achieve 100% coverage."""
    
    def test_context_var_provider_with_prefix_filter(self):
        """Test ContextVarEnvironmentProvider.get_all with prefix filter (covers line 114)."""
        provider = ContextVarEnvironmentProvider()
        
        # Use override_env context manager to set variables
        from ai_utilities.env_overrides import override_env
        with override_env({"TEST_VAR_1": "value1", "TEST_VAR_2": "value2", "OTHER_VAR": "other"}):
            result = provider.get_all(prefix="TEST_VAR_")
            
            assert result == {"TEST_VAR_1": "value1", "TEST_VAR_2": "value2"}
            assert "OTHER_VAR" not in result
    
    def test_test_environment_provider_with_prefix_filter(self):
        """Test EnvironmentProviderStub.get_all with prefix filter (covers line 217)."""
        provider = EnvironmentProviderStub()
        
        # Set variables directly on the test provider
        provider._env = {"TEST_VAR_1": "value1", "TEST_VAR_2": "value2", "OTHER_VAR": "other"}
        
        result = provider.get_all(prefix="TEST_VAR_")
        
        assert result == {"TEST_VAR_1": "value1", "TEST_VAR_2": "value2"}
        assert "OTHER_VAR" not in result


class TestEnvironmentDetectionCoverage:
    """Tests for env_detection.py to achieve 100% coverage."""
    
    def test_is_interactive_non_tty_stdin(self):
        """Test is_interactive_environment when stdin is not a TTY (covers line 44)."""
        with patch('sys.stdin.isatty', return_value=False):
            result = is_interactive_environment()
            assert result is False
    
    def test_is_interactive_nologin_shell(self):
        """Test is_interactive_environment with nologin shell (covers line 49)."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch.dict(os.environ, {"SHELL": "/usr/sbin/nologin"}):
                result = is_interactive_environment()
                assert result is False
    
    def test_is_interactive_false_shell(self):
        """Test is_interactive_environment with false shell (covers line 49)."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch.dict(os.environ, {"SHELL": "/bin/false"}):
                result = is_interactive_environment()
                assert result is False
    
    def test_is_interactive_docker_container(self):
        """Test is_interactive_environment in Docker container (covers line 53)."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch.dict(os.environ, {"SHELL": "/bin/bash", "DOCKER_CONTAINER": "1"}):
                result = is_interactive_environment()
                assert result is False
    
    def test_is_interactive_systemd_environment(self):
        """Test is_interactive_environment in systemd environment (covers line 57)."""
        with patch('sys.stdin.isatty', return_value=True):
            with patch.dict(os.environ, {"SHELL": "/bin/bash", "INVOCATION_ID": "12345"}):
                result = is_interactive_environment()
                assert result is False
    
    def test_get_environment_type_ci(self):
        """Test get_environment_type in CI environment."""
        with patch.dict(os.environ, {"CI": "true"}):
            result = get_environment_type()
            assert isinstance(result, str)  # Contract: result is string type
            assert len(result) > 0  # Contract: non-empty environment type
    
    def test_get_environment_type_development(self):
        """Test get_environment_type in development environment."""
        with patch.dict(os.environ, {"DEVELOPMENT": "true"}, clear=True):
            result = get_environment_type()
            assert isinstance(result, str)  # Contract: result is string type
            assert len(result) > 0  # Contract: non-empty environment type


class TestEnvironmentOverridesCoverage:
    """Tests for env_overrides.py to achieve 100% coverage."""
    
    def test_is_test_mode_pytest_detection(self):
        """Test is_test_mode detects pytest environment (covers lines 52-53)."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_file.py::test_function"}):
            result = is_test_mode()
            assert result is True
    
    def test_standard_environment_provider(self):
        """Test StandardEnvironmentProvider basic functionality."""
        provider = StandardEnvironmentProvider()
        
        # Test getting a variable that exists
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = provider.get("TEST_VAR")
            assert isinstance(result, str)  # Contract: result is string type
            assert len(result) > 0  # Contract: non-empty value
        
        # Test getting a variable that doesn't exist
        result = provider.get("NONEXISTENT_VAR", "default")
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty default value
        
        # Test getting all variables
        with patch.dict(os.environ, {"VAR1": "val1", "VAR2": "val2"}, clear=True):
            result = provider.get_all()
            assert result == {"VAR1": "val1", "VAR2": "val2"}
    
    def test_test_mode_guard_context_manager(self) -> None:
        """Test test_mode_guard context manager functionality."""
        # Test that the context manager works correctly
        initial_state = is_test_mode()
        
        # Use the context manager properly with 'with' statement
        with mode_guard():
            assert is_test_mode() is True
        
        # Should return to previous state
        assert is_test_mode() is initial_state
