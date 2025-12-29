"""
Unit tests for CLI argument handling and --list-models functionality.

Tests CLI parsing, argument validation, and output formatting.
"""

from __future__ import annotations

from unittest.mock import Mock, patch
import argparse
import os
import sys

import pytest

from ai_utilities.demo.app import run_app, print_models_and_exit
from ai_utilities.demo.model_registry import ModelDef, ProviderId
from ai_utilities.demo.validation import ModelStatus, ValidatedModel


class TestListModelsCLI:
    """Test --list-models CLI functionality."""

    def create_validated_model(
        self,
        provider: ProviderId,
        model: str,
        status: ModelStatus = ModelStatus.READY,
        base_url: str = None
    ) -> ValidatedModel:
        """Helper to create ValidatedModel instances."""
        if base_url is None:
            base_url = "http://localhost:11434/v1" if provider != ProviderId.OPENAI else None

        model_def = ModelDef(
            provider=provider,
            display_name=f"{provider.value} - {model}",
            model=model,
            base_url=base_url,
            requires_env="AI_API_KEY" if provider == ProviderId.OPENAI else None,
            is_local=provider != ProviderId.OPENAI,
            endpoint_id="test"
        )
        
        # Create appropriate menu line text based on status
        display_name = model_def.display_name
        if status == ModelStatus.READY:
            menu_line_text = f"{display_name} – {model} ✅ ready"
        elif status == ModelStatus.NEEDS_KEY:
            menu_line_text = f"{display_name} – {model} 🔑 needs key"
        elif status == ModelStatus.UNREACHABLE:
            menu_line_text = f"{display_name} – {model} ❌ server not running"
        elif status == ModelStatus.INVALID_MODEL:
            menu_line_text = f"{display_name} – {model} ❓ invalid model"
        else:  # ERROR
            menu_line_text = f"{display_name} – {model} ⚠️ error"
        
        return ValidatedModel(
            model_def=model_def,
            status=status,
            status_detail=status.value,
            fix_instructions="" if status == ModelStatus.READY else "Fix this",
            menu_line_text=menu_line_text
        )

    @patch("ai_utilities.demo.app.build_catalog")
    @patch("ai_utilities.demo.app.validate_model")
    def test_list_models_basic_output(self, mock_validate: Mock, mock_catalog: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test basic --list-models output."""
        # Mock catalog and validation
        mock_catalog.return_value = [
            ModelDef(
                provider=ProviderId.OPENAI,
                display_name="OpenAI",
                model="gpt-4",
                base_url=None,
                requires_env="AI_API_KEY",
                is_local=False,
                endpoint_id="openai"
            )
        ]
        mock_validate.return_value = self.create_validated_model(ProviderId.OPENAI, "gpt-4")

        args = argparse.Namespace(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            list_models=True,
            non_interactive=False,
            debug=False
        )

        # Should print and exit
        with pytest.raises(SystemExit):
            run_app(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "AVAILABLE MODELS" in output
        assert "openai - gpt-4 – gpt-4 ✅ ready" in output

    @patch("ai_utilities.demo.app.build_catalog")
    @patch("ai_utilities.demo.app.validate_model")
    def test_list_models_multiple_statuses(self, mock_validate: Mock, mock_catalog: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test --list-models with different model statuses."""
        # Mock different validation results
        def mock_validate_side_effect(model_def, debug=False):
            if model_def.provider == ProviderId.OPENAI:
                return self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.READY)
            elif model_def.provider == ProviderId.GROQ:
                return self.create_validated_model(ProviderId.GROQ, "llama3", ModelStatus.NEEDS_KEY)
            elif model_def.provider == ProviderId.OLLAMA:
                return self.create_validated_model(ProviderId.OLLAMA, "llama3.2", ModelStatus.UNREACHABLE)
            else:
                return self.create_validated_model(model_def.provider, "model", ModelStatus.ERROR)

        mock_catalog.return_value = [
            ModelDef(ProviderId.OPENAI, "OpenAI", "gpt-4", None, "AI_API_KEY", False, "openai"),
            ModelDef(ProviderId.GROQ, "Groq", "llama3", None, "GROQ_API_KEY", False, "groq"),
            ModelDef(ProviderId.OLLAMA, "Ollama", "llama3.2", "http://localhost:11434/v1", None, True, "ollama"),
        ]
        mock_validate.side_effect = mock_validate_side_effect

        args = argparse.Namespace(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            list_models=True,
            non_interactive=False,
            debug=False
        )

        with pytest.raises(SystemExit):
            run_app(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "openai - gpt-4 – gpt-4 ✅ ready" in output
        assert "groq - llama3 – llama3 🔑 needs key" in output
        assert "ollama - llama3.2 – llama3.2 ❌ server not running" in output

    @patch("ai_utilities.demo.app.build_catalog")
    @patch("ai_utilities.demo.app.validate_model")
    def test_list_models_with_fix_instructions(self, mock_validate: Mock, mock_catalog: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test --list-models includes fix instructions for non-ready models."""
        def mock_validate_side_effect(model_def, debug=False):
            if model_def.provider == ProviderId.OPENAI:
                validated = self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.NEEDS_KEY)
                validated.fix_instructions = "Set AI_API_KEY=your-key in .env"
                return validated
            else:
                return self.create_validated_model(model_def.provider, "model", ModelStatus.READY)

        mock_catalog.return_value = [
            ModelDef(ProviderId.OPENAI, "OpenAI", "gpt-4", None, "AI_API_KEY", False, "openai"),
        ]
        mock_validate.side_effect = mock_validate_side_effect

        args = argparse.Namespace(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            list_models=True,
            non_interactive=False,
            debug=False
        )

        with pytest.raises(SystemExit):
            run_app(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "Set AI_API_KEY=your-key in .env" in output

    @patch("ai_utilities.demo.app.build_catalog")
    @patch("ai_utilities.demo.app.validate_model")
    def test_list_models_alphabetical_order(self, mock_validate: Mock, mock_catalog: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that --list-models outputs models in alphabetical order."""
        # Mock catalog in non-alphabetical order
        mock_catalog.return_value = [
            ModelDef(ProviderId.GROQ, "Groq", "llama3", None, "GROQ_API_KEY", False, "groq"),
            ModelDef(ProviderId.OPENAI, "OpenAI", "gpt-4", None, "AI_API_KEY", False, "openai"),
            ModelDef(ProviderId.OLLAMA, "Ollama", "llama3.2", "http://localhost:11434/v1", None, True, "ollama"),
        ]
        
        def mock_validate_side_effect(model_def, debug=False):
            return self.create_validated_model(model_def.provider, model_def.model, ModelStatus.READY)
        
        mock_validate.side_effect = mock_validate_side_effect

        args = argparse.Namespace(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            list_models=True,
            non_interactive=False,
            debug=False
        )

        with pytest.raises(SystemExit):
            run_app(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should be alphabetical: Groq, Ollama, OpenAI
        lines = [line.strip() for line in output.split('\n') if '✅ ready' in line]
        assert len(lines) == 3
        assert "groq" in lines[0]
        assert "ollama" in lines[1] 
        assert "openai" in lines[2]

    @patch("ai_utilities.demo.app.build_catalog")
    @patch("ai_utilities.demo.app.validate_model")
    def test_list_models_empty_catalog(self, mock_validate: Mock, mock_catalog: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test --list-models with empty catalog."""
        mock_catalog.return_value = []
        mock_validate.return_value = None

        args = argparse.Namespace(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            list_models=True,
            non_interactive=False,
            debug=False
        )

        with pytest.raises(SystemExit):
            run_app(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "AVAILABLE MODELS" in output
        # Should not have any model entries
        assert "✅" not in output
        assert "❌" not in output

    @patch("ai_utilities.demo.app.build_catalog")
    @patch("ai_utilities.demo.app.validate_model")
    def test_list_models_with_debug(self, mock_validate: Mock, mock_catalog: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test --list-models with debug flag enabled."""
        mock_catalog.return_value = [
            ModelDef(ProviderId.OPENAI, "OpenAI", "gpt-4", None, "AI_API_KEY", False, "openai"),
        ]
        
        def mock_validate_side_effect(model_def, debug=False):
            # Should receive debug=True
            assert debug is True
            return self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.READY)
        
        mock_validate.side_effect = mock_validate_side_effect

        args = argparse.Namespace(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            list_models=True,
            non_interactive=False,
            debug=True
        )

        with pytest.raises(SystemExit):
            run_app(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "AVAILABLE MODELS" in output
        assert "openai - gpt-4 – gpt-4 ✅ ready" in output

    def test_print_models_and_exit_directly(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test print_models_and_exit function directly."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.READY),
            self.create_validated_model(ProviderId.GROQ, "llama3", ModelStatus.NEEDS_KEY),
        ]

        # Add fix instructions for the non-ready model
        models[1].fix_instructions = "Set GROQ_API_KEY=your-key in .env"

        with pytest.raises(SystemExit):
            print_models_and_exit(models)

        captured = capsys.readouterr()
        output = captured.out

        assert "🤖 AI UTILITIES - AVAILABLE MODELS" in output
        assert "openai - gpt-4 – gpt-4 ✅ ready" in output
        assert "groq - llama3 – llama3 🔑 needs key" in output
        assert "Set GROQ_API_KEY=your-key in .env" in output
        assert "=" * 50 in output

    def test_print_models_and_exit_no_models(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test print_models_and_exit with no models."""
        models = []

        with pytest.raises(SystemExit):
            print_models_and_exit(models)

        captured = capsys.readouterr()
        output = captured.out

        assert "🤖 AI UTILITIES - AVAILABLE MODELS" in output
        assert "No models found" in output or "AVAILABLE MODELS" in output

    def test_print_models_and_exit_error_status(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test print_models_and_exit with error status models."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.ERROR),
        ]
        models[0].fix_instructions = "Check your configuration"

        with pytest.raises(SystemExit):
            print_models_and_exit(models)

        captured = capsys.readouterr()
        output = captured.out

        assert "openai - gpt-4 – gpt-4 ⚠️ error" in output
        assert "Check your configuration" in output
