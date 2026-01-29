"""Comprehensive tests for provider_capabilities.py module.

This module tests the ProviderCapabilities dataclass and ensures all code paths are exercised.
"""

from typing import Optional, Set
import pytest

# Force import to ensure coverage can track the module
import ai_utilities.providers.provider_capabilities
from ai_utilities.providers.provider_capabilities import ProviderCapabilities


class TestProviderCapabilities:
    """Test ProviderCapabilities dataclass comprehensively."""

    def test_default_creation(self) -> None:
        """Test creating ProviderCapabilities with default values."""
        caps = ProviderCapabilities()
        
        # Core capabilities
        assert caps.supports_text is True
        assert caps.supports_json_mode is False
        assert caps.supports_streaming is False
        assert caps.supports_tools is False
        assert caps.supports_images is False
        
        # File operations
        assert caps.supports_files_upload is False
        assert caps.supports_files_download is False
        
        # Model capabilities
        assert caps.supports_temperature is True
        assert caps.supports_max_tokens is True
        assert caps.supports_top_p is False
        assert caps.supports_frequency_penalty is False
        assert caps.supports_presence_penalty is False
        
        # Additional metadata
        assert caps.max_context_length is None
        assert caps.supported_models is None

    def test_custom_creation(self) -> None:
        """Test creating ProviderCapabilities with custom values."""
        supported_models: Set[str] = {"model-1", "model-2"}
        caps = ProviderCapabilities(
            supports_text=False,
            supports_json_mode=True,
            supports_streaming=True,
            supports_tools=True,
            supports_images=True,
            supports_files_upload=True,
            supports_files_download=True,
            supports_temperature=False,
            supports_max_tokens=False,
            supports_top_p=True,
            supports_frequency_penalty=True,
            supports_presence_penalty=True,
            max_context_length=32000,
            supported_models=supported_models
        )
        
        # Core capabilities
        assert caps.supports_text is False
        assert caps.supports_json_mode is True
        assert caps.supports_streaming is True
        assert caps.supports_tools is True
        assert caps.supports_images is True
        
        # File operations
        assert caps.supports_files_upload is True
        assert caps.supports_files_download is True
        
        # Model capabilities
        assert caps.supports_temperature is False
        assert caps.supports_max_tokens is False
        assert caps.supports_top_p is True
        assert caps.supports_frequency_penalty is True
        assert caps.supports_presence_penalty is True
        
        # Additional metadata
        assert caps.max_context_length == 32000
        assert caps.supported_models == supported_models

    def test_openai_capabilities(self) -> None:
        """Test OpenAI provider capabilities."""
        caps = ProviderCapabilities.openai()
        
        # Core capabilities
        assert caps.supports_text is True
        assert caps.supports_json_mode is True
        assert caps.supports_streaming is True
        assert caps.supports_tools is True
        assert caps.supports_images is True
        
        # File operations
        assert caps.supports_files_upload is True
        assert caps.supports_files_download is True
        
        # Model capabilities
        assert caps.supports_temperature is True
        assert caps.supports_max_tokens is True
        assert caps.supports_top_p is True
        assert caps.supports_frequency_penalty is True
        assert caps.supports_presence_penalty is True
        
        # Additional metadata
        assert caps.max_context_length == 128000
        assert caps.supported_models is None

    def test_openai_compatible_capabilities(self) -> None:
        """Test OpenAI-compatible provider capabilities."""
        caps = ProviderCapabilities.openai_compatible()
        
        # Core capabilities
        assert caps.supports_text is True
        assert caps.supports_json_mode is True
        assert caps.supports_streaming is False
        assert caps.supports_tools is False
        assert caps.supports_images is False
        
        # File operations
        assert caps.supports_files_upload is False
        assert caps.supports_files_download is False
        
        # Model capabilities
        assert caps.supports_temperature is True
        assert caps.supports_max_tokens is True
        assert caps.supports_top_p is False
        assert caps.supports_frequency_penalty is False
        assert caps.supports_presence_penalty is False
        
        # Additional metadata
        assert caps.max_context_length == 4096
        assert caps.supported_models is None

    def test_dataclass_properties(self) -> None:
        """Test dataclass properties and methods."""
        caps = ProviderCapabilities(
            supports_text=True,
            max_context_length=4096
        )
        
        # Test that it's a dataclass
        from dataclasses import is_dataclass, fields, asdict
        
        assert is_dataclass(caps)
        
        # Test fields
        field_names = {f.name for f in fields(caps)}
        expected_fields = {
            'supports_text',
            'supports_json_mode',
            'supports_streaming',
            'supports_tools',
            'supports_images',
            'supports_files_upload',
            'supports_files_download',
            'supports_temperature',
            'supports_max_tokens',
            'supports_top_p',
            'supports_frequency_penalty',
            'supports_presence_penalty',
            'max_context_length',
            'supported_models'
        }
        assert field_names == expected_fields
        
        # Test asdict conversion
        caps_dict = asdict(caps)
        assert isinstance(caps_dict, dict)
        assert caps_dict['supports_text'] is True
        assert caps_dict['max_context_length'] == 4096

    def test_equality(self) -> None:
        """Test ProviderCapabilities equality."""
        caps1 = ProviderCapabilities(supports_text=True, max_context_length=4096)
        caps2 = ProviderCapabilities(supports_text=True, max_context_length=4096)
        caps3 = ProviderCapabilities(supports_text=False, max_context_length=4096)
        
        assert caps1 == caps2
        assert caps1 != caps3

    def test_immutability_of_defaults(self) -> None:
        """Test that default values are properly handled."""
        caps1 = ProviderCapabilities()
        caps2 = ProviderCapabilities()
        
        # Both should have the same defaults
        assert caps1.supports_text == caps2.supports_text
        assert caps1.max_context_length == caps2.max_context_length
        assert caps1.supported_models == caps2.supported_models

    def test_supported_models_set(self) -> None:
        """Test supported_models field with set."""
        models: Set[str] = {"gpt-4", "gpt-3.5-turbo", "claude-3"}
        caps = ProviderCapabilities(supported_models=models)
        
        assert isinstance(caps.supported_models, set)
        assert caps.supported_models == models
        assert "gpt-4" in caps.supported_models
        assert "unknown-model" not in caps.supported_models

    def test_supported_models_none(self) -> None:
        """Test supported_models field with None."""
        caps = ProviderCapabilities(supported_models=None)
        
        assert caps.supported_models is None

    def test_max_context_length_values(self) -> None:
        """Test different max_context_length values."""
        test_values = [
            None,
            0,
            1024,
            4096,
            8192,
            32768,
            128000,
            2000000,
        ]
        
        for value in test_values:
            caps = ProviderCapabilities(max_context_length=value)
            assert caps.max_context_length == value

    def test_boolean_combinations(self) -> None:
        """Test various boolean capability combinations."""
        # All capabilities enabled
        full_caps = ProviderCapabilities(
            supports_text=True,
            supports_json_mode=True,
            supports_streaming=True,
            supports_tools=True,
            supports_images=True,
            supports_files_upload=True,
            supports_files_download=True,
            supports_temperature=True,
            supports_max_tokens=True,
            supports_top_p=True,
            supports_frequency_penalty=True,
            supports_presence_penalty=True,
        )
        
        assert all([
            full_caps.supports_text,
            full_caps.supports_json_mode,
            full_caps.supports_streaming,
            full_caps.supports_tools,
            full_caps.supports_images,
            full_caps.supports_files_upload,
            full_caps.supports_files_download,
            full_caps.supports_temperature,
            full_caps.supports_max_tokens,
            full_caps.supports_top_p,
            full_caps.supports_frequency_penalty,
            full_caps.supports_presence_penalty,
        ])
        
        # Minimal capabilities
        minimal_caps = ProviderCapabilities(
            supports_text=True,
            supports_json_mode=False,
            supports_streaming=False,
            supports_tools=False,
            supports_images=False,
            supports_files_upload=False,
            supports_files_download=False,
            supports_temperature=True,
            supports_max_tokens=True,
            supports_top_p=False,
            supports_frequency_penalty=False,
            supports_presence_penalty=False,
        )
        
        assert minimal_caps.supports_text is True
        assert minimal_caps.supports_temperature is True
        assert minimal_caps.supports_max_tokens is True
        assert minimal_caps.supports_json_mode is False
        assert minimal_caps.supports_streaming is False

    def test_class_method_independence(self) -> None:
        """Test that class methods return independent instances."""
        openai_caps1 = ProviderCapabilities.openai()
        openai_caps2 = ProviderCapabilities.openai()
        compatible_caps = ProviderCapabilities.openai_compatible()
        
        # Should be equal but not the same instance
        assert openai_caps1 == openai_caps2
        assert openai_caps1 is not openai_caps2
        assert openai_caps1 != compatible_caps

    def test_capability_invariants(self) -> None:
        """Test important invariants about provider capabilities."""
        openai_caps = ProviderCapabilities.openai()
        compatible_caps = ProviderCapabilities.openai_compatible()
        
        # OpenAI should be more capable than compatible
        assert openai_caps.supports_streaming >= compatible_caps.supports_streaming
        assert openai_caps.supports_tools >= compatible_caps.supports_tools
        assert openai_caps.supports_images >= compatible_caps.supports_images
        assert openai_caps.supports_files_upload >= compatible_caps.supports_files_upload
        assert openai_caps.supports_files_download >= compatible_caps.supports_files_download
        assert openai_caps.max_context_length >= compatible_caps.max_context_length
        
        # Both should support text
        assert openai_caps.supports_text is True
        assert compatible_caps.supports_text is True
        
        # Both should support basic parameters
        assert openai_caps.supports_temperature is True
        assert compatible_caps.supports_temperature is True
        assert openai_caps.supports_max_tokens is True
        assert compatible_caps.supports_max_tokens is True
