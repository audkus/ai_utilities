"""Unit tests for openai_compatible_provider module."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Union
from unittest.mock import MagicMock, Mock, patch, call
import pytest

from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider
from ai_utilities.providers.provider_capabilities import ProviderCapabilities
from ai_utilities.providers.provider_exceptions import (
    ProviderConfigurationError,
    ProviderCapabilityError,
    MissingOptionalDependencyError
)


class TestOpenAICompatibleProvider:
    """Test cases for OpenAICompatibleProvider."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.base_url = "http://localhost:8080/v1"
        self.api_key = "test-key"
        self.timeout = 30
        self.extra_headers = {"Custom-Header": "test-value"}

    def test_initialization_with_required_params(self) -> None:
        """Test provider initialization with required parameters."""
        provider = OpenAICompatibleProvider(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout
        )
        
        assert provider.base_url == self.base_url
        assert provider.settings.base_url == self.base_url
        assert provider.settings.api_key == self.api_key
        assert provider.settings.timeout == self.timeout
        assert provider.provider_name == "openai_compatible"
        assert isinstance(provider.capabilities, ProviderCapabilities)

    def test_initialization_with_extra_headers(self) -> None:
        """Test provider initialization with extra headers."""
        provider = OpenAICompatibleProvider(
            base_url=self.base_url,
            extra_headers=self.extra_headers
        )
        
        assert provider.extra_headers == self.extra_headers
        assert provider.settings.extra_headers == self.extra_headers

    def test_initialization_with_model(self) -> None:
        """Test provider initialization with model parameter."""
        model = "llama-2-7b"
        provider = OpenAICompatibleProvider(
            base_url=self.base_url,
            model=model
        )
        
        assert provider.settings.model == model

    def test_initialization_without_base_url_raises_error(self) -> None:
        """Test that initialization raises error without base_url."""
        with pytest.raises(ProviderConfigurationError) as exc_info:
            OpenAICompatibleProvider()
        
        assert "base_url is required" in str(exc_info.value)
        assert exc_info.value.provider == "openai_compatible"

    def test_base_url_trailing_slash_removed(self) -> None:
        """Test that trailing slash is removed from base_url."""
        provider = OpenAICompatibleProvider(base_url="http://localhost:8080/v1/")
        assert provider.base_url == "http://localhost:8080/v1"

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_openai_client_initialization(self, mock_openai_class: MagicMock) -> None:
        """Test that OpenAI client is initialized with correct parameters."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            extra_headers=self.extra_headers
        )
        
        mock_openai_class.assert_called_once_with(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            default_headers=self.extra_headers
        )
        assert provider.client == mock_client

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_openai_client_with_dummy_key(self, mock_openai_class: MagicMock) -> None:
        """Test that dummy API key is used when none provided."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        mock_openai_class.assert_called_once_with(
            api_key="dummy-key",
            base_url=self.base_url,
            timeout=30
        )

    def test_provider_name_property(self) -> None:
        """Test provider_name property."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        assert provider.provider_name == "openai_compatible"

    def test_capabilities_property(self) -> None:
        """Test capabilities property returns correct capabilities."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        capabilities = provider.capabilities
        
        assert isinstance(capabilities, ProviderCapabilities)
        assert capabilities.supports_text is True
        assert capabilities.supports_json_mode is True
        assert capabilities.supports_streaming is False
        assert capabilities.supports_tools is False
        assert capabilities.supports_images is False

    def test_capabilities_setter(self) -> None:
        """Test capabilities setter."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        new_capabilities = ProviderCapabilities(supports_streaming=True)
        
        provider.capabilities = new_capabilities
        assert provider.capabilities.supports_streaming is True

    def test_check_capability_supported(self) -> None:
        """Test _check_capability for supported capabilities."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Should not raise for supported capabilities
        provider._check_capability("json_mode")  # Should not raise

    def test_check_capability_unsupported(self) -> None:
        """Test _check_capability for unsupported capabilities."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider._check_capability("streaming")
        
        assert exc_info.value.capability == "streaming"
        assert exc_info.value.provider == "openai_compatible"

    def test_show_warning_once(self) -> None:
        """Test that warnings are shown only once."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with patch('builtins.print') as mock_print:
            # Call warning multiple times
            provider._show_warning_once("test_key", "Test warning message")
            provider._show_warning_once("test_key", "Test warning message")
            
            # Should only print once
            assert mock_print.call_count == 1
            mock_print.assert_called_with("\nTest warning message")
            assert "test_key" in provider._shown_warnings

    def test_show_different_warnings(self) -> None:
        """Test that different warnings are both shown."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with patch('builtins.print') as mock_print:
            provider._show_warning_once("key1", "Warning 1")
            provider._show_warning_once("key2", "Warning 2")
            
            assert mock_print.call_count == 2
            mock_print.assert_has_calls([
                call("\nWarning 1"),
                call("\nWarning 2")
            ])

    def test_filter_parameters_supported(self) -> None:
        """Test _filter_parameters with supported parameters."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        params = provider._filter_parameters(
            temperature=0.5,
            max_tokens=100,
            model="test-model"
        )
        
        expected = {
            "temperature": 0.5,
            "max_tokens": 100,
            "model": "test-model"
        }
        assert params == expected

    def test_filter_parameters_unsupported(self) -> None:
        """Test _filter_parameters with unsupported parameters."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with patch.object(provider, '_show_warning_once') as mock_warning:
            params = provider._filter_parameters(
                temperature=0.5,
                unsupported_param="value",
                another_unsupported="value2"
            )
            
            # Should filter out unsupported params
            assert params == {"temperature": 0.5}
            
            # Should show warnings for unsupported params
            assert mock_warning.call_count == 2
            mock_warning.assert_any_call(
                "unsupported_param_unsupported_param",
                "Parameter 'unsupported_param' ignored: This parameter is not supported by all OpenAI-compatible servers"
            )

    def test_filter_parameters_specific_explanations(self) -> None:
        """Test that specific unsupported parameters get correct explanations."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with patch.object(provider, '_show_warning_once') as mock_warning:
            provider._filter_parameters(provider="should-be-ignored")
            
            mock_warning.assert_called_once_with(
                "unsupported_param_provider",
                "Parameter 'provider' ignored: Provider selection is handled at client level, not API level"
            )

    def test_prepare_request_params_backward_compatibility(self) -> None:
        """Test _prepare_request_params for backward compatibility."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with patch.object(provider, '_filter_parameters') as mock_filter:
            test_params = {"temperature": 0.5, "max_tokens": 100}
            result = provider._prepare_request_params(**test_params)
            
            mock_filter.assert_called_once_with(**test_params)
            assert result == mock_filter.return_value

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_text_format(self, mock_openai_class: MagicMock) -> None:
        """Test ask method with text format."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        result = provider.ask("Test prompt", return_format="text")
        
        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_json_format_success(self, mock_openai_class: MagicMock) -> None:
        """Test ask method with JSON format - successful parsing."""
        json_response = {"key": "value", "number": 42}
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(json_response)
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        result = provider.ask("Test prompt", return_format="json")
        
        assert result == json_response

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_json_format_parse_error(self, mock_openai_class: MagicMock) -> None:
        """Test ask method with JSON format - parsing error fallback."""
        invalid_json = "This is not valid JSON"
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = invalid_json
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        result = provider.ask("Test prompt", return_format="json")
        
        # Should return raw text when JSON parsing fails
        assert result == invalid_json

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_with_custom_parameters(self, mock_openai_class: MagicMock) -> None:
        """Test ask method with custom parameters."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Custom response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        result = provider.ask(
            "Test prompt",
            temperature=0.8,
            max_tokens=200,
            model="custom-model"
        )
        
        # Check that custom parameters were passed through
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.8
        assert call_args.kwargs["max_tokens"] == 200
        assert call_args.kwargs["model"] == "custom-model"

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_json_mode_warning(self, mock_openai_class: MagicMock) -> None:
        """Test that JSON mode warning is shown."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": "response"}'
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with patch.object(provider, '_show_warning_once') as mock_warning:
            provider.ask("Test prompt", return_format="json")
            
            mock_warning.assert_called_once_with(
                "json_mode_warning",
                "JSON mode requested but not guaranteed to be supported by this OpenAI-compatible provider"
            )

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_many(self, mock_openai_class: MagicMock) -> None:
        """Test ask_many method."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = provider.ask_many(prompts)
        
        assert len(results) == 3
        assert all(result == "Response" for result in results)
        assert mock_client.chat.completions.create.call_count == 3

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_error_handling(self, mock_openai_class: MagicMock) -> None:
        """Test error handling in ask method."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(Exception, match="API Error"):
            provider.ask("Test prompt")

    def test_upload_file_not_supported(self) -> None:
        """Test that upload_file raises ProviderCapabilityError."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider.upload_file(Path("test.txt"))
        
        assert exc_info.value.capability == "Files API (upload)"
        assert exc_info.value.provider == "openai_compatible"

    def test_download_file_not_supported(self) -> None:
        """Test that download_file raises ProviderCapabilityError."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider.download_file("file-123")
        
        assert exc_info.value.capability == "Files API (download)"
        assert exc_info.value.provider == "openai_compatible"

    def test_generate_image_not_supported(self) -> None:
        """Test that generate_image raises ProviderCapabilityError."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider.generate_image("A beautiful landscape")
        
        assert exc_info.value.capability == "Image generation"
        assert exc_info.value.provider == "openai_compatible"

    def test_generate_image_with_parameters_not_supported(self) -> None:
        """Test generate_image with parameters raises ProviderCapabilityError."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider.generate_image(
                "Test image",
                size="512x512",
                quality="hd",
                n=2
            )
        
        assert exc_info.value.capability == "Image generation"
        assert exc_info.value.provider == "openai_compatible"

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_with_empty_response_content(self, mock_openai_class: MagicMock) -> None:
        """Test ask method when response content is empty."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        result = provider.ask("Test prompt")
        
        assert result == ""

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_ask_with_empty_response_content_json(self, mock_openai_class: MagicMock) -> None:
        """Test ask method with JSON format when response content is empty."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        result = provider.ask("Test prompt", return_format="json")
        
        assert result == ""

    def test_inheritance_from_base_provider(self) -> None:
        """Test that OpenAICompatibleProvider inherits from BaseProvider."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        from ai_utilities.providers.base_provider import BaseProvider
        assert isinstance(provider, BaseProvider)

    def test_logging_configuration(self) -> None:
        """Test that provider is properly configured for logging."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        logger = logging.getLogger("ai_utilities.providers.openai_compatible_provider")
        assert logger is not None

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_default_model_usage(self, mock_openai_class: MagicMock) -> None:
        """Test that default model is used when none specified."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Default model response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        provider.ask("Test prompt")
        
        # Should use default model
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-3.5-turbo"

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_response_format_for_json(self, mock_openai_class: MagicMock) -> None:
        """Test that response_format is included for JSON requests."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": "json"}'
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        provider.ask("Test prompt", return_format="json")
        
        # Should include response_format for JSON
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["response_format"] == {"type": "json_object"}

    @patch('ai_utilities.providers.openai_compatible_provider.OpenAI')
    def test_no_response_format_for_text(self, mock_openai_class: MagicMock) -> None:
        """Test that response_format is not included for text requests."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Text response"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        provider.ask("Test prompt", return_format="text")
        
        # Should not include response_format for text
        call_args = mock_client.chat.completions.create.call_args
        assert "response_format" not in call_args.kwargs
