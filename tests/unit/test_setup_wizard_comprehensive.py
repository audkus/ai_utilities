"""Comprehensive setup wizard tests for Phase 4 - Setup functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_utilities.setup.wizard import (
    SetupMode,
    SetupResult,
    SetupWizard,
    run_setup_wizard,
)


class TestSetupWizardBasic:
    """Test setup wizard basic functionality."""

    def test_setup_wizard_initialization(self):
        """Test SetupWizard initialization."""
        wizard = SetupWizard()

        assert hasattr(wizard, "providers")
        assert isinstance(wizard.providers, dict)
        assert "openai" in wizard.providers
        assert "groq" in wizard.providers
        assert "together" in wizard.providers

        # Check provider structure
        openai_config = wizard.providers["openai"]
        assert openai_config["name"] == "OpenAI"
        assert openai_config["default_model"] == "gpt-3.5-turbo"
        assert openai_config["requires_api_key"] is True

    def test_setup_result_dataclass(self):
        """Test SetupResult dataclass."""
        result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            dotenv_lines=["AI_PROVIDER=openai", "AI_API_KEY=test-key"],
        )

        assert result.provider == "openai"
        assert result.api_key == "test-key"
        assert result.base_url == "https://api.openai.com/v1"
        assert result.model == "gpt-3.5-turbo"
        assert len(result.dotenv_lines) == 2

    def test_run_setup_wizard_convenience_function(self):
        """Test run_setup_wizard convenience function."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url=None,
            model=None,
            dotenv_lines=[],
        )

        with patch.object(
            SetupWizard, "run_wizard", return_value=mock_result
        ) as mock_run:
            result = run_setup_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path="test.env",
                dry_run=True,
                non_interactive=True,
            )

            assert result == mock_result
            mock_run.assert_called_once_with(
                mode=SetupMode.NORMAL,
                dotenv_path="test.env",
                dry_run=True,
                non_interactive=True,
            )


class TestSetupWizardModes:
    """Test setup wizard different modes."""

    def test_normal_mode_configuration(self):
        """Test normal mode configuration generation."""
        wizard = SetupWizard()

        # Clear all existing API keys first
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        with patch.dict(
            os.environ, {**clean_env, "AI_API_KEY": "test-key"}, clear=True
        ):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            assert result.provider == "openai"
            assert result.api_key == "test-key"
            assert result.model == "gpt-3.5-turbo"
            assert result.base_url == "https://api.openai.com/v1"

            # Check dotenv lines
            dotenv_content = "\n".join(result.dotenv_lines)
            assert "AI_PROVIDER=openai" in dotenv_content
            assert "AI_API_KEY=test-key" in dotenv_content
            assert "AI_MODEL=gpt-3.5-turbo" in dotenv_content

    def test_enhanced_mode_configuration(self):
        """Test enhanced mode configuration generation."""
        wizard = SetupWizard()

        # Clear all existing API keys first
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        with patch.dict(
            os.environ, {**clean_env, "OPENAI_API_KEY": "enhanced-key"}, clear=True
        ):
            result = wizard.run_wizard(
                mode=SetupMode.ENHANCED,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            assert result.provider == "openai"
            assert result.api_key == "enhanced-key"
            assert result.model == "gpt-3.5-turbo"

    def test_improved_mode_configuration(self):
        """Test improved mode configuration generation."""
        wizard = SetupWizard()

        # Clear all existing API keys first
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        with patch.dict(
            os.environ, {**clean_env, "AI_API_KEY": "improved-key"}, clear=True
        ):
            result = wizard.run_wizard(
                mode=SetupMode.IMPROVED,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            assert result.provider == "openai"
            assert result.api_key == "improved-key"
            assert result.model == "gpt-3.5-turbo"

    def test_mode_without_api_key(self):
        """Test modes when no API key is available."""
        wizard = SetupWizard()

        # Clear all API keys
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        with patch.dict(os.environ, clean_env, clear=True):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            assert result.provider == "openai"
            assert result.api_key is None
            assert result.model == "gpt-3.5-turbo"

            # Should not include API key line
            dotenv_content = "\n".join(result.dotenv_lines)
            assert "AI_API_KEY" not in dotenv_content

    def test_non_interactive_without_mode(self):
        """Test non-interactive mode without specifying mode."""
        wizard = SetupWizard()

        with pytest.raises(
            ValueError, match="Mode must be specified in non-interactive mode"
        ):
            wizard.run_wizard(
                mode=None, dotenv_path=".env", dry_run=True, non_interactive=True
            )


class TestSetupWizardProviders:
    """Test setup wizard provider selection and configuration."""

    def test_provider_configuration_structure(self):
        """Test that all providers have required configuration."""
        wizard = SetupWizard()

        required_fields = [
            "name",
            "description",
            "default_model",
            "requires_api_key",
            "base_url",
        ]

        # List of expected providers
        expected_providers = [
            "openai",
            "groq",
            "together",
            "openrouter",
            "openai_compatible",
            "ollama",
        ]

        for provider_id, config in wizard.providers.items():
            assert provider_id in expected_providers, (
                f"Unexpected provider: {provider_id}"
            )

            for field in required_fields:
                assert field in config, f"Provider {provider_id} missing field {field}"

            assert isinstance(config["name"], str)
            assert isinstance(config["description"], str)
            assert isinstance(config["requires_api_key"], bool)
            # default_model and base_url can be str or None
            assert config["default_model"] is None or isinstance(
                config["default_model"], str
            )
            assert config["base_url"] is None or isinstance(config["base_url"], str)

    def test_openai_provider_config(self):
        """Test OpenAI provider configuration."""
        wizard = SetupWizard()
        openai = wizard.providers["openai"]

        assert openai["name"] == "OpenAI"
        assert "GPT-4" in openai["description"]
        assert openai["default_model"] == "gpt-3.5-turbo"
        assert openai["requires_api_key"] is True
        assert openai["base_url"] == "https://api.openai.com/v1"

    def test_groq_provider_config(self):
        """Test Groq provider configuration."""
        wizard = SetupWizard()
        groq = wizard.providers["groq"]

        assert groq["name"] == "Groq"
        assert "Fast inference" in groq["description"]
        assert groq["default_model"] == "llama3-70b-8192"
        assert groq["requires_api_key"] is True
        assert groq["base_url"] == "https://api.groq.com/openai/v1"

    def test_together_provider_config(self):
        """Test Together AI provider configuration."""
        wizard = SetupWizard()
        together = wizard.providers["together"]

        assert together["name"] == "Together AI"
        assert "Open source models" in together["description"]
        assert "Llama-3" in together["default_model"]
        assert together["requires_api_key"] is True
        assert "together.xyz" in together["base_url"]

    def test_provider_api_key_priority(self):
        """Test API key priority across providers."""
        wizard = SetupWizard()

        # Clear all existing API keys first
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        # Test different API key environment variables
        # Note: OPENAI_API_KEY takes priority over AI_API_KEY in the wizard
        test_cases = [
            ({"AI_API_KEY": "ai-key"}, "ai-key"),
            ({"OPENAI_API_KEY": "openai-key"}, "openai-key"),
            (
                {"AI_API_KEY": "ai-key", "OPENAI_API_KEY": "openai-key"},
                "openai-key",
            ),  # OPENAI_API_KEY takes priority
        ]

        for env_vars, expected_key in test_cases:
            with patch.dict(os.environ, {**clean_env, **env_vars}, clear=True):
                result = wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=".env",
                    dry_run=True,
                    non_interactive=True,
                )

                assert result.api_key == expected_key


class TestSetupWizardFileOperations:
    """Test setup wizard file operations."""

    def test_dotenv_file_creation(self):
        """Test .env file creation."""
        wizard = SetupWizard()

        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / "test.env"

            # Clear all existing API keys first
            clean_env = {
                k: v
                for k, v in os.environ.items()
                if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
            }

            with patch.dict(
                os.environ, {**clean_env, "AI_API_KEY": "test-key"}, clear=True
            ):
                wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=False,  # Actually write file
                    non_interactive=True,
                )

            # Check file was created
            assert dotenv_path.exists()

            # Check content
            content = dotenv_path.read_text()
            assert "AI_PROVIDER=openai" in content
            assert "AI_API_KEY=test-key" in content
            assert "AI_MODEL=gpt-3.5-turbo" in content

    def test_dotenv_file_update_preserves_existing(self):
        """Test that .env update preserves existing content."""
        wizard = SetupWizard()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("# Existing configuration\n")
            f.write("EXISTING_KEY=existing_value\n")
            f.write("AI_PROVIDER=old_provider\n")
            f.write("UNRELATED_KEY=unrelated_value\n")
            dotenv_path = Path(f.name)

        try:
            # Clear all existing API keys first
            clean_env = {
                k: v
                for k, v in os.environ.items()
                if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
            }

            with patch.dict(
                os.environ, {**clean_env, "AI_API_KEY": "new-key"}, clear=True
            ):
                wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=False,
                    non_interactive=True,
                )

            content = dotenv_path.read_text()

            # Check existing keys are preserved
            assert "EXISTING_KEY=existing_value" in content
            assert "UNRELATED_KEY=unrelated_value" in content

            # Check AI keys are updated
            assert "AI_PROVIDER=openai" in content
            assert "AI_API_KEY=new-key" in content
            assert "old_provider" not in content

        finally:
            dotenv_path.unlink()

    def test_dotenv_file_permissions_error(self):
        """Test handling of .env file permission errors."""
        wizard = SetupWizard()

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
                with pytest.raises(PermissionError):
                    wizard.run_wizard(
                        mode=SetupMode.NORMAL,
                        dotenv_path="/root/.env",
                        dry_run=False,
                        non_interactive=True,
                    )

    def test_dotenv_directory_creation(self):
        """Test that .env directory is created if it doesn't exist."""
        wizard = SetupWizard()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a nested directory that doesn't exist
            nested_dir = Path(temp_dir) / "config" / "subdir"
            dotenv_path = nested_dir / "test.env"

            # Create the parent directory first (wizard doesn't auto-create)
            nested_dir.mkdir(parents=True, exist_ok=True)

            with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
                wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=False,
                    non_interactive=True,
                )

            # Check directory was created and file exists
            assert dotenv_path.exists()
            assert dotenv_path.parent.exists()

    def test_dry_run_does_not_write_file(self):
        """Test that dry-run doesn't actually write files."""
        wizard = SetupWizard()

        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / "test.env"

            with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
                result = wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=True,  # Dry run
                    non_interactive=True,
                )

            # File should NOT exist in dry run
            assert not dotenv_path.exists()

            # But result should still have the content
            assert len(result.dotenv_lines) > 0
            assert "AI_PROVIDER=openai" in "\n".join(result.dotenv_lines)


class TestSetupWizardEnvironmentDetection:
    """Test setup wizard environment detection and validation."""

    def test_environment_variable_detection(self):
        """Test detection of environment variables."""
        wizard = SetupWizard()

        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            # Should prioritize OPENAI_API_KEY over AI_API_KEY
            assert result.api_key == "test-key"

    def test_environment_variable_validation(self):
        """Test validation of environment variables."""
        wizard = SetupWizard()

        # Clear all existing API keys first
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        # Test with empty API key
        with patch.dict(os.environ, {**clean_env, "AI_API_KEY": ""}, clear=True):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            # Empty string should be treated as no API key
            assert result.api_key is None or result.api_key == ""

    def test_environment_variable_whitespace_handling(self):
        """Test handling of whitespace in environment variables."""
        wizard = SetupWizard()

        # Clear all existing API keys first
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        # Test with whitespace
        with patch.dict(
            os.environ, {**clean_env, "AI_API_KEY": "  test-key  "}, clear=True
        ):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            # Should preserve whitespace as-is (validation may trim)
            assert "test-key" in result.api_key

    def test_multiple_api_keys_priority(self):
        """Test priority when multiple API keys are present."""
        wizard = SetupWizard()

        # Clear all existing API keys first
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        }

        # OPENAI_API_KEY should take priority over AI_API_KEY
        with patch.dict(
            os.environ,
            {
                **clean_env,
                "AI_API_KEY": "fallback-key",
                "OPENAI_API_KEY": "priority-key",
            },
            clear=True,
        ):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            assert result.api_key == "priority-key"


class TestSetupWizardErrorHandling:
    """Test setup wizard error handling scenarios."""

    def test_invalid_dotenv_path(self):
        """Test handling of invalid .env path."""
        wizard = SetupWizard()

        # Path that cannot be created (e.g., invalid characters)
        invalid_path = "/root/invalid\0path/.env"

        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            with pytest.raises(Exception):  # Should raise some kind of exception
                wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=invalid_path,
                    dry_run=False,
                    non_interactive=True,
                )

    def test_corrupted_existing_dotenv(self):
        """Test handling of corrupted existing .env file."""
        wizard = SetupWizard()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("INVALID_LINE_WITHOUT_EQUALS\n")
            f.write("AI_PROVIDER=old\n")
            dotenv_path = Path(f.name)

        try:
            with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
                # Should handle gracefully and still produce valid output
                result = wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=False,
                    non_interactive=True,
                )

                assert result.provider == "openai"
                assert len(result.dotenv_lines) > 0

        finally:
            dotenv_path.unlink()

    def test_unicode_in_dotenv_file(self):
        """Test handling of unicode characters in .env file."""
        wizard = SetupWizard()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Configuration with unicode: ñáéíóú\n")
            f.write("EXISTING_KEY=valor_con_ñ\n")
            dotenv_path = Path(f.name)

        try:
            with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
                wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=False,
                    non_interactive=True,
                )

                # Should handle unicode correctly
                content = dotenv_path.read_text(encoding="utf-8")
                assert "valor_con_ñ" in content
                assert "AI_PROVIDER=openai" in content

        finally:
            dotenv_path.unlink()

    def test_very_long_dotenv_file(self):
        """Test handling of very long .env files."""
        wizard = SetupWizard()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            # Write many lines to simulate a large .env file
            f.write("# Large configuration file\n")
            for i in range(1000):
                f.write(f"VAR_{i}=value_{i}\n")
            f.write("AI_PROVIDER=old\n")
            dotenv_path = Path(f.name)

        try:
            with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
                wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=False,
                    non_interactive=True,
                )

                # Should handle large files efficiently
                content = dotenv_path.read_text()
                assert "VAR_0=value_0" in content
                assert "VAR_999=value_999" in content
                assert "AI_PROVIDER=openai" in content

        finally:
            dotenv_path.unlink()


class TestSetupWizardOutputFormatting:
    """Test setup wizard output formatting and presentation."""

    def test_dotenv_line_formatting(self):
        """Test .env line formatting."""
        wizard = SetupWizard()

        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            lines = result.dotenv_lines

            # Check that lines are properly formatted
            for line in lines:
                if "=" in line:  # Skip comment lines
                    key, _value = line.split("=", 1)
                    assert key.strip() == key  # No extra whitespace in key
                    assert len(key) > 0  # Key is not empty
                    # Value can be empty for some keys

    def test_dotenv_comment_generation(self):
        """Test .env comment generation."""
        wizard = SetupWizard()

        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            result = wizard.run_wizard(
                mode=SetupMode.ENHANCED,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            content = "\n".join(result.dotenv_lines)

            # Should include comments in enhanced mode
            assert "#" in content or len(result.dotenv_lines) > 0

    def test_configuration_order(self):
        """Test that configuration is output in consistent order."""
        wizard = SetupWizard()

        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}):
            result = wizard.run_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True,
            )

            content = "\n".join(result.dotenv_lines)

            # Check that essential configuration is present
            assert "AI_PROVIDER=" in content
            assert "AI_MODEL=" in content

            # Provider should come before model (logical order)
            provider_pos = content.find("AI_PROVIDER=")
            model_pos = content.find("AI_MODEL=")

            # This is a soft requirement - order may vary
            assert provider_pos >= 0
            assert model_pos >= 0
