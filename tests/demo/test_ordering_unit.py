"""
Unit tests for model ordering and menu display logic.

Tests alphabetical sorting, case-insensitivity, and status independence.
"""

from __future__ import annotations

from typing import List

import pytest

from ai_utilities.demo.model_registry import ModelDef, ProviderId
from ai_utilities.demo.validation import ModelStatus, ValidatedModel


class TestModelOrdering:
    """Test model ordering logic."""

    def create_validated_model(
        self,
        display_name: str,
        model: str,
        status: ModelStatus,
        provider: ProviderId = ProviderId.OPENAI
    ) -> ValidatedModel:
        """Helper to create ValidatedModel instances."""
        model_def = ModelDef(
            provider=provider,
            display_name=display_name,
            model=model,
            base_url="http://example.com/v1" if provider != ProviderId.OPENAI else None,
            requires_env="AI_API_KEY" if provider == ProviderId.OPENAI else None,
            is_local=provider != ProviderId.OPENAI,
            endpoint_id="test"
        )
        
        # Create appropriate menu line text based on status
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

    def test_alphabetical_ordering_basic(self) -> None:
        """Test basic alphabetical ordering."""
        models = [
            self.create_validated_model("Zebra", "z", ModelStatus.READY),
            self.create_validated_model("Apple", "a", ModelStatus.NEEDS_KEY),
            self.create_validated_model("Banana", "b", ModelStatus.UNREACHABLE),
        ]

        # Sort by menu_line_text
        sorted_models = sorted(models, key=lambda m: m.menu_line_text.lower())

        assert sorted_models[0].model_def.display_name == "Apple"
        assert sorted_models[1].model_def.display_name == "Banana"
        assert sorted_models[2].model_def.display_name == "Zebra"

    def test_case_insensitive_ordering(self) -> None:
        """Test that ordering is case-insensitive."""
        models = [
            self.create_validated_model("apple", "a", ModelStatus.READY),
            self.create_validated_model("Banana", "b", ModelStatus.READY),
            self.create_validated_model("CHERRY", "c", ModelStatus.READY),
        ]

        sorted_models = sorted(models, key=lambda m: m.menu_line_text.lower())

        # Should be: apple, Banana, CHERRY (alphabetical ignoring case)
        assert sorted_models[0].model_def.display_name == "apple"
        assert sorted_models[1].model_def.display_name == "Banana"
        assert sorted_models[2].model_def.display_name == "CHERRY"

    def test_status_independent_ordering(self) -> None:
        """Test that status does not affect alphabetical ordering."""
        models = [
            self.create_validated_model("Zebra", "z", ModelStatus.READY),      # Ready
            self.create_validated_model("Apple", "a", ModelStatus.ERROR),      # Error
            self.create_validated_model("Banana", "b", ModelStatus.NEEDS_KEY), # Needs key
        ]

        sorted_models = sorted(models, key=lambda m: m.menu_line_text.lower())

        # Should maintain alphabetical order regardless of status
        assert sorted_models[0].model_def.display_name == "Apple"
        assert sorted_models[1].model_def.display_name == "Banana"
        assert sorted_models[2].model_def.display_name == "Zebra"

    def test_menu_line_text_formatting(self) -> None:
        """Test menu line text formatting with different statuses."""
        models = [
            self.create_validated_model("OpenAI", "gpt-4", ModelStatus.READY),
            self.create_validated_model("Groq", "llama3", ModelStatus.NEEDS_KEY),
            self.create_validated_model("Ollama", "llama3.2", ModelStatus.UNREACHABLE),
            self.create_validated_model("Local", "model", ModelStatus.ERROR),
            self.create_validated_model("Test", "model", ModelStatus.INVALID_MODEL),
        ]

        lines = [m.menu_line_text for m in models]

        assert "OpenAI – gpt-4 ✅ ready" in lines[0]
        assert "Groq – llama3 🔑 needs key" in lines[1]
        assert "Ollama – llama3.2 ❌ server not running" in lines[2]
        assert "Local – model ⚠️ error" in lines[3]
        assert "Test – model ❓ invalid model" in lines[4]

    def test_complex_mixed_ordering(self) -> None:
        """Test ordering with complex mixed display names."""
        models = [
            self.create_validated_model("FastChat (local)", "model", ModelStatus.READY),
            self.create_validated_model("groq (cloud)", "model", ModelStatus.READY),
            self.create_validated_model("LM Studio (local)", "model", ModelStatus.READY),
            self.create_validated_model("OpenAI (cloud)", "model", ModelStatus.READY),
            self.create_validated_model("text-generation-webui (local)", "model", ModelStatus.READY),
        ]

        sorted_models = sorted(models, key=lambda m: m.menu_line_text.lower())

        expected_order = [
            "FastChat (local)",
            "groq (cloud)", 
            "LM Studio (local)",
            "OpenAI (cloud)",
            "text-generation-webui (local)"
        ]

        actual_order = [m.model_def.display_name for m in sorted_models]
        assert actual_order == expected_order

    def test_ordering_with_provider_types(self) -> None:
        """Test ordering when mixed with different provider types."""
        models = [
            self.create_validated_model("Zebra Local", "z", ModelStatus.READY, ProviderId.OLLAMA),
            self.create_validated_model("Apple Cloud", "a", ModelStatus.READY, ProviderId.OPENAI),
            self.create_validated_model("Banana Local", "b", ModelStatus.READY, ProviderId.OPENAI_COMPAT_LOCAL),
        ]

        sorted_models = sorted(models, key=lambda m: m.menu_line_text.lower())

        assert sorted_models[0].model_def.display_name == "Apple Cloud"
        assert sorted_models[1].model_def.display_name == "Banana Local"
        assert sorted_models[2].model_def.display_name == "Zebra Local"

    def test_ordering_stability(self) -> None:
        """Test that ordering is stable (same input produces same output)."""
        models = [
            self.create_validated_model("Apple", "a", ModelStatus.READY),
            self.create_validated_model("Banana", "b", ModelStatus.READY),
            self.create_validated_model("Cherry", "c", ModelStatus.READY),
        ]

        # Sort twice
        sorted1 = sorted(models, key=lambda m: m.menu_line_text.lower())
        sorted2 = sorted(models, key=lambda m: m.menu_line_text.lower())

        assert [m.model_def.display_name for m in sorted1] == \
               [m.model_def.display_name for m in sorted2]

    def test_ordering_with_duplicate_names(self) -> None:
        """Test ordering when display names are duplicates."""
        models = [
            self.create_validated_model("Test", "model1", ModelStatus.READY),
            self.create_validated_model("Test", "model2", ModelStatus.NEEDS_KEY),
        ]

        sorted_models = sorted(models, key=lambda m: m.menu_line_text.lower())

        # Both should be present, order may vary but should be consistent
        assert len(sorted_models) == 2
        assert all(m.model_def.display_name == "Test" for m in sorted_models)

    def test_ordering_with_special_characters(self) -> None:
        """Test ordering with special characters in display names."""
        models = [
            self.create_validated_model("Model-123", "a", ModelStatus.READY),
            self.create_validated_model("Model_456", "b", ModelStatus.READY),
            self.create_validated_model("Model 789", "c", ModelStatus.READY),
        ]

        sorted_models = sorted(models, key=lambda m: m.menu_line_text.lower())

        # Should handle special characters correctly
        names = [m.model_def.display_name for m in sorted_models]
        assert names[0] == "Model 789"
        assert names[1] == "Model-123"
        assert names[2] == "Model_456"
