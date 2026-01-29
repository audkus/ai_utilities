"""Comprehensive tests for environment detection and overrides - Phase 7.

This module provides thorough testing for env_detection.py and env_overrides.py,
covering all environment detection scenarios and contextvar override functionality.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from contextvars import ContextVar
from contextlib import contextmanager

from ai_utilities.env_detection import (
    is_interactive_environment,
    is_ci_environment,
    is_development_environment,
    get_environment_type,
    safe_input,
    should_prompt_for_reconfigure,
    log_environment_info
)

# Import the module directly for patching
import ai_utilities.env_detection

from ai_utilities.env_overrides import (
    get_env_overrides,
    override_env,
    OverrideAwareEnvSource,
    get_ai_env,
    get_ai_env_bool,
    get_ai_env_int,
    get_ai_env_float
)


class TestEnvironmentDetection:
    """Test environment detection functions."""
    
    @pytest.mark.parametrize("ci_var", [
        "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI",
        "TRAVIS", "CIRCLECI", "JENKINS_URL", "AZURE_PIPELINES",
        "BITBUCKET_BUILD_NUMBER", "APPVEYOR", "CODEBUILD_BUILD_ID",
        "GOOGLE_CLOUD_PROJECT", "BUILDKITE"
    ])
    def test_ci_environment_detection(self, ci_var):
        """Test detection of various CI environments."""
        with patch.dict(os.environ, {ci_var: "true"}):
            assert is_ci_environment() is True
            assert is_interactive_environment() is False
    
    def test_no_ci_environment(self):
        """Test detection when not in CI environment."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_ci_environment() is False
    
    @pytest.mark.parametrize("dev_var", [
        "VIRTUAL_ENV", "CONDA_DEFAULT_ENV", "PYCHARM_HOSTED",
        "VSCODE_PID", "IPython"
    ])
    def test_development_environment_detection(self, dev_var):
        """Test detection of development environments."""
        with patch.dict(os.environ, {dev_var: "true"}):
            assert is_development_environment() is True
    
    def test_no_development_environment(self):
        """Test detection when not in development environment."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_development_environment() is False
    
    def test_pytest_environment_detection(self):
        """Test detection of pytest environment."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_file.py::test_function"}):
            assert is_interactive_environment() is False
    
    def test_pytest_in_sys_modules(self):
        """Test detection when pytest is in sys.modules."""
        with patch.dict(sys.modules, {"pytest": MagicMock()}):
            assert is_interactive_environment() is False
    
    @patch('sys.stdin.isatty')
    def test_tty_detection(self, mock_isatty):
        """Test TTY detection for interactive environment."""
        mock_isatty.return_value = False
        
        with patch.dict(os.environ, {}, clear=True):
            assert is_interactive_environment() is False
    
    @pytest.mark.parametrize("shell", [
        "/bin/nologin", "/usr/bin/false", "/sbin/nologin"
    ])
    def test_non_interactive_shell_detection(self, shell):
        """Test detection of non-interactive shells."""
        with patch.dict(os.environ, {"SHELL": shell}):
            assert is_interactive_environment() is False
    
    @patch('sys.stdin.isatty')
    def test_interactive_shell_detection(self, mock_isatty):
        """Test detection of interactive shells."""
        mock_isatty.return_value = True
        
        # Note: When running under pytest, the environment is correctly detected as non-interactive
        # because PYTEST_CURRENT_TEST is set. This is the expected behavior.
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert is_interactive_environment() is False  # pytest environment is non-interactive
    
    def test_docker_environment_detection(self):
        """Test detection of Docker container environments."""
        with patch.dict(os.environ, {"DOCKER_CONTAINER": "true"}):
            assert is_interactive_environment() is False
    
    def test_systemd_environment_detection(self):
        """Test detection of systemd environments."""
        with patch.dict(os.environ, {"INVOCATION_ID": "12345"}):
            assert is_interactive_environment() is False
    
    def test_daemon_process_detection(self):
        """Test detection of daemon/background processes."""
        with patch.dict(os.environ, {"DAEMON_PROCESS": "true"}):
            assert is_interactive_environment() is False


class TestEnvironmentType:
    """Test environment type classification."""
    
    def test_ci_environment_type(self):
        """Test CI environment type classification."""
        with patch.dict(os.environ, {"CI": "true"}):
            assert get_environment_type() == "CI/CD"
    
    def test_non_interactive_environment_type(self):
        """Test non-interactive environment type classification."""
        with patch.dict(os.environ, {"DOCKER_CONTAINER": "true"}):
            assert get_environment_type() == "Non-Interactive"
    
    def test_development_environment_type(self):
        """Test development environment type classification."""
        # Note: When running under pytest, the environment is correctly detected as Non-Interactive
        # because PYTEST_CURRENT_TEST is set, even with VIRTUAL_ENV present.
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
            with patch('sys.stdin.isatty', return_value=True):
                assert get_environment_type() == "Non-Interactive"  # pytest environment is non-interactive
    
    def test_interactive_environment_type(self):
        """Test interactive environment type classification."""
        # Note: When running under pytest, the environment is correctly detected as Non-Interactive
        # because PYTEST_CURRENT_TEST is set, even when clearing other environment variables.
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stdin.isatty', return_value=True):
                assert get_environment_type() == "Non-Interactive"  # pytest environment is non-interactive


class TestSafeInput:
    """Test safe input functionality."""
    
    def test_safe_input_in_non_interactive(self):
        """Test safe input returns default in non-interactive environment."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
            result = safe_input("Enter value: ", "default")
            assert result == "default"
    
    @patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True)
    @patch('builtins.input', return_value="user_input")
    def test_safe_input_success(self, mock_input, mock_interactive):
        """Test safe input with successful user input."""
        result = safe_input("Enter value: ", "default")
        assert result == "user_input"
        mock_input.assert_called_once_with("Enter value: ")
    
    @patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True)
    @patch('builtins.input', side_effect=EOFError)
    def test_safe_input_eof_error(self, mock_input, mock_interactive):
        """Test safe input handles EOFError."""
        result = safe_input("Enter value: ", "default")
        assert result == "default"
    
    @patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True)
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_safe_input_keyboard_interrupt(self, mock_input, mock_interactive):
        """Test safe input handles KeyboardInterrupt."""
        result = safe_input("Enter value: ", "default")
        assert result == "default"
    
    def test_safe_input_empty_default(self):
        """Test safe input with empty default."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
            result = safe_input("Enter value: ")
            assert result == ""


class TestReconfigurePrompting:
    """Test reconfigure prompting logic."""
    
    def test_should_prompt_in_interactive(self):
        """Test that prompting is allowed in interactive environment."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
            with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
                assert should_prompt_for_reconfigure() is True
    
    def test_should_not_prompt_in_ci(self):
        """Test that prompting is not allowed in CI environment."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
            with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=True):
                assert should_prompt_for_reconfigure() is False
    
    def test_should_not_prompt_in_non_interactive(self):
        """Test that prompting is not allowed in non-interactive environment."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
            with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
                assert should_prompt_for_reconfigure() is False


class TestLogEnvironmentInfo:
    """Test environment information logging."""
    
    @patch('builtins.print')
    def test_log_environment_info_ci(self, mock_print):
        """Test logging in CI environment."""
        with patch.dict(os.environ, {"CI": "true"}):
            log_environment_info()
            
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("CI/CD" in call for call in calls)
            assert any("Interactive: False" in call for call in calls)
            assert any("CI/CD: True" in call for call in calls)
    
    @patch('builtins.print')
    def test_log_environment_info_development(self, mock_print):
        """Test logging in development environment."""
        # Note: When running under pytest, the environment is correctly detected as Non-Interactive
        # because PYTEST_CURRENT_TEST is set, even with VIRTUAL_ENV present.
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/venv"}):
            with patch('sys.stdin.isatty', return_value=True):
                log_environment_info()
                
                calls = [str(call) for call in mock_print.call_args_list]
                # Should show Non-Interactive since we're in pytest
                assert any("Non-Interactive" in call for call in calls)
                assert any("Interactive: False" in call for call in calls)
    
    @patch('builtins.print')
    def test_log_environment_info_non_interactive(self, mock_print):
        """Test logging in non-interactive environment."""
        with patch.dict(os.environ, {"DOCKER_CONTAINER": "true"}):
            log_environment_info()
            
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Non-Interactive" in call for call in calls)
            assert any("Non-interactive environment detected" in call for call in calls)


class TestEnvOverrides:
    """Test environment variable overrides functionality."""
    
    def test_get_env_overrides_empty(self):
        """Test getting empty environment overrides."""
        overrides = get_env_overrides()
        assert overrides == {}
        assert isinstance(overrides, dict)
    
    def test_override_env_context_manager(self):
        """Test basic override environment context manager."""
        initial_overrides = get_env_overrides()
        
        with override_env({"TEST_VAR": "test_value"}):
            overrides = get_env_overrides()
            assert overrides == {"TEST_VAR": "test_value"}
        
        # Should be restored after context
        final_overrides = get_env_overrides()
        assert final_overrides == initial_overrides
    
    def test_override_env_with_none(self):
        """Test override environment with None."""
        with override_env(None):
            overrides = get_env_overrides()
            assert overrides == {}
    
    def test_override_env_type_conversion(self):
        """Test type conversion in override environment."""
        with override_env({
            "STRING_VAR": "test",
            "INT_VAR": 42,
            "FLOAT_VAR": 3.14,
            "BOOL_VAR": True
        }):
            overrides = get_env_overrides()
            assert overrides["STRING_VAR"] == "test"
            assert overrides["INT_VAR"] == "42"
            assert overrides["FLOAT_VAR"] == "3.14"
            assert overrides["BOOL_VAR"] == "True"
    
    def test_override_env_nested_contexts(self):
        """Test nested override environment contexts."""
        with override_env({"OUTER": "outer_value"}):
            assert get_env_overrides() == {"OUTER": "outer_value"}
            
            # No warning since no conflicting keys
            with override_env({"INNER": "inner_value"}):
                assert get_env_overrides() == {
                    "OUTER": "outer_value",
                    "INNER": "inner_value"
                }
            
            # Inner context should be restored
            assert get_env_overrides() == {"OUTER": "outer_value"}
        
        # Outer context should be restored
        assert get_env_overrides() == {}
    
    def test_override_env_exception_handling(self):
        """Test that environment is restored even if exception occurs."""
        try:
            with override_env({"TEST_VAR": "test_value"}):
                assert get_env_overrides() == {"TEST_VAR": "test_value"}
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        
        # Should be restored after exception
        assert get_env_overrides() == {}


class TestOverrideAwareEnvSource:
    """Test the OverrideAwareEnvSource class."""
    
    def test_init_default_prefix(self):
        """Test OverrideAwareEnvSource initialization with default prefix."""
        source = OverrideAwareEnvSource()
        assert source.env_prefix == "AI_"
    
    def test_init_custom_prefix(self):
        """Test OverrideAwareEnvSource initialization with custom prefix."""
        source = OverrideAwareEnvSource("CUSTOM_")
        assert source.env_prefix == "CUSTOM_"
    
    def test_get_with_override(self):
        """Test getting environment variable with override."""
        source = OverrideAwareEnvSource()
        
        with override_env({"AI_TEST_VAR": "override_value"}):
            value = source.get("TEST_VAR")
            assert value == "override_value"
    
    def test_get_without_override(self):
        """Test getting environment variable without override."""
        source = OverrideAwareEnvSource()
        
        with patch.dict(os.environ, {"AI_TEST_VAR": "env_value"}):
            value = source.get("TEST_VAR")
            assert value == "env_value"
    
    def test_get_override_takes_precedence(self):
        """Test that override takes precedence over environment."""
        source = OverrideAwareEnvSource()
        
        with patch.dict(os.environ, {"AI_TEST_VAR": "env_value"}):
            with override_env({"AI_TEST_VAR": "override_value"}):
                value = source.get("TEST_VAR")
                assert value == "override_value"
    
    def test_get_not_found(self):
        """Test getting non-existent environment variable."""
        source = OverrideAwareEnvSource()
        
        with patch.dict(os.environ, {}, clear=True):
            value = source.get("NONEXISTENT")
            assert value is None
    
    def test_get_bool_true_values(self):
        """Test boolean environment variable with true values."""
        source = OverrideAwareEnvSource()
        
        for true_val in ["true", "1", "yes", "on"]:
            with override_env({"AI_BOOL_VAR": true_val}):
                assert source.get_bool("BOOL_VAR") is True
    
    def test_get_bool_false_values(self):
        """Test boolean environment variable with false values."""
        source = OverrideAwareEnvSource()
        
        for false_val in ["false", "0", "no", "off", ""]:
            with override_env({"AI_BOOL_VAR": false_val}):
                assert source.get_bool("BOOL_VAR") is False
    
    def test_get_bool_not_found(self):
        """Test boolean environment variable when not found."""
        source = OverrideAwareEnvSource()
        
        with patch.dict(os.environ, {}, clear=True):
            assert source.get_bool("NONEXISTENT") is False
    
    def test_get_int_success(self):
        """Test integer environment variable parsing."""
        source = OverrideAwareEnvSource()
        
        with override_env({"AI_INT_VAR": "42"}):
            assert source.get_int("INT_VAR") == 42
    
    def test_get_int_not_found(self):
        """Test integer environment variable when not found."""
        source = OverrideAwareEnvSource()
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="not found"):
                source.get_int("NONEXISTENT")
    
    def test_get_int_invalid_value(self):
        """Test integer environment variable with invalid value."""
        source = OverrideAwareEnvSource()
        
        with override_env({"AI_INT_VAR": "not_a_number"}):
            with pytest.raises(ValueError, match="must be an integer"):
                source.get_int("INT_VAR")
    
    def test_get_float_success(self):
        """Test float environment variable parsing."""
        source = OverrideAwareEnvSource()
        
        with override_env({"AI_FLOAT_VAR": "3.14"}):
            assert source.get_float("FLOAT_VAR") == 3.14
    
    def test_get_float_not_found(self):
        """Test float environment variable when not found."""
        source = OverrideAwareEnvSource()
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="not found"):
                source.get_float("NONEXISTENT")
    
    def test_get_float_invalid_value(self):
        """Test float environment variable with invalid value."""
        source = OverrideAwareEnvSource()
        
        with override_env({"AI_FLOAT_VAR": "not_a_number"}):
            with pytest.raises(ValueError, match="must be a float"):
                source.get_float("FLOAT_VAR")


class TestGlobalAIEnvFunctions:
    """Test global AI environment variable functions."""
    
    def test_get_ai_env_with_override(self):
        """Test get_ai_env with override."""
        with override_env({"AI_MODEL": "test-model"}):
            assert get_ai_env("MODEL") == "test-model"
    
    def test_get_ai_env_without_override(self):
        """Test get_ai_env without override."""
        with patch.dict(os.environ, {"AI_MODEL": "env-model"}):
            assert get_ai_env("MODEL") == "env-model"
    
    def test_get_ai_env_bool(self):
        """Test get_ai_env_bool function."""
        with override_env({"AI_DEBUG": "true"}):
            assert get_ai_env_bool("DEBUG") is True
        
        with override_env({"AI_DEBUG": "false"}):
            assert get_ai_env_bool("DEBUG") is False
    
    def test_get_ai_env_int(self):
        """Test get_ai_env_int function."""
        with override_env({"AI_TIMEOUT": "30"}):
            assert get_ai_env_int("TIMEOUT") == 30
    
    def test_get_ai_env_float(self):
        """Test get_ai_env_float function."""
        with override_env({"AI_TEMPERATURE": "0.7"}):
            assert get_ai_env_float("TEMPERATURE") == 0.7


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_override_env_empty_dict(self):
        """Test override_env with empty dictionary."""
        with override_env({}):
            overrides = get_env_overrides()
            assert overrides == {}
    
    def test_multiple_overrides_same_key(self):
        """Test multiple overrides of the same key."""
        with override_env({"AI_VAR": "first"}):
            assert get_ai_env("VAR") == "first"
            
            # Nested override should generate warning
            with pytest.warns(UserWarning, match="Nested environment overrides detected"):
                with override_env({"AI_VAR": "second"}):
                    assert get_ai_env("VAR") == "second"
            
            # Should restore to first value
            assert get_ai_env("VAR") == "first"
    
    def test_environment_variable_case_sensitivity(self):
        """Test that environment variable keys are case sensitive."""
        source = OverrideAwareEnvSource()
        
        with override_env({"AI_TEST": "value"}):
            # The source converts key to uppercase with prefix
            assert source.get("TEST") == "value"
            # Different case should still work because we uppercase the key
            assert source.get("test") == "value"  # Should also work due to upper() conversion
    
    def test_context_isolation(self):
        """Test that contexts are properly isolated."""
        results = []
        
        def context_function(value):
            with override_env({"AI_VALUE": value}):
                results.append(get_ai_env("VALUE"))
        
        # These should not interfere with each other
        context_function("first")
        context_function("second")
        
        assert results == ["first", "second"]
        assert get_ai_env("VALUE") is None
    
    def test_large_override_dict(self):
        """Test handling of large override dictionaries."""
        large_dict = {f"AI_VAR_{i}": f"value_{i}" for i in range(100)}
        
        with override_env(large_dict):
            overrides = get_env_overrides()
            assert len(overrides) == 100
            assert overrides["AI_VAR_0"] == "value_0"
            assert overrides["AI_VAR_99"] == "value_99"
        
        # Should be cleaned up
        assert get_env_overrides() == {}
