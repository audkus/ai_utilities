"""Tests for non-blocking behavior in CI/non-interactive environments.

These tests verify that AiClient and AiSettings don't block or prompt in CI.
"""

import os
import pytest
from unittest.mock import patch

from ai_utilities.client import AiClient
from ai_utilities.config_models import AiSettings


class TestAiClientNonBlocking:
    """Test that AiClient doesn't block in CI environments."""

    def test_client_does_not_block_in_ci_with_key(self):
        """Test that AiClient doesn't block in CI when API key exists."""
        with patch.dict(os.environ, {"CI": "true", "AI_API_KEY": "test-key"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                client = AiClient()
                assert client.settings.api_key == "test-key"

    def test_client_does_not_block_in_github_actions(self):
        """Test that AiClient doesn't block in GitHub Actions."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "AI_API_KEY": "test-key"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                client = AiClient()
                assert client.settings.api_key == "test-key"

    def test_client_does_not_block_in_gitlab_ci(self):
        """Test that AiClient doesn't block in GitLab CI."""
        with patch.dict(os.environ, {"GITLAB_CI": "true", "AI_API_KEY": "test-key"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                client = AiClient()
                assert client.settings.api_key == "test-key"

    def test_client_does_not_block_in_travis_ci(self):
        """Test that AiClient doesn't block in Travis CI."""
        with patch.dict(os.environ, {"TRAVIS": "true", "AI_API_KEY": "test-key"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                client = AiClient()
                assert client.settings.api_key == "test-key"

    def test_client_does_not_block_in_circleci(self):
        """Test that AiClient doesn't block in CircleCI."""
        with patch.dict(os.environ, {"CIRCLECI": "true", "AI_API_KEY": "test-key"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                client = AiClient()
                assert client.settings.api_key == "test-key"

    def test_client_does_not_block_in_jenkins(self):
        """Test that AiClient doesn't block in Jenkins."""
        with patch.dict(os.environ, {"JENKINS_URL": "http://jenkins.example.com", "AI_API_KEY": "test-key"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                client = AiClient()
                assert client.settings.api_key == "test-key"

    def test_client_does_not_block_in_ci_without_key(self):
        """Test that AiClient doesn't block in CI when no API key."""
        with patch.dict(os.environ, {"CI": "true"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                # Should raise ProviderConfigurationError without blocking or calling input()
                # New invariant: ProviderConfigurationError is acceptable in CI/non-interactive
                with pytest.raises(Exception) as exc_info:
                    client = AiClient()
                # Should be a configuration error, not an input-related error
                assert "configuration" in str(exc_info.value).lower() or "provider" in str(exc_info.value).lower()
                # input() should not have been called (otherwise AssertionError would be raised)

    def test_client_with_explicit_settings_never_blocks(self):
        """Test that explicit settings never cause blocking."""
        settings = AiSettings(api_key="explicit-key")
        
        with patch('builtins.input', side_effect=AssertionError("input() must not be called")):
            client = AiClient(settings=settings)
            assert client.settings.api_key == "explicit-key"


class TestInteractiveSetupNonBlocking:
    """Test that interactive_setup is safe in non-interactive environments."""

    def test_interactive_setup_in_ci_with_key(self):
        """Test that interactive_setup doesn't prompt in CI when API key exists."""
        with patch.dict(os.environ, {"CI": "true", "AI_API_KEY": "test-key"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                settings = AiSettings.interactive_setup()
                assert settings.api_key == "test-key"

    def test_interactive_setup_in_ci_without_key(self):
        """Test that interactive_setup handles CI without API key."""
        with patch.dict(os.environ, {"CI": "true"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                settings = AiSettings.interactive_setup()
                # Should create settings without blocking
                assert settings is not None

    def test_interactive_setup_with_force_reconfigure_in_ci(self):
        """Test that force_reconfigure is ignored safely in CI."""
        with patch.dict(os.environ, {"CI": "true"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                settings = AiSettings.interactive_setup(force_reconfigure=True)
                assert settings is not None  # Should not block


class TestInputPreventionEnforcement:
    """Test that input() is never called in CI environments."""

    def test_input_call_raises_assertion_in_client(self):
        """Test that calling input() during AiClient init raises AssertionError."""
        with patch.dict(os.environ, {"CI": "true"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                # Should raise ProviderConfigurationError without calling input()
                # New invariant: ProviderConfigurationError is acceptable in CI/non-interactive
                with pytest.raises(Exception) as exc_info:
                    client = AiClient()
                # Should be a configuration error, not an input-related error
                assert "configuration" in str(exc_info.value).lower() or "provider" in str(exc_info.value).lower()
                # input() should not have been called (otherwise AssertionError would be raised)

    def test_input_call_raises_assertion_in_interactive_setup(self):
        """Test that calling input() during interactive_setup raises AssertionError."""
        with patch.dict(os.environ, {"CI": "true"}):
            with patch('builtins.input', side_effect=AssertionError("input() must not be called in CI")):
                # This should pass because input() should not be called
                settings = AiSettings.interactive_setup()
                assert settings is not None
