"""Tests for AiSettings environment variable parsing for model."""

import pytest
from unittest.mock import patch

from ai_utilities.config_models import AiSettings


class TestSettingsEnvModelParsing:
    """Test AiSettings environment variable parsing for model."""

    def test_ai_settings_reads_ai_model_env(self):
        """Test that AiSettings reads AI_MODEL environment variable."""
        with patch.dict('os.environ', {'AI_MODEL': 'gpt-4'}, clear=True):
            settings = AiSettings()
            assert settings.model == 'gpt-4'

    def test_ai_settings_model_whitespace_stripped(self):
        """Test that whitespace is stripped from AI_MODEL environment variable."""
        with patch.dict('os.environ', {'AI_MODEL': '  gpt-4-turbo  '}, clear=True):
            settings = AiSettings()
            assert settings.model == 'gpt-4-turbo'

    def test_ai_settings_empty_model_env(self):
        """Test that empty AI_MODEL environment variable results in None."""
        with patch.dict('os.environ', {'AI_MODEL': ''}, clear=True):
            settings = AiSettings()
            assert settings.model is None

    def test_ai_settings_no_model_env(self):
        """Test that missing AI_MODEL environment variable results in None."""
        with patch.dict('os.environ', {}, clear=True):
            settings = AiSettings()
            assert settings.model is None

    def test_explicit_model_overrides_env(self):
        """Test that explicit model parameter overrides environment variable."""
        with patch.dict('os.environ', {'AI_MODEL': 'gpt-3.5-turbo'}, clear=True):
            settings = AiSettings(model='gpt-4')
            assert settings.model == 'gpt-4'
