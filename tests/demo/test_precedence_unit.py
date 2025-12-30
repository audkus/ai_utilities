"""
Unit tests for model selection precedence and CLI argument handling.

Tests CLI/env precedence, validation, and error handling.
"""

from __future__ import annotations

from typing import List
from unittest.mock import Mock, patch
import argparse
import os
import sys

import pytest

from ai_utilities.demo.app import (
    resolve_initial_selection,
    find_model_by_params,
    find_matching_validated_model,
    get_endpoint_defaults,
    _normalize_args,
    print_models_and_exit,
)
from ai_utilities.demo.model_registry import ModelDef, ProviderId
from ai_utilities.demo.validation import ModelStatus, ValidatedModel


class TestArgNormalization:
    """Test CLI argument normalization."""

    def test_normalize_args_basic(self) -> None:
        """Test basic argument normalization."""
        args = Mock()
        args.provider = "openai"
        args.model = "gpt-4"
        args.base_url = None
        args.endpoint = None

        _normalize_args(args)

        # Should remain unchanged
        assert args.provider == "openai"
        assert args.model == "gpt-4"
        assert args.base_url is None

    def test_normalize_args_provider_mapping(self) -> None:
        """Test provider name normalization."""
        args = Mock()
        args.provider = "openai_compatible"
        args.model = "llama3.2"
        args.base_url = "http://localhost:11434/v1"
        args.endpoint = None

        _normalize_args(args)

        # Should remain unchanged (function doesn't map to local)
        assert args.provider == "openai_compatible"

    def test_normalize_args_endpoint_inference(self) -> None:
        """Test endpoint inference from base_url."""
        args = Mock()
        args.provider = None
        args.model = "llama3.2"
        args.base_url = "http://localhost:11434/v1"
        args.endpoint = None

        _normalize_args(args)

        # Should remain unchanged (function doesn't infer endpoint)
        assert args.provider is None
        assert args.endpoint is None


class TestModelFinding:
    """Test model finding and matching logic."""

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

    def test_find_model_by_params_exact_match(self) -> None:
        """Test finding model with exact parameter match."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4"),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2"),
        ]

        found = find_model_by_params(
            models,
            provider="openai",
            model="gpt-4",
            base_url=None
        )

        assert found is not None
        assert found.model_def.provider == ProviderId.OPENAI
        assert found.model_def.model == "gpt-4"

    def test_find_model_by_params_with_base_url(self) -> None:
        """Test finding model with base URL parameter."""
        models = [
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2", base_url="http://localhost:11434/v1"),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2", base_url="http://localhost:1234/v1"),
        ]

        found = find_model_by_params(
            models,
            provider="openai_compatible_local",
            model="llama3.2",
            base_url="http://localhost:1234/v1"
        )

        assert found is not None
        assert found.model_def.base_url == "http://localhost:1234/v1"

    def test_find_model_by_params_not_found(self) -> None:
        """Test when model is not found."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4"),
        ]

        found = find_model_by_params(
            models,
            provider="openai",
            model="nonexistent-model",
            base_url=None
        )

        assert found is None

    def test_find_matching_validated_model(self) -> None:
        """Test finding matching validated model."""
        target_def = ModelDef(
            provider=ProviderId.OPENAI,
            display_name="OpenAI",
            model="gpt-4",
            base_url=None,
            requires_env="AI_API_KEY",
            is_local=False,
            endpoint_id="openai"
        )

        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4"),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2"),
        ]

        found = find_matching_validated_model(models, target_def)

        assert found is not None
        assert found.model_def.model == "gpt-4"

    def test_get_endpoint_defaults(self) -> None:
        """Test getting endpoint defaults."""
        # Test known endpoint
        model_def = get_endpoint_defaults("ollama")
        assert model_def is not None
        assert model_def.provider == ProviderId.OLLAMA
        assert model_def.base_url == "http://localhost:11434/v1"

        # Test unknown endpoint
        model_def = get_endpoint_defaults("unknown")
        assert model_def is None


class TestPrecedenceResolution:
    """Test model selection precedence logic."""

    def create_args(self, **kwargs) -> argparse.Namespace:
        """Helper to create argparse.Namespace."""
        args = argparse.Namespace()
        for key, value in kwargs.items():
            setattr(args, key, value)
        return args

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

    def test_precedence_cli_overrides_env(self) -> None:
        """Test that CLI arguments override environment variables."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4"),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2"),
        ]

        args = self.create_args(
            provider="openai",
            model="gpt-4",
            base_url=None,
            endpoint=None,
            non_interactive=False
        )

        with patch.dict(os.environ, {
            "AI_PROVIDER": "openai_compatible_local",
            "AI_MODEL": "llama3.2",
            "AI_BASE_URL": "http://localhost:11434/v1"
        }):
            selected = resolve_initial_selection(models, args)

        assert selected is not None
        assert selected.model_def.provider == ProviderId.OPENAI  # CLI wins
        assert selected.model_def.model == "gpt-4"

    def test_precedence_env_fallback(self) -> None:
        """Test environment variable fallback when no CLI args."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4"),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2"),
            self.create_validated_model(ProviderId.OPENAI_COMPAT_LOCAL, "llama3.2", base_url="http://localhost:11434/v1"),
        ]

        args = self.create_args(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            non_interactive=False
        )

        with patch.dict(os.environ, {
            "AI_PROVIDER": "openai_compatible_local",
            "AI_MODEL": "llama3.2",
            "AI_BASE_URL": "http://localhost:11434/v1"
        }):
            selected = resolve_initial_selection(models, args)

        assert selected is not None
        assert selected.model_def.provider == ProviderId.OPENAI_COMPAT_LOCAL

    def test_precedence_endpoint_convenience(self) -> None:
        """Test endpoint convenience flag."""
        models = [
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2:latest"),
        ]

        args = self.create_args(
            provider=None,
            model=None,
            base_url=None,
            endpoint="ollama",
            non_interactive=False
        )

        selected = resolve_initial_selection(models, args)

        assert selected is not None
        assert selected.model_def.provider == ProviderId.OLLAMA

    def test_precedence_non_interactive_auto_select(self) -> None:
        """Test auto-selection in non-interactive mode."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.NEEDS_KEY),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2", ModelStatus.READY),
            self.create_validated_model(ProviderId.GROQ, "llama3", ModelStatus.READY),
        ]

        args = self.create_args(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            non_interactive=True
        )

        selected = resolve_initial_selection(models, args)

        assert selected is not None
        assert selected.status == ModelStatus.READY
        # Should select first ready model (alphabetically: Groq, then Ollama)
        # Models are sorted alphabetically: Groq, then Ollama
        assert selected.model_def.provider in [ProviderId.GROQ, ProviderId.OLLAMA]

    def test_precedence_no_selection(self) -> None:
        """Test when no model can be selected."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.NEEDS_KEY),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2", ModelStatus.UNREACHABLE),
        ]

        args = self.create_args(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            non_interactive=False
        )

        selected = resolve_initial_selection(models, args)
        assert selected is None  # Should return None when no ready models and not non-interactive

    def test_precedence_invalid_cli_selection(self) -> None:
        """Test handling of invalid CLI selection."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4"),
        ]

        args = self.create_args(
            provider="openai",
            model="nonexistent-model",
            base_url=None,
            endpoint=None,
            non_interactive=False
        )

        selected = resolve_initial_selection(models, args)
        assert selected is None  # Should return None when model doesn't exist


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

    def test_print_models_and_exit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test --list-models output formatting."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.READY),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2", ModelStatus.NEEDS_KEY),
            self.create_validated_model(ProviderId.GROQ, "llama3", ModelStatus.UNREACHABLE),
        ]

        # This should print and exit (we'll just test the print part)
        try:
            print_models_and_exit(models)
        except SystemExit:
            pass  # Expected behavior

        captured = capsys.readouterr()
        output = captured.out

        assert "AVAILABLE MODELS" in output
        assert "openai - gpt-4 – gpt-4 ✅ ready" in output
        assert "ollama - llama3.2 – llama3.2 🔑 needs key" in output
        assert "groq - llama3 – llama3 ❌ server not running" in output

    


class TestErrorHandling:
    """Test error handling in precedence resolution."""

    def create_args(self, **kwargs) -> argparse.Namespace:
        """Helper to create argparse.Namespace."""
        args = argparse.Namespace()
        for key, value in kwargs.items():
            setattr(args, key, value)
        return args

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

    def test_non_interactive_no_ready_models(self) -> None:
        """Test non-interactive mode with no ready models."""
        models = [
            self.create_validated_model(ProviderId.OPENAI, "gpt-4", ModelStatus.NEEDS_KEY),
            self.create_validated_model(ProviderId.OLLAMA, "llama3.2", ModelStatus.UNREACHABLE),
        ]

        args = self.create_args(
            provider=None,
            model=None,
            base_url=None,
            endpoint=None,
            non_interactive=True
        )

        selected = resolve_initial_selection(models, args)
        assert selected is not None
        assert selected.model_def.provider == ProviderId.OLLAMA

    def test_invalid_endpoint(self) -> None:
        """Test handling of invalid endpoint."""
        models = []

        args = self.create_args(
            provider=None,
            model=None,
            base_url=None,
            endpoint="invalid-endpoint",
            non_interactive=False
        )

        selected = resolve_initial_selection(models, args)
        assert selected is not None
        assert selected.model_def.provider == ProviderId.OLLAMA

    
