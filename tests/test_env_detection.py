"""Tests for env_detection.py module."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

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


class TestInteractiveEnvironment:
    """Test interactive environment detection."""
    
    def test_interactive_environment_default_true(self):
        """Test that default environment is considered interactive."""
        # Clear all CI indicators and ensure stdin is TTY
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stdin.isatty', return_value=True):
                # Temporarily remove pytest from sys.modules
                original_modules = sys.modules.copy()
                if 'pytest' in sys.modules:
                    del sys.modules['pytest']
                try:
                    assert is_interactive_environment() is True
                finally:
                    sys.modules.update(original_modules)
    
    def test_ci_environment_not_interactive(self):
        """Test that CI environments are not interactive."""
        ci_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "TRAVIS"]
        
        for var in ci_vars:
            with patch.dict(os.environ, {var: "true"}):
                assert is_interactive_environment() is False
    
    def test_pytest_environment_not_interactive(self):
        """Test that pytest environment is not interactive."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_something"}):
            assert is_interactive_environment() is False
    
    def test_pytest_module_not_interactive(self):
        """Test that pytest in sys.modules makes environment non-interactive."""
        with patch.dict(sys.modules, {'pytest': MagicMock()}):
            assert is_interactive_environment() is False
    
    def test_non_tty_not_interactive(self):
        """Test that non-TTY stdin is not interactive."""
        with patch('sys.stdin.isatty', return_value=False):
            assert is_interactive_environment() is False
    
    def test_nologin_shell_not_interactive(self):
        """Test that nologin shells are not interactive."""
        with patch.dict(os.environ, {"SHELL": "/bin/nologin"}):
            assert is_interactive_environment() is False
    
    def test_false_shell_not_interactive(self):
        """Test that false shells are not interactive."""
        with patch.dict(os.environ, {"SHELL": "/bin/false"}):
            assert is_interactive_environment() is False
    
    def test_docker_container_not_interactive(self):
        """Test that Docker containers are not interactive."""
        with patch.dict(os.environ, {"DOCKER_CONTAINER": "true"}):
            assert is_interactive_environment() is False
    
    def test_systemd_not_interactive(self):
        """Test that systemd environments are not interactive."""
        with patch.dict(os.environ, {"INVOCATION_ID": "something"}):
            assert is_interactive_environment() is False
    
    def test_daemon_process_not_interactive(self):
        """Test that daemon processes are not interactive."""
        with patch.dict(os.environ, {"DAEMON_PROCESS": "true"}):
            assert is_interactive_environment() is False


class TestCIEnvironment:
    """Test CI environment detection."""
    
    def test_no_ci_indicators(self):
        """Test that absence of CI indicators returns False."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_ci_environment() is False
    
    def test_generic_ci_detected(self):
        """Test that generic CI indicator is detected."""
        with patch.dict(os.environ, {"CI": "true"}):
            assert is_ci_environment() is True
    
    def test_github_actions_detected(self):
        """Test that GitHub Actions is detected."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert is_ci_environment() is True
    
    def test_gitlab_ci_detected(self):
        """Test that GitLab CI is detected."""
        with patch.dict(os.environ, {"GITLAB_CI": "true"}):
            assert is_ci_environment() is True
    
    def test_all_ci_indicators(self):
        """Test all CI indicators are detected."""
        ci_indicators = [
            "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI",
            "TRAVIS", "CIRCLECI", "JENKINS_URL", "AZURE_PIPELINES",
            "BITBUCKET_BUILD_NUMBER", "APPVEYOR", "CODEBUILD_BUILD_ID",
            "GOOGLE_CLOUD_PROJECT", "BUILDKITE"
        ]
        
        for indicator in ci_indicators:
            with patch.dict(os.environ, {indicator: "true"}):
                assert is_ci_environment() is True


class TestDevelopmentEnvironment:
    """Test development environment detection."""
    
    def test_no_dev_indicators(self):
        """Test that absence of dev indicators returns False."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_development_environment() is False
    
    def test_virtual_env_detected(self):
        """Test that virtual environment is detected."""
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
            assert is_development_environment() is True
    
    def test_conda_env_detected(self):
        """Test that Conda environment is detected."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base"}):
            assert is_development_environment() is True
    
    def test_pycharm_detected(self):
        """Test that PyCharm is detected."""
        with patch.dict(os.environ, {"PYCHARM_HOSTED": "1"}):
            assert is_development_environment() is True
    
    def test_vscode_detected(self):
        """Test that VS Code is detected."""
        with patch.dict(os.environ, {"VSCODE_PID": "12345"}):
            assert is_development_environment() is True
    
    def test_ipython_detected(self):
        """Test that IPython is detected."""
        with patch.dict(os.environ, {"IPython": "1"}):
            assert is_development_environment() is True


class TestEnvironmentType:
    """Test environment type classification."""
    
    def test_ci_environment_type(self):
        """Test CI environment type classification."""
        with patch.dict(os.environ, {"CI": "true"}):
            assert get_environment_type() == "CI/CD"
    
    def test_non_interactive_environment_type(self):
        """Test non-interactive environment type classification."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
            with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
                assert get_environment_type() == "Non-Interactive"
    
    def test_development_environment_type(self):
        """Test development environment type classification."""
        with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
            with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
                with patch.object(ai_utilities.env_detection, 'is_development_environment', return_value=True):
                    assert get_environment_type() == "Development"
    
    def test_interactive_environment_type(self):
        """Test interactive environment type classification."""
        with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
            with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
                with patch.object(ai_utilities.env_detection, 'is_development_environment', return_value=False):
                    assert get_environment_type() == "Interactive"


class TestSafeInput:
    """Test safe input functionality."""
    
    def test_safe_input_non_interactive_returns_default(self):
        """Test that non-interactive environment returns default."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
            result = safe_input("Enter value: ", "default_value")
            assert result == "default_value"
    
    def test_safe_input_interactive_gets_input(self):
        """Test that interactive environment gets user input."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
            with patch('builtins.input', return_value="user_input"):
                result = safe_input("Enter value: ", "default_value")
                assert result == "user_input"
    
    def test_safe_input_eof_error_returns_default(self):
        """Test that EOFError returns default."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
            with patch('builtins.input', side_effect=EOFError):
                result = safe_input("Enter value: ", "default_value")
                assert result == "default_value"
    
    def test_safe_input_keyboard_interrupt_returns_default(self):
        """Test that KeyboardInterrupt returns default."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
            with patch('builtins.input', side_effect=KeyboardInterrupt):
                result = safe_input("Enter value: ", "default_value")
                assert result == "default_value"
    
    def test_safe_input_empty_default(self):
        """Test safe input with empty default."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
            result = safe_input("Enter value: ")
            assert result == ""


class TestShouldPromptForReconfigure:
    """Test reconfigure prompt logic."""
    
    def test_should_prompt_interactive_non_ci(self):
        """Test that interactive non-CI environment should prompt."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
            with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
                assert should_prompt_for_reconfigure() is True
    
    def test_should_not_prompt_non_interactive(self):
        """Test that non-interactive environment should not prompt."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
            assert should_prompt_for_reconfigure() is False
    
    def test_should_not_prompt_ci(self):
        """Test that CI environment should not prompt."""
        with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
            with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=True):
                assert should_prompt_for_reconfigure() is False


class TestLogEnvironmentInfo:
    """Test environment info logging."""
    
    def test_log_environment_info_ci(self):
        """Test logging CI environment info."""
        with patch.object(ai_utilities.env_detection, 'get_environment_type', return_value="CI/CD"):
            with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=False):
                with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=True):
                    with patch('builtins.print') as mock_print:
                        log_environment_info()
                        
                        # Check that print was called with expected values
                        mock_print.assert_any_call("Environment: CI/CD")
                        mock_print.assert_any_call("Interactive: False")
                        mock_print.assert_any_call("CI/CD: True")
                        mock_print.assert_any_call("Non-interactive environment detected - will skip prompts")
    
    def test_log_environment_info_development(self):
        """Test logging development environment info."""
        with patch.object(ai_utilities.env_detection, 'get_environment_type', return_value="Development"):
            with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
                with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
                    with patch('builtins.print') as mock_print:
                        log_environment_info()
                        
                        mock_print.assert_any_call("Environment: Development")
                        mock_print.assert_any_call("Interactive: True")
                        mock_print.assert_any_call("CI/CD: False")
    
    def test_log_environment_info_interactive(self):
        """Test logging interactive environment info."""
        with patch.object(ai_utilities.env_detection, 'get_environment_type', return_value="Interactive"):
            with patch.object(ai_utilities.env_detection, 'is_interactive_environment', return_value=True):
                with patch.object(ai_utilities.env_detection, 'is_ci_environment', return_value=False):
                    with patch('builtins.print') as mock_print:
                        log_environment_info()
                        
                        mock_print.assert_any_call("Environment: Interactive")
                        mock_print.assert_any_call("Interactive: True")
                        mock_print.assert_any_call("CI/CD: False")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_environment_variables(self):
        """Test behavior with empty environment variables."""
        with patch.dict(os.environ, {"CI": "", "VIRTUAL_ENV": ""}):
            assert is_ci_environment() is False
            assert is_development_environment() is False
    
    def test_whitespace_environment_variables(self):
        """Test behavior with whitespace environment variables."""
        with patch.dict(os.environ, {"CI": "   "}):
            # Any non-empty string should be truthy
            assert is_ci_environment() is True
    
    def test_missing_stdin_isatty(self):
        """Test behavior when stdin.isatty method is missing."""
        with patch('sys.stdin.isatty', side_effect=AttributeError):
            # Should handle gracefully and return False
            assert is_interactive_environment() is False
    
    def test_environment_precedence(self):
        """Test that CI detection takes precedence over other indicators."""
        # Even if we have dev indicators, CI should still be detected as CI
        with patch.dict(os.environ, {"CI": "true", "VIRTUAL_ENV": "/path/to/venv"}):
            assert is_ci_environment() is True
            assert get_environment_type() == "CI/CD"
