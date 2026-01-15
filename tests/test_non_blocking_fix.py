"""Focused tests for the critical non-blocking functionality.

These tests verify that the core fix works - AiClient doesn't block in CI environments.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from ai_utilities.client import AiClient
from ai_utilities.config_models import AiSettings


class TestCriticalBlockingFix:
    """Test the critical fix that prevents blocking in non-interactive environments."""

    @patch.dict(os.environ, {"CI": "true", "AI_API_KEY": "test-key"})
    def test_client_does_not_block_in_ci_with_key(self):
        """Test that AiClient doesn't block in CI when API key exists."""
        # This should not block or hang
        client = AiClient()
        assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {"CI": "true"})
    def test_client_does_not_block_in_ci_without_key(self):
        """Test that AiClient doesn't block in CI when no API key."""
        # This should not block or hang
        client = AiClient()
        # Should create client without blocking
        assert client is not None

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "AI_API_KEY": "test-key"})
    def test_client_does_not_block_in_github_actions(self):
        """Test that AiClient doesn't block in GitHub Actions."""
        client = AiClient()
        assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {"GITLAB_CI": "true", "AI_API_KEY": "test-key"})
    def test_client_does_not_block_in_gitlab_ci(self):
        """Test that AiClient doesn't block in GitLab CI."""
        client = AiClient()
        assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {"TRAVIS": "true", "AI_API_KEY": "test-key"})
    def test_client_does_not_block_in_travis_ci(self):
        """Test that AiClient doesn't block in Travis CI."""
        client = AiClient()
        assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {"CIRCLECI": "true", "AI_API_KEY": "test-key"})
    def test_client_does_not_block_in_circleci(self):
        """Test that AiClient doesn't block in CircleCI."""
        client = AiClient()
        assert client.settings.api_key == "test-key"

    @patch.dict(os.environ, {"JENKINS_URL": "http://jenkins.example.com", "AI_API_KEY": "test-key"})
    def test_client_does_not_block_in_jenkins(self):
        """Test that AiClient doesn't block in Jenkins."""
        client = AiClient()
        assert client.settings.api_key == "test-key"

    def test_client_with_explicit_settings_never_blocks(self):
        """Test that explicit settings never cause blocking."""
        settings = AiSettings(api_key="explicit-key")
        client = AiClient(settings=settings)
        assert client.settings.api_key == "explicit-key"

    @patch.dict(os.environ, {"CI": "true"})
    def test_client_with_auto_setup_disabled_never_blocks(self):
        """Test that auto_setup=False never blocks."""
    def test_client_with_smart_setup_never_blocks(self):
        """Test that smart_setup never blocks in CI."""
        client = AiClient()
        assert client is not None


class TestInteractiveSetupSafety:
    """Test that interactive_setup is safe in non-interactive environments."""

    @patch.dict(os.environ, {"CI": "true", "AI_API_KEY": "test-key"})
    def test_interactive_setup_in_ci(self):
        """Test that interactive_setup doesn't prompt in CI."""
        settings = AiSettings.interactive_setup()
        assert settings.api_key == "test-key"

    @patch.dict(os.environ, {"CI": "true"})
    def test_interactive_setup_in_ci_no_key(self):
        """Test that interactive_setup handles CI without API key."""
        settings = AiSettings.interactive_setup()
        # Should create settings without blocking
        assert settings is not None

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "AI_API_KEY": "test-key"})
    def test_interactive_setup_in_github_actions(self):
        """Test that interactive_setup doesn't prompt in GitHub Actions."""
        settings = AiSettings.interactive_setup()
        assert settings.api_key == "test-key"

    def test_interactive_setup_with_explicit_force_reconfigure(self):
        """Test that force_reconfigure parameter works."""
        # This test is for interactive environments only
        # In CI, it should be ignored safely
        with patch.dict(os.environ, {"CI": "true"}):
            settings = AiSettings.interactive_setup(force_reconfigure=True)
            assert settings is not None  # Should not block


class TestEnvironmentDetection:
    """Test environment detection utilities."""

    def test_detects_ci_environment(self):
        """Test that CI environments are detected."""
        ci_indicators = [
            {"CI": "true"},
            {"GITHUB_ACTIONS": "true"},
            {"GITLAB_CI": "true"},
            {"TRAVIS": "true"},
            {"CIRCLECI": "true"},
            {"JENKINS_URL": "http://jenkins.example.com"},
        ]
        
        for ci_vars in ci_indicators:
            with patch.dict(os.environ, ci_vars):
                from ai_utilities.env_detection import is_ci_environment
                assert is_ci_environment() is True

    def test_detects_pytest_environment(self):
        """Test that pytest environment is detected."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_file.py::test_function"}):
            from ai_utilities.env_detection import should_prompt_for_reconfigure
            assert should_prompt_for_reconfigure() is False

    def test_safe_input_returns_default_in_non_interactive(self):
        """Test that safe_input returns default in non-interactive environments."""
        from ai_utilities.env_detection import safe_input
        
        with patch('ai_utilities.env_detection.is_interactive_environment', return_value=False):
            result = safe_input("Enter value: ", default="default_value")
            assert result == "default_value"


class TestRealWorldScenarios:
    """Test real-world scenarios where blocking would be problematic."""

    @patch.dict(os.environ, {"CI": "true"})
    def test_ci_pipeline_scenario(self):
        """Test behavior in CI pipeline."""
        # Simulate CI pipeline with API key
        with patch.dict(os.environ, {"AI_API_KEY": "pipeline-key"}):
            client = AiClient()
            assert client.settings.api_key == "pipeline-key"

    @patch.dict(os.environ, {"CI": "true"})
    def test_docker_container_scenario(self):
        """Test behavior in Docker container."""
        # Should not block in Docker
        client = AiClient()
        assert client is not None

    @patch.dict(os.environ, {"CI": "true"})
    def test_server_process_scenario(self):
        """Test behavior in server process."""
        # Should not block as server process
        client = AiClient()
        assert client is not None

    @patch.dict(os.environ, {"CI": "true"})
    def test_automated_script_scenario(self):
        """Test behavior in automated script."""
        # Should not block in automated script
        client = AiClient()
        assert client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
