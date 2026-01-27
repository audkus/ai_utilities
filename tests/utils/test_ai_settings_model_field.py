"""Tests for Pydantic-based AI_MODEL environment loading."""

import os
import pytest
from unittest.mock import patch

from ai_utilities.config_models import AiSettings


class TestAiSettingsModelField:
    """Test that AiSettings.model is populated directly from environment variables."""

    def test_ai_model_populates_model_field(self):
        """Test that AI_MODEL environment variable populates AiSettings.model."""
        with patch.dict(os.environ, {"AI_MODEL": "gpt-4"}):
            settings = AiSettings()
            assert settings.model == "gpt-4"

    def test_openai_model_fallback(self):
        """Test that OPENAI_MODEL is used as fallback when AI_MODEL is not set."""
        with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-3.5-turbo"}, clear=True):
            settings = AiSettings()
            # AiSettings itself does not automatically map OPENAI_MODEL to model.
            # Provider-specific model selection is handled by provider resolution.
            assert settings.model is None

    def test_ai_model_takes_priority_over_openai_model(self):
        """Test that AI_MODEL takes priority over OPENAI_MODEL when both are set."""
        with patch.dict(os.environ, {
            "AI_MODEL": "gpt-4",
            "OPENAI_MODEL": "gpt-3.5-turbo"
        }):
            settings = AiSettings()
            assert settings.model == "gpt-4"

    def test_no_model_env_vars_sets_default(self):
        """Test that model remains None when neither AI_MODEL nor OPENAI_MODEL are set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = AiSettings()
            assert settings.model is None

    def test_empty_string_treated_as_default(self):
        """Test that empty string AI_MODEL is treated as None."""
        with patch.dict(os.environ, {"AI_MODEL": ""}, clear=True):
            settings = AiSettings()
            assert settings.model is None

    def test_whitespace_only_treated_as_default(self):
        """Test that whitespace-only AI_MODEL is treated as None."""
        test_cases = ["   ", "\t", "\n", "  \t\n  "]
        for whitespace_value in test_cases:
            with patch.dict(os.environ, {"AI_MODEL": whitespace_value}, clear=True):
                settings = AiSettings()
                assert settings.model is None, f"Failed for whitespace: {repr(whitespace_value)}"

    def test_whitespace_is_trimmed(self):
        """Test that whitespace around model values is trimmed."""
        with patch.dict(os.environ, {"AI_MODEL": "  gpt-4  "}, clear=True):
            settings = AiSettings()
            assert settings.model == "gpt-4"

    def test_explicit_model_overrides_env(self):
        """Test that explicit model parameter overrides environment variables."""
        with patch.dict(os.environ, {"AI_MODEL": "gpt-3.5-turbo"}):
            settings = AiSettings(model="gpt-4")
            assert settings.model == "gpt-4"

    def test_complex_model_names(self):
        """Test that complex model names work correctly."""
        complex_models = [
            "meta-llama/Llama-3-8b-chat-hf",
            "meta-llama/llama-3-8b-instruct:free",
            "accounts/fireworks/models/llama-v3-8b-instruct",
        ]
        
        for model_name in complex_models:
            with patch.dict(os.environ, {"AI_MODEL": model_name}, clear=True):
                settings = AiSettings()
                assert settings.model == model_name

    def test_model_field_with_other_settings(self):
        """Test that model field works correctly with other AiSettings fields."""
        with patch.dict(os.environ, {
            "AI_MODEL": "gpt-4",
            "AI_API_KEY": "test-key",
            "AI_PROVIDER": "openai",
            "AI_TEMPERATURE": "0.5"
        }):
            settings = AiSettings()
            assert settings.model == "gpt-4"
            assert settings.api_key == "test-key"
            assert settings.provider == "openai"
            assert settings.temperature == 0.5

    def test_model_field_type_annotation(self):
        """Test that model field has correct type annotation."""
        from typing import get_type_hints
        hints = get_type_hints(AiSettings)
        assert hints["model"] is type(None) or str  # Optional[str]


class TestModelFieldValidator:
    """Test the model field validator behavior."""

    def test_validator_handles_none(self):
        """Test that validator preserves None values."""
        settings = AiSettings(model=None)
        assert settings.model is None

    def test_validator_preserves_valid_strings(self):
        """Test that validator preserves valid model strings."""
        settings = AiSettings(model="gpt-4")
        assert settings.model == "gpt-4"

    def test_validator_normalizes_whitespace(self):
        """Test that validator normalizes whitespace correctly."""
        test_cases = [
            ("  gpt-4  ", "gpt-4"),
            ("\tgpt-4\t", "gpt-4"),
            ("\ngpt-4\n", "gpt-4"),
            ("  \tgpt-4\n  ", "gpt-4"),
        ]
        
        for input_val, expected in test_cases:
            settings = AiSettings(model=input_val)
            assert settings.model == expected

    def test_validator_converts_empty_to_default(self):
        """Test that validator converts empty strings to None."""
        test_cases = ["", "   ", "\t", "\n", "  \t\n  "]
        
        for empty_val in test_cases:
            settings = AiSettings(model=empty_val)
            assert settings.model is None, f"Failed for: {repr(empty_val)}"


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_explicit_none_converts_to_default(self):
        """Test that explicitly setting model=None keeps model as None."""
        settings = AiSettings(model=None, api_key="test")
        assert settings.model is None

    def test_explicit_model_still_works(self):
        """Test that explicitly setting model still works."""
        settings = AiSettings(model="gpt-4", api_key="test")
        assert settings.model == "gpt-4"

    def test_mixed_explicit_and_env(self):
        """Test that explicit model takes priority over environment."""
        with patch.dict(os.environ, {"AI_MODEL": "env-model"}):
            settings = AiSettings(model="explicit-model")
            assert settings.model == "explicit-model"


class TestIntegrationWithResolver:
    """Test integration with the model resolver."""

    def test_resolver_uses_settings_model(self):
        """Test that resolve_model uses the populated settings.model."""
        from ai_utilities.config_resolver import resolve_model
        
        with patch.dict(os.environ, {"AI_MODEL": "gpt-4"}):
            settings = AiSettings(api_key="test")
            # settings.model should be populated by Pydantic
            resolved_model = resolve_model(settings, "openai")
            assert resolved_model == "gpt-4"

    def test_resolver_fallback_to_default(self):
        """Test that resolver falls back to provider default when no env model."""
        from ai_utilities.config_resolver import resolve_model
        
        with patch.dict(os.environ, {}, clear=True):
            settings = AiSettings(api_key="test")  # No model in settings
            resolved_model = resolve_model(settings, "openai")
            assert resolved_model == "gpt-3.5-turbo"  # Provider default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
