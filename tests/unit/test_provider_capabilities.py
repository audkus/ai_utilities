"""Unit tests for provider_capabilities module."""

import pytest

from ai_utilities.providers.provider_capabilities import ProviderCapabilities


class TestProviderCapabilities:
    """Test cases for ProviderCapabilities dataclass."""

    def test_default_creation(self) -> None:
        """Test creating ProviderCapabilities with defaults."""
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
            max_context_length=8192,
            supported_models={"model-1", "model-2"}
        )
        
        assert caps.supports_text is False
        assert caps.supports_json_mode is True
        assert caps.supports_streaming is True
        assert caps.supports_tools is True
        assert caps.supports_images is True
        assert caps.supports_files_upload is True
        assert caps.supports_files_download is True
        assert caps.supports_temperature is False
        assert caps.supports_max_tokens is False
        assert caps.supports_top_p is True
        assert caps.supports_frequency_penalty is True
        assert caps.supports_presence_penalty is True
        assert caps.max_context_length == 8192
        assert caps.supported_models == {"model-1", "model-2"}

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

    def test_equality(self) -> None:
        """Test ProviderCapabilities equality."""
        caps1 = ProviderCapabilities(supports_streaming=True)
        caps2 = ProviderCapabilities(supports_streaming=True)
        caps3 = ProviderCapabilities(supports_streaming=False)
        
        assert caps1 == caps2
        assert caps1 != caps3

    def test_immutability_of_supported_models(self) -> None:
        """Test that supported_models can be modified after creation."""
        models = {"model-a", "model-b"}
        caps = ProviderCapabilities(supported_models=models)
        
        assert caps.supported_models == {"model-a", "model-b"}
        
        # Modify the original set
        models.add("model-c")
        
        # The capability should reflect the change (dataclass doesn't deep copy)
        assert caps.supported_models == {"model-a", "model-b", "model-c"}

    @pytest.mark.parametrize("field_name", [
        "supports_text", "supports_json_mode", "supports_streaming", "supports_tools", "supports_images",
        "supports_files_upload", "supports_files_download", "supports_temperature", "supports_max_tokens",
        "supports_top_p", "supports_frequency_penalty", "supports_presence_penalty"
    ])
    def test_boolean_fields_accept_bool(self, field_name: str) -> None:
        """Test that all boolean fields accept True/False values."""
        # Test True
        caps_true = ProviderCapabilities(**{field_name: True})
        assert getattr(caps_true, field_name) is True
        
        # Test False
        caps_false = ProviderCapabilities(**{field_name: False})
        assert getattr(caps_false, field_name) is False

    @pytest.mark.parametrize("max_context_length", [1, 1024, 8192, 32000, 128000])
    def test_valid_max_context_lengths(self, max_context_length: int) -> None:
        """Test that valid max_context_length values are accepted."""
        caps = ProviderCapabilities(max_context_length=max_context_length)
        assert caps.max_context_length == max_context_length

    def test_supported_models_with_set(self) -> None:
        """Test supported_models with set of strings."""
        models = {"gpt-4", "gpt-3.5-turbo", "claude-3"}
        caps = ProviderCapabilities(supported_models=models)
        assert caps.supported_models == models
        assert isinstance(caps.supported_models, set)

    def test_supported_models_with_empty_set(self) -> None:
        """Test supported_models with empty set."""
        caps = ProviderCapabilities(supported_models=set())
        assert caps.supported_models == set()
        assert len(caps.supported_models) == 0

    def test_dataclass_repr(self) -> None:
        """Test string representation of ProviderCapabilities."""
        caps = ProviderCapabilities(
            supports_streaming=True,
            max_context_length=4096
        )
        
        repr_str = repr(caps)
        assert "ProviderCapabilities" in repr_str
        assert "supports_streaming=True" in repr_str
        assert "max_context_length=4096" in repr_str

    def test_openai_vs_openai_compatible_differences(self) -> None:
        """Test that OpenAI and OpenAI-compatible have different capabilities."""
        openai_caps = ProviderCapabilities.openai()
        compatible_caps = ProviderCapabilities.openai_compatible()
        
        # These should be different
        assert openai_caps.supports_streaming != compatible_caps.supports_streaming
        assert openai_caps.supports_tools != compatible_caps.supports_tools
        assert openai_caps.supports_images != compatible_caps.supports_images
        assert openai_caps.supports_files_upload != compatible_caps.supports_files_upload
        assert openai_caps.supports_files_download != compatible_caps.supports_files_download
        assert openai_caps.supports_top_p != compatible_caps.supports_top_p
        assert openai_caps.supports_frequency_penalty != compatible_caps.supports_frequency_penalty
        assert openai_caps.supports_presence_penalty != compatible_caps.supports_presence_penalty
        assert openai_caps.max_context_length != compatible_caps.max_context_length
        
        # These should be the same
        assert openai_caps.supports_text == compatible_caps.supports_text
        assert openai_caps.supports_json_mode == compatible_caps.supports_json_mode
        assert openai_caps.supports_temperature == compatible_caps.supports_temperature
        assert openai_caps.supports_max_tokens == compatible_caps.supports_max_tokens

    def test_partial_field_override(self) -> None:
        """Test overriding specific fields while keeping defaults."""
        # Start with OpenAI capabilities
        caps = ProviderCapabilities.openai()
        
        # Override specific fields
        caps.supports_streaming = False
        caps.max_context_length = 2048
        
        # Check that only specified fields changed
        assert caps.supports_streaming is False
        assert caps.max_context_length == 2048
        
        # Other fields should remain as OpenAI defaults
        assert caps.supports_text is True
        assert caps.supports_json_mode is True
        assert caps.supports_tools is True
        assert caps.supports_images is True
