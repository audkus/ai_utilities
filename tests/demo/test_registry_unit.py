"""
Unit tests for model registry functionality.

Tests model discovery, catalog building, and parsing logic.
All HTTP calls are mocked to ensure deterministic, fast tests.
"""

from __future__ import annotations

from typing import List
from unittest.mock import Mock, patch

import pytest

from ai_utilities.demo.model_registry import (
    ModelDef,
    ProviderId,
    discover_ollama_models,
    discover_openai_compatible_models,
    get_builtin_cloud_models,
    build_catalog,
    MODEL_ID_PLACEHOLDER,
)


class TestOllamaDiscovery:
    """Test Ollama model discovery logic."""

    @patch("ai_utilities.demo.model_registry.requests.get")
    def test_discover_ollama_models_success(self, mock_get: Mock) -> None:
        """Test successful Ollama model discovery."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:latest"},
                {"name": "mistral:latest"},
                {"name": "codellama:latest"}
            ]
        }
        mock_get.return_value = mock_response

        models = discover_ollama_models()

        assert len(models) == 3
        assert all(m.provider == ProviderId.OLLAMA for m in models)
        assert all(m.base_url == "http://localhost:11434/v1" for m in models)
        assert all(m.requires_env is None for m in models)
        assert all(m.is_local for m in models)
        
        # Check model names
        model_names = [m.model for m in models]
        assert "llama3.2:latest" in model_names
        assert "mistral:latest" in model_names
        assert "codellama:latest" in model_names

    @patch("ai_utilities.demo.model_registry.requests.get")
    def test_discover_ollama_models_empty(self, mock_get: Mock) -> None:
        """Test Ollama discovery with empty models list - returns fallback."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        models = discover_ollama_models()

        # Should return one fallback model when no models found
        assert len(models) == 1
        assert models[0].provider == ProviderId.OLLAMA
        assert models[0].model == MODEL_ID_PLACEHOLDER
        assert models[0].display_name == "Ollama (local)"

    @patch("ai_utilities.demo.model_registry.requests.get")
    def test_discover_ollama_models_unreachable(self, mock_get: Mock) -> None:
        """Test Ollama discovery when server is unreachable."""
        mock_get.side_effect = Exception("Connection refused")

        models = discover_ollama_models()

        assert models == []  # Returns empty list when unreachable


class TestOpenAICompatibleDiscovery:
    """Test OpenAI-compatible model discovery logic."""

    @patch("ai_utilities.demo.model_registry.requests.get")
    def test_discover_openai_compatible_models_success(self, mock_get: Mock) -> None:
        """Test successful OpenAI-compatible model discovery."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "Qwen2.5-7B"},
                {"id": "Llama-3-8B"},
                {"id": "Mistral-7B"}
            ]
        }
        mock_get.return_value = mock_response

        models = discover_openai_compatible_models(
            "LM Studio",
            "http://localhost:1234/v1"
        )

        assert len(models) == 3
        assert all(m.provider == ProviderId.OPENAI_COMPAT_LOCAL for m in models)
        assert all(m.base_url == "http://localhost:1234/v1" for m in models)
        assert all(m.requires_env is None for m in models)
        assert all(m.is_local for m in models)
        
        # Check display names and model names
        assert "LM Studio" in models[0].display_name
        assert models[0].model == "Qwen2.5-7B"

    @patch("ai_utilities.demo.model_registry.requests.get")
    def test_discover_openai_compatible_models_404(self, mock_get: Mock) -> None:
        """Test OpenAI-compatible discovery when /models returns 404."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        models = discover_openai_compatible_models(
            "LM Studio",
            "http://localhost:1234/v1"
        )

        assert len(models) == 1
        model = models[0]
        assert model.provider == ProviderId.OPENAI_COMPAT_LOCAL
        assert model.display_name == "LM Studio (local)"
        assert model.model == MODEL_ID_PLACEHOLDER
        assert model.base_url == "http://localhost:1234/v1"

    @patch("ai_utilities.demo.model_registry.requests.get")
    def test_discover_openai_compatible_models_error(self, mock_get: Mock) -> None:
        """Test OpenAI-compatible discovery when server errors."""
        mock_get.side_effect = Exception("Connection error")

        models = discover_openai_compatible_models(
            "LM Studio",
            "http://localhost:1234/v1"
        )

        assert models == []


class TestBuiltinCloudModels:
    """Test built-in cloud models catalog."""

    def test_get_builtin_cloud_models(self) -> None:
        """Test that built-in models include expected providers."""
        models = get_builtin_cloud_models()
        
        # Should have at least OpenAI and Groq
        providers = {m.provider for m in models}
        assert ProviderId.OPENAI in providers
        assert ProviderId.GROQ in providers
        
        # Check specific models exist
        openai_models = [m for m in models if m.provider == ProviderId.OPENAI]
        groq_models = [m for m in models if m.provider == ProviderId.GROQ]
        
        assert len(openai_models) > 0
        assert len(groq_models) > 0
        
        # Check cloud models are marked as non-local
        assert all(not m.is_local for m in openai_models)
        assert all(not m.is_local for m in groq_models)


class TestCatalogBuilding:
    """Test catalog building and merging logic."""

    @patch("ai_utilities.demo.model_registry.discover_ollama_models")
    @patch("ai_utilities.demo.model_registry.discover_openai_compatible_models")
    def test_build_catalog_merges_all_sources(
        self, 
        mock_openai_compat: Mock,
        mock_ollama: Mock
    ) -> None:
        """Test that catalog properly merges all model sources."""
        # Mock discovery results
        mock_ollama.return_value = [
            ModelDef(
                provider=ProviderId.OLLAMA,
                display_name="Ollama (local) - llama3.2:latest",
                model="llama3.2:latest",
                base_url="http://localhost:11434/v1",
                requires_env=None,
                is_local=True,
                endpoint_id="ollama"
            )
        ]
        
        mock_openai_compat.return_value = [
            ModelDef(
                provider=ProviderId.OPENAI_COMPAT_LOCAL,
                display_name="LM Studio (local) - Qwen2.5-7B",
                model="Qwen2.5-7B",
                base_url="http://localhost:1234/v1",
                requires_env=None,
                is_local=True,
                endpoint_id="lmstudio"
            )
        ]

        catalog = build_catalog()

        # Should include built-in + discovered models
        assert len(catalog) >= 3  # At least OpenAI, Groq, + discovered
        
        # Check that discovered models are included
        providers = {m.provider for m in catalog}
        assert ProviderId.OLLAMA in providers
        assert ProviderId.OPENAI_COMPAT_LOCAL in providers
        assert ProviderId.OPENAI in providers  # Built-in
        assert ProviderId.GROQ in providers    # Built-in

    @patch("ai_utilities.demo.model_registry.discover_ollama_models")
    @patch("ai_utilities.demo.model_registry.discover_openai_compatible_models")
    def test_build_catalog_handles_empty_discovery(
        self, 
        mock_openai_compat: Mock,
        mock_ollama: Mock
    ) -> None:
        """Test catalog building when discovery returns empty results."""
        mock_ollama.return_value = []
        mock_openai_compat.return_value = []

        catalog = build_catalog()

        # Should still have built-in models
        providers = {m.provider for m in catalog}
        assert ProviderId.OPENAI in providers
        assert ProviderId.GROQ in providers
        assert ProviderId.OLLAMA not in providers
        assert ProviderId.OPENAI_COMPAT_LOCAL not in providers

    def test_build_catalog_deterministic(self) -> None:
        """Test that catalog building is deterministic."""
        catalog1 = build_catalog()
        catalog2 = build_catalog()
        
        assert len(catalog1) == len(catalog2)
        assert catalog1 == catalog2
