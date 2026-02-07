"""Extended tests for openai_compatible_provider to increase coverage."""

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
from ai_utilities.file_models import UploadedFile


class TestOpenAICompatibleProviderExtended:
    """Extended test cases for OpenAICompatibleProvider to cover missing lines."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.base_url = "http://localhost:8080/v1"
        self.api_key = "test-key"
        self.timeout = 30
        self.extra_headers = {"Custom-Header": "test-value"}

    def test_provider_name_property(self) -> None:
        """Test provider_name property."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        assert provider.provider_name == "openai_compatible"

    def test_check_capability_supported(self) -> None:
        """Test _check_capability with supported capabilities using actual contract."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # These should not raise exceptions based on actual capabilities
        provider._check_capability("json_mode")  # supports_json_mode=True
        # text generation is the default and not checked

    def test_check_capability_unsupported(self) -> None:
        """Test _check_capability with unsupported capabilities using actual contract."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider._check_capability("images")  # Use actual capability name
        
        assert "images" in str(exc_info.value)
        # The error message is just the capability name, not a full sentence

    def test_base_url_trailing_slash_removal(self) -> None:
        """Test that trailing slash is removed from base_url."""
        urls_with_slash = [
            "http://localhost:8080/v1/",
            "https://api.example.com/v1/",
            "http://127.0.0.1:11434/v1//"
        ]
        
        for url in urls_with_slash:
            provider = OpenAICompatibleProvider(base_url=url)
            assert provider.base_url == url.rstrip('/')
            assert not provider.base_url.endswith('/')

    def test_initialization_with_model_parameter(self) -> None:
        """Test initialization with model parameter."""
        model = "custom-model"
        provider = OpenAICompatibleProvider(
            base_url=self.base_url,
            model=model
        )
        
        assert provider.settings.model == model

    def test_initialization_warning_tracking(self) -> None:
        """Test that warning tracking is initialized."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        assert hasattr(provider, '_shown_warnings')
        assert isinstance(provider._shown_warnings, set)

    def test_ask_with_streaming(self) -> None:
        """Test ask method with streaming enabled."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock the streaming response
        mock_stream = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "test"
        mock_stream.__iter__.return_value = [mock_chunk]
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_stream):
            response = provider.ask("test prompt", stream=True)
            
            # Should handle streaming response
            assert response is not None

    def test_ask_with_invalid_return_format(self) -> None:
        """Test ask method with invalid return format."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            # Should handle unknown return format gracefully
            response = provider.ask("test", return_format="unknown")
            # Contract: verify error handling returns content (passthrough)
            assert response is not None
            assert isinstance(response, str)  # Verify return type contract

    def test_ask_with_max_tokens_parameter(self) -> None:
        """Test ask method with max_tokens parameter."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            provider.ask("test", max_tokens=1000)
            
            # Should pass max_tokens to the API call
            call_args = mock_create.call_args
            assert 'max_tokens' in call_args[1]

    def test_ask_with_top_p_parameter(self) -> None:
        """Test ask method with top_p parameter."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            provider.ask("test", top_p=0.9)
            
            # Contract: verify that unsupported parameters are filtered out, defaults are applied
            call_args = mock_create.call_args
            # Should have default parameters always present
            assert 'temperature' in call_args[1]
            assert 'max_tokens' in call_args[1]
            assert 'model' in call_args[1]
            # Should NOT have unsupported parameters
            unsupported_params = {'top_p', 'frequency_penalty', 'presence_penalty', 'stop'}
            actual_params = set(call_args[1].keys())
            assert not actual_params.intersection(unsupported_params)

    def test_ask_with_frequency_penalty_parameter(self) -> None:
        """Test ask method with frequency_penalty parameter."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            provider.ask("test", frequency_penalty=0.5)
            
            # Contract: verify that unsupported parameters are filtered out, defaults are applied
            call_args = mock_create.call_args
            # Should have default parameters always present
            assert 'temperature' in call_args[1]
            assert 'max_tokens' in call_args[1]
            assert 'model' in call_args[1]
            # Should NOT have unsupported parameters
            unsupported_params = {'top_p', 'frequency_penalty', 'presence_penalty', 'stop'}
            actual_params = set(call_args[1].keys())
            assert not actual_params.intersection(unsupported_params)

    def test_ask_with_presence_penalty_parameter(self) -> None:
        """Test ask method with presence_penalty parameter."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            provider.ask("test", presence_penalty=0.5)
            
            # Contract: verify that unsupported parameters are filtered out, defaults are applied
            call_args = mock_create.call_args
            # Should have default parameters always present
            assert 'temperature' in call_args[1]
            assert 'max_tokens' in call_args[1]
            assert 'model' in call_args[1]
            # Should NOT have unsupported parameters
            unsupported_params = {'top_p', 'frequency_penalty', 'presence_penalty', 'stop'}
            actual_params = set(call_args[1].keys())
            assert not actual_params.intersection(unsupported_params)

    def test_ask_with_stop_sequences(self) -> None:
        """Test ask method with stop sequences."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            provider.ask("test", stop=["\n", "Human:"])
            
            # Contract: verify that unsupported parameters are filtered out, defaults are applied
            call_args = mock_create.call_args
            # Should have default parameters always present
            assert 'temperature' in call_args[1]
            assert 'max_tokens' in call_args[1]
            assert 'model' in call_args[1]
            # Should NOT have unsupported parameters
            unsupported_params = {'top_p', 'frequency_penalty', 'presence_penalty', 'stop'}
            actual_params = set(call_args[1].keys())
            assert not actual_params.intersection(unsupported_params)

    def test_ask_many_with_parameters(self) -> None:
        """Test ask_many method with various parameters."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            prompts = ["prompt1", "prompt2"]
            responses = provider.ask_many(prompts, temperature=0.5, max_tokens=1000)
            
            assert len(responses) == 2
            # Contract: verify provider was called and returned results (passthrough)
            assert all(r is not None for r in responses)
            assert all(isinstance(r, str) for r in responses)  # Verify return type contract
            
            # Should make multiple calls with parameters
            assert mock_create.call_count == 2
            for call in mock_create.call_args_list:
                assert 'temperature' in call[1]
                assert call[1]['temperature'] == 0.5
                assert 'max_tokens' in call[1]
                assert call[1]['max_tokens'] == 1000

    def test_upload_file_not_implemented(self) -> None:
        """Test upload_file method raises NotImplementedError."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        mock_file = MagicMock(spec=UploadedFile)
        mock_file.filename = "test.txt"
        mock_file.bytes = b"test content"
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider.upload_file(mock_file)
        
        # Contract: verify that capability error is raised for file upload
        assert "Files API (upload)" in str(exc_info.value)
        # Contract: should be a ProviderCapabilityError (no semantic message requirements)

    def test_download_file_not_implemented(self) -> None:
        """Test download_file method raises NotImplementedError."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider.download_file("test-file-id")
        
        # Contract: verify that capability error is raised for file download
        assert "Files API (download)" in str(exc_info.value)
        # Contract: should be a ProviderCapabilityError (no semantic message requirements)

    def test_generate_image_not_implemented(self) -> None:
        """Test generate_image method raises NotImplementedError."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        with pytest.raises(ProviderCapabilityError) as exc_info:
            provider.generate_image("test prompt")
        
        # Contract: verify that capability error is raised for image generation
        assert "Image generation" in str(exc_info.value)
        # Contract: should be a ProviderCapabilityError (no semantic message requirements)

    def test_ask_with_complex_json_response(self) -> None:
        """Test ask method with complex JSON response."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock complex JSON response
        complex_json = {
            "data": {
                "items": [
                    {"id": 1, "name": "item1"},
                    {"id": 2, "name": "item2"}
                ],
                "total": 2
            },
            "status": "success"
        }
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(complex_json)
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            response = provider.ask("test", return_format="json")
            
            assert response == complex_json
            assert response["data"]["total"] == 2
            assert len(response["data"]["items"]) == 2

    def test_ask_with_malformed_json_recovery(self) -> None:
        """Test ask method with malformed JSON that can be recovered."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response with slightly malformed JSON that can be fixed
        malformed_json = '{"key": "value", "incomplete":'  # Missing closing brace and value
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = malformed_json
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            with patch('ai_utilities.providers.openai_compatible_provider.logger') as mock_logger:
                response = provider.ask("test", return_format="json")
                
                # Should log error but return raw text
                mock_logger.error.assert_called()
                assert response == malformed_json

    def test_ask_with_empty_response(self) -> None:
        """Test ask method with empty response."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            response = provider.ask("test")
            # Contract: verify error handling returns content (passthrough)
            assert response is not None
            assert isinstance(response, str)  # Verify return type contract

    def test_ask_with_none_response_content(self) -> None:
        """Test ask method with None response content."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response with None content
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            response = provider.ask("test")
            # Contract: None content is converted to empty string (edge case handling)
            assert isinstance(response, str)  # Contract: returns string type
            assert len(response) == 0  # Contract: empty string for None content

    def test_ask_with_no_choices_in_response(self) -> None:
        """Test ask method with no choices in response."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Mock response with no choices
        mock_response = MagicMock()
        mock_response.choices = []
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(Exception):  # Should raise an error
                provider.ask("test")

    def test_initialization_with_kwargs(self) -> None:
        """Test initialization with additional kwargs."""
        provider = OpenAICompatibleProvider(
            base_url=self.base_url,
            custom_param="value",
            another_param=123
        )
        
        # Should initialize successfully
        assert provider.base_url == self.base_url
        assert provider.provider_name == "openai_compatible"

    def test_capabilities_property(self) -> None:
        """Test capabilities property returns correct capabilities."""
        provider = OpenAICompatibleProvider(base_url=self.base_url)
        
        # Contract: verify capabilities structure and type
        assert isinstance(provider.capabilities, ProviderCapabilities)
        # Should have basic text support capability
        assert provider.capabilities.supports_text is True
        # Should not claim unsupported capabilities by default
        assert provider.capabilities.supports_images is False
        assert provider.capabilities.supports_files_upload is False
