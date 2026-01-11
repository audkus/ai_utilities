"""Tests for environment detection and safe interactive setup.

These tests ensure that AiClient doesn't block in non-interactive environments
like CI/CD, server processes, or automated scripts.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from ai_utilities.env_detection import (
    is_interactive_environment,
    is_ci_environment,
    is_development_environment,
    get_environment_type,
    safe_input,
    should_prompt_for_reconfigure,
)
from ai_utilities.client import AiClient
from ai_utilities.config_models import AiSettings


class TestEnvironmentDetection:
    """Test environment detection utilities."""

    @patch.dict(os.environ, {"CI": "true"})
    def test_detects_ci_environment(self):
        """Test that CI environments are detected correctly."""
        assert is_ci_environment() is True
        assert is_interactive_environment() is False
        assert get_environment_type() == "CI/CD"
        assert should_prompt_for_reconfigure() is False

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_detects_github_actions(self):
        """Test that GitHub Actions is detected as CI."""
        assert is_ci_environment() is True
        assert is_interactive_environment() is False
        assert get_environment_type() == "CI/CD"

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_file.py::test_function"})
    def test_detects_pytest_environment(self):
        """Test that pytest environment is detected as non-interactive."""
        assert is_interactive_environment() is False
        assert should_prompt_for_reconfigure() is False

    @patch('sys.stdin')
    def test_detects_non_tty_stdin(self, mock_stdin):
        """Test that non-TTY stdin is detected as non-interactive."""
        mock_stdin.isatty.return_value = False
        
        assert is_interactive_environment() is False

    @patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"})
    @patch('sys.stdin')
    def test_detects_development_environment(self, mock_stdin):
        """Test that development environments are detected."""
        mock_stdin.isatty.return_value = True
        
        assert is_development_environment() is True
        assert is_interactive_environment() is True
        assert get_environment_type() == "Development"

    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.stdin')
    def test_detects_interactive_environment(self, mock_stdin):
        """Test that interactive environments are detected."""
        mock_stdin.isatty.return_value = True
        
        assert is_interactive_environment() is True
        assert should_prompt_for_reconfigure() is True
        assert get_environment_type() == "Interactive"

    def test_safe_input_in_non_interactive(self):
        """Test that safe_input returns default in non-interactive environments."""
        with patch('ai_utilities.env_detection.is_interactive_environment', return_value=False):
            result = safe_input("Enter value: ", default="default_value")
            assert result == "default_value"

    def test_safe_input_with_exception(self):
        """Test that safe_input handles exceptions gracefully."""
        with patch('ai_utilities.env_detection.is_interactive_environment', return_value=True):
            with patch('builtins.input', side_effect=EOFError):
                result = safe_input("Enter value: ", default="default_value")
                assert result == "default_value"


class TestSafeClientInitialization:
    """Test that AiClient doesn't block in non-interactive environments."""

    @patch.dict(os.environ, {"CI": "true", "AI_API_KEY": "test-key"})
    def test_client_in_ci_with_api_key(self):
        """Test that AiClient works in CI when API key exists."""
        # Should not block or prompt
        client = AiClient()
        assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {"CI": "true"})
    def test_client_in_ci_without_api_key(self):
        """Test that AiClient works in CI without API key."""
        # Should not block or prompt
        client = AiClient()
        # Should create minimal settings without blocking
        assert client.settings.api_key is None

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "AI_API_KEY": "test-key"})
    def test_client_in_github_actions(self):
        """Test that AiClient works in GitHub Actions."""
        client = AiClient()
        assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_file.py::test_function"})
    def test_client_in_pytest(self):
        """Test that AiClient works in pytest environment."""
        client = AiClient()
        # Should not block during test collection/execution
        assert client is not None

    @patch.dict(os.environ, {}, clear=True)
    @patch('sys.stdin')
    @patch('builtins.input')
    def test_client_in_interactive_environment(self, mock_input, mock_stdin):
        """Test that AiClient works normally in interactive environments."""
        mock_stdin.isatty.return_value = True
        mock_input.return_value = "n"  # Don't reconfigure
        
        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            client = AiClient()
            assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {}, clear=True)
    @patch('ai_utilities.env_detection.is_interactive_environment', return_value=False)
    def test_client_with_auto_setup_disabled(self, mock_interactive):
        """Test that auto_setup=False works correctly."""
        client = AiClient(auto_setup=False)
        assert client is not None
        # Should not attempt any setup

    @patch.dict(os.environ, {}, clear=True)
    @patch('ai_utilities.env_detection.is_interactive_environment', return_value=False)
    def test_client_with_explicit_settings(self, mock_interactive):
        """Test that explicit settings work regardless of environment."""
        settings = AiSettings(api_key="explicit-key")
        client = AiClient(settings=settings)
        assert client.settings.api_key == "explicit-key"


class TestInteractiveSetupSafety:
    """Test that interactive_setup is safe in non-interactive environments."""

    @patch.dict(os.environ, {"CI": "true", "AI_API_KEY": "test-key"})
    def test_interactive_setup_in_ci(self):
        """Test that interactive_setup doesn't prompt in CI."""
        settings = AiSettings.interactive_setup()
        assert settings.api_key == "test-key"

    @patch.dict(os.environ, {"CI": "true"})
    @patch('ai_utilities.config_models.Path')
    def test_interactive_setup_in_ci_no_key(self, mock_path):
        """Test that interactive_setup handles CI without API key."""
        mock_path.return_value.exists.return_value = False
        
        settings = AiSettings.interactive_setup()
        assert settings.api_key is None  # Should create minimal settings

    @patch.dict(os.environ, {"CI": "true"})
    @patch('ai_utilities.env_detection.Path')
    def test_interactive_setup_in_ci_with_env_file(self, mock_path):
        """Test that interactive_setup uses .env in CI."""
        mock_path.return_value.exists.return_value = True
        
        with patch.object(AiSettings, 'from_dotenv') as mock_from_dotenv:
            mock_settings = AiSettings(api_key="env-file-key")
            mock_from_dotenv.return_value = mock_settings
            
            settings = AiSettings.interactive_setup()
            assert settings.api_key == "env-file-key"
            mock_from_dotenv.assert_called_once_with(".env")

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_file.py::test_function"})
    def test_interactive_setup_in_pytest(self):
        """Test that interactive_setup doesn't prompt in pytest."""
        settings = AiSettings.interactive_setup()
        assert settings is not None  # Should not block

    @patch('ai_utilities.env_detection.should_prompt_for_reconfigure', return_value=False)
    @patch.dict(os.environ, {"AI_API_KEY": "test-key"})
    def test_interactive_setup_no_prompt_when_unsafe(self, mock_should_prompt):
        """Test that interactive_setup skips prompting when unsafe."""
        settings = AiSettings.interactive_setup()
        assert settings.api_key == "test-key"
        mock_should_prompt.assert_called_once()

    @patch('ai_utilities.env_detection.should_prompt_for_reconfigure', return_value=True)
    @patch('builtins.input')
    @patch.dict(os.environ, {"AI_API_KEY": "test-key"})
    def test_interactive_setup_prompts_when_safe(self, mock_input, mock_should_prompt):
        """Test that interactive_setup prompts when safe."""
        mock_input.return_value = "n"  # Don't reconfigure
        
        settings = AiSettings.interactive_setup()
        assert settings.api_key == "test-key"
        mock_should_prompt.assert_called_once()
        mock_input.assert_called_once()

    @patch('ai_utilities.env_detection.should_prompt_for_reconfigure', return_value=True)
    @patch('builtins.input', side_effect=EOFError)
    @patch.dict(os.environ, {"AI_API_KEY": "test-key"})
    def test_interactive_setup_handles_eof_error(self, mock_input, mock_should_prompt):
        """Test that interactive_setup handles EOFError gracefully."""
        settings = AiSettings.interactive_setup()
        assert settings.api_key == "test-key"
        mock_should_prompt.assert_called_once()


class TestRealWorldScenarios:
    """Test real-world scenarios where blocking would be problematic."""

    def test_docker_container_scenario(self):
        """Test behavior in Docker container."""
        with patch.dict(os.environ, {"DOCKER_CONTAINER": "true"}):
            assert is_interactive_environment() is False
            
            # Should not block
            client = AiClient()
            assert client is not None

    def test_systemd_service_scenario(self):
        """Test behavior in systemd service."""
        with patch.dict(os.environ, {"INVOCATION_ID": "service-id"}):
            assert is_interactive_environment() is False
            
            # Should not block
            client = AiClient()
            assert client is not None

    def test_cron_job_scenario(self):
        """Test behavior in cron job."""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False
            assert is_interactive_environment() is False
            
            # Should not block
            client = AiClient()
            assert client is not None

    def test_server_process_scenario(self):
        """Test behavior in server process."""
        with patch.dict(os.environ, {"DAEMON_PROCESS": "true"}):
            assert is_interactive_environment() is False
            
            # Should not block
            client = AiClient()
            assert client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
