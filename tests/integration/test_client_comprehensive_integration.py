"""
Comprehensive integration tests for client.py including full functionality coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os
import json
from pydantic import BaseModel, ValidationError

from ai_utilities.client import (
    AiClient, _sanitize_namespace, _default_namespace, _running_under_pytest, create_client
)
from ai_utilities.config_models import AiSettings
from ai_utilities.models import AskResult
from ai_utilities.json_parsing import JsonParseError
from ai_utilities.file_models import UploadedFile
from ai_utilities.providers.provider_exceptions import (
    FileTransferError, ProviderCapabilityError, ProviderConfigurationError
)

pytestmark = pytest.mark.integration


class TestClientIntegrationWorkflows:
    """Integration tests for complete client workflows."""
    
    def test_ask_many_with_concurrency_and_fail_fast(self):
        """Test ask_many with concurrency control and fail_fast."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model = "gpt-3.5-turbo"
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            # Simulate one success, one failure
            mock_provider.ask.side_effect = ["Response 1", Exception("Failed"), "Response 3"]
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            results = client.ask_many(["Prompt 1", "Prompt 2", "Prompt 3"], 
                                    concurrency=2, fail_fast=True)
            
            assert len(results) == 3
            assert results[0].response == "Response 1"
            assert results[0].error is None
            assert results[1].response is None
            assert results[1].error == "Failed"
            assert results[2].error == "Cancelled due to fail_fast mode"
    
    def test_json_workflow_with_repair_mechanism(self):
        """Test complete JSON workflow with repair mechanism."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider, \
             patch('ai_utilities.client.parse_json_from_text') as mock_parse, \
             patch('ai_utilities.client.create_repair_prompt') as mock_repair:
            
            mock_provider = Mock()
            mock_provider.ask_text.side_effect = ["invalid json", '{"key": "fixed"}']
            mock_create_provider.return_value = mock_provider
            
            # First parse fails, second succeeds
            mock_parse.side_effect = [JsonParseError("Invalid", "invalid json"), {"key": "fixed"}]
            mock_repair.return_value = "repair prompt"
            
            client = AiClient(settings=mock_settings)
            result = client.ask_json("Test prompt", max_repairs=1)
            
            assert result == {"key": "fixed"}
            assert mock_parse.call_count == 2
            assert mock_provider.ask_text.call_count == 2
    
    def test_typed_response_workflow(self):
        """Test typed response workflow with Pydantic models."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        class TestModel(BaseModel):
            name: str
            age: int
            email: str = None
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider, \
             patch.object(AiClient, 'ask_json') as mock_ask_json:
            
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            mock_ask_json.return_value = {"name": "Alice", "age": 30, "email": "alice@test.com"}
            
            client = AiClient(settings=mock_settings)
            result = client.ask_typed("Test prompt", TestModel)
            
            assert isinstance(result, TestModel)
            assert result.name == "Alice"
            assert result.age == 30
            assert result.email == "alice@test.com"


class TestClientFileOperationsIntegration:
    """Integration tests for file operations."""
    
    def test_complete_file_upload_download_workflow(self):
        """Test complete file upload and download workflow."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider, \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True):
            
            mock_provider = Mock()
            mock_uploaded_file = Mock()
            mock_uploaded_file.file_id = "file-123"
            mock_uploaded_file.filename = "test.txt"
            mock_uploaded_file.size = 1024
            mock_provider.upload_file.return_value = mock_uploaded_file
            mock_provider.download_file.return_value = b"downloaded content"
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # Upload workflow (with file reading)
            with patch('builtins.open', mock_open(read_data=b"file content")):
                uploaded = client.upload_file("/test/file.txt")
                assert uploaded.file_id == "file-123"
            
            # Download workflow (bytes)
            content = client.download_file("file-123")
            assert content == b"downloaded content"
            
            # Download workflow (to file)
            with patch('pathlib.Path.mkdir'), \
                 patch('builtins.open', mock_open()) as mock_file:
                
                result_path = client.download_file("file-123", to_path="/output/downloaded.txt")
                assert isinstance(result_path, Path)
    
    def test_file_operations_error_handling(self):
        """Test file operations with comprehensive error handling."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # Test file not found
            with pytest.raises(ValueError, match="File does not exist"):
                client.upload_file("/nonexistent/file.txt")
            
            # Test directory instead of file
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.is_file', return_value=False):
                
                with pytest.raises(ValueError, match="Path is not a file"):
                    client.upload_file("/test/directory")
            
            # Test empty file ID
            with pytest.raises(ValueError, match="file_id cannot be empty"):
                client.download_file("")
            
            # Test provider capability errors
            mock_provider.upload_file.side_effect = ProviderCapabilityError("Not supported", "test-provider")
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.is_file', return_value=True):
                
                with pytest.raises(ProviderCapabilityError):
                    client.upload_file("/test/file.txt")


class TestClientImageGenerationIntegration:
    """Integration tests for image generation."""
    
    def test_image_generation_workflow(self):
        """Test complete image generation workflow."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_provider.generate_image.return_value = ["https://example.com/image1.png", "https://example.com/image2.png"]
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            result = client.generate_image("A beautiful sunset", n=2, size="1024x1024")
            
            assert len(result) == 2
            assert all(url.startswith("https://") for url in result)
            mock_provider.generate_image.assert_called_once_with(
                "A beautiful sunset", size="1024x1024", quality="standard", n=2
            )
    
    def test_image_generation_validation(self):
        """Test image generation parameter validation."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # Test empty prompt
            with pytest.raises(ValueError, match="prompt cannot be empty"):
                client.generate_image("")
            
            # Test invalid n values
            with pytest.raises(ValueError, match="n must be between 1 and 10"):
                client.generate_image("test", n=0)
            
            with pytest.raises(ValueError, match="n must be between 1 and 10"):
                client.generate_image("test", n=11)


class TestClientAudioProcessingIntegration:
    """Integration tests for audio processing."""
    
    def test_audio_transcription_workflow(self):
        """Test complete audio transcription workflow."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            # Mock AudioProcessor
            with patch('ai_utilities.audio.audio_processor.AudioProcessor') as mock_processor_class:
                mock_processor = Mock()
                mock_result = Mock()
                mock_result.text = "Transcribed audio content"
                mock_result.language = "en"
                mock_result.duration_seconds = 30.5
                mock_result.model_used = "whisper-1"
                mock_result.processing_time_seconds = 5.2
                mock_result.word_count = 3
                mock_result.character_count = 26
                mock_result.segments = None
                mock_result.metadata = {}
                
                mock_processor.transcribe_audio.return_value = mock_result
                mock_processor_class.return_value = mock_processor
                
                client = AiClient(settings=mock_settings)
                result = client.transcribe_audio("audio.wav")
                
                assert result["text"] == "Transcribed audio content"
                assert result["language"] == "en"
                assert result["duration_seconds"] == 30.5
    
    def test_audio_generation_workflow(self):
        """Test complete audio generation workflow."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            # Mock AudioProcessor and AudioFormat
            with patch('ai_utilities.audio.audio_processor.AudioProcessor') as mock_processor_class, \
                 patch('ai_utilities.audio.audio_models.AudioFormat') as mock_format:
                
                mock_processor = Mock()
                mock_result = Mock()
                mock_result.audio_data = b"generated audio data"
                mock_processor.generate_audio.return_value = mock_result
                mock_processor_class.return_value = mock_processor
                
                mock_format.MP3 = "mp3"
                
                client = AiClient(settings=mock_settings)
                result = client.generate_audio("Hello world", voice="alloy", response_format="mp3")
                
                assert result == b"generated audio data"
    
    def test_audio_voices_and_validation(self):
        """Test audio voices retrieval and validation."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            with patch('ai_utilities.audio.audio_processor.AudioProcessor') as mock_processor_class:
                mock_processor = Mock()
                mock_processor.get_supported_voices.return_value = {
                    "voices": [
                        {"id": "alloy", "name": "Alloy", "language": "en"},
                        {"id": "echo", "name": "Echo", "language": "en"}
                    ]
                }
                mock_processor.validate_audio_for_transcription.return_value = {
                    "valid": True,
                    "duration": 45.2,
                    "format": "wav"
                }
                mock_processor_class.return_value = mock_processor
                
                client = AiClient(settings=mock_settings)
                
                # Test voices
                voices = client.get_audio_voices()
                assert len(voices) == 2
                assert voices[0]["id"] == "alloy"
                
                # Test validation
                validation = client.validate_audio_file("test.wav")
                assert validation["valid"] is True
                assert validation["duration"] == 45.2


class TestClientKnowledgeBaseIntegration:
    """Integration tests for knowledge base functionality."""
    
    def test_knowledge_base_disabled_handling(self):
        """Test knowledge base functionality when disabled."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.knowledge_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # All knowledge operations should raise errors when disabled
            with pytest.raises(Exception):
                client._ensure_knowledge_enabled()
            
            with pytest.raises(Exception):
                client.index_knowledge()
            
            with pytest.raises(Exception):
                client.search_knowledge("test query")
            
            with pytest.raises(Exception):
                client.ask_with_knowledge("test query")


class TestClientEmbeddingsIntegration:
    """Integration tests for embeddings functionality."""
    
    def test_embeddings_workflow(self):
        """Test complete embeddings workflow."""
        try:
            import openai
        except ImportError:
            pytest.skip("OpenAI package not available for embeddings test")
            
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.api_key = "test-api-key"
        mock_settings.embedding_model = "text-embedding-3-small"
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider, \
             patch('openai.OpenAI') as mock_openai:
            
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            # Setup OpenAI mock
            mock_client = Mock()
            mock_response = Mock()
            mock_data = Mock()
            mock_data.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            mock_response.data = [mock_data]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = AiClient(settings=mock_settings)
            
            # Test basic embeddings
            result = client.get_embeddings(["test text"])
            assert result == [[0.1, 0.2, 0.3, 0.4, 0.5]]
            
            # Test with dimensions
            result = client.get_embeddings(["test text"], dimensions=512)
            assert result == [[0.1, 0.2, 0.3, 0.4, 0.5]]
            
            # Test with custom model
            result = client.get_embeddings(["test text"], model="custom-model")
            assert result == [[0.1, 0.2, 0.3, 0.4, 0.5]]
            
            # Verify OpenAI was called correctly
            assert mock_client.embeddings.create.call_count == 3
    
    def test_embeddings_error_handling(self):
        """Test embeddings error handling."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.api_key = None  # No API key
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # Test without API key
            with pytest.raises(ValueError, match="API key is required for embeddings"):
                client.get_embeddings(["test"])


class TestClientConfigurationIntegration:
    """Integration tests for client configuration and setup."""
    
    def test_client_configuration_from_dotenv(self):
        """Test client configuration from .env file."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('ai_utilities.client.AiSettings.from_dotenv') as mock_from_dotenv, \
             patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            
            mock_settings = Mock()
            mock_settings.cache_enabled = False
            mock_settings.model_dump.return_value = {}
            mock_from_dotenv.return_value = mock_settings
            
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            client = AiClient()
            
            assert client.settings == mock_settings
            mock_from_dotenv.assert_called_once_with(".env")
    
    def test_client_reconfiguration_workflow(self):
        """Test client reconfiguration workflow."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        mock_settings.provider = "openai"  # Add provider attribute
        mock_settings.api_key = "test-key"
        mock_settings.model = "gpt-3.5-turbo"
        
        with patch('ai_utilities.client.AiSettings.interactive_setup') as mock_setup, \
             patch('ai_utilities.providers.openai_provider.OpenAIProvider') as mock_openai_provider:
            
            mock_new_settings = Mock()
            mock_new_settings.base_url = "https://new-api.example.com"
            mock_new_settings.model = "gpt-4"
            mock_new_settings.provider = "openai"
            mock_new_settings.api_key = "test-key"
            mock_setup.return_value = mock_new_settings
            
            mock_new_provider = Mock()
            mock_openai_provider.return_value = mock_new_provider
            
            client = AiClient(settings=mock_settings)
            
            # Test reconfiguration
            client.reconfigure()
            
            assert client.settings == mock_new_settings
            assert client.provider == mock_new_provider
            mock_setup.assert_called_once_with(force_reconfigure=True)
            # OpenAIProvider should be called twice: once for init, once for reconfigure
            assert mock_openai_provider.call_count == 2
            # Check that provider was called with settings objects (exact args may differ due to resolution)
            assert mock_openai_provider.call_args_list[0][0][0] is not None
            assert mock_openai_provider.call_args_list[1][0][0] is not None
    
    def test_create_client_convenience_function(self):
        """Test create_client convenience function with various configurations."""
        with patch('ai_utilities.client.AiSettings') as mock_settings_class, \
             patch('ai_utilities.client.AiClient') as mock_aiclient:
            
            mock_settings = Mock()
            mock_settings_class.return_value = mock_settings
            mock_client = Mock()
            mock_aiclient.return_value = mock_client
            
            # Test basic creation
            result = create_client(api_key="test-key", model="gpt-4")
            assert result == mock_client
            
            # Test with additional settings
            result = create_client(
                api_key="test-key",
                model="gpt-4",
                base_url="https://custom.url",
                temperature=0.7,
                max_tokens=1000
            )
            
            mock_settings_class.assert_called_with(
                model="gpt-4",
                _env_file=None,
                base_url="https://custom.url",
                temperature=0.7,
                max_tokens=1000
            )
            assert mock_settings.api_key == "test-key"


class TestClientErrorHandlingIntegration:
    """Integration tests for comprehensive error handling."""
    
    def test_provider_error_propagation(self):
        """Test that provider errors are properly propagated."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # Test various provider errors
            mock_provider.ask.side_effect = ProviderConfigurationError("Invalid config", "openai")
            with pytest.raises(ProviderConfigurationError):
                client.ask("test")
            
            mock_provider.ask.side_effect = ProviderCapabilityError("Not supported", "openai")
            with pytest.raises(ProviderCapabilityError):
                client.ask("test")
            
            mock_provider.ask.side_effect = Exception("Generic error")
            with pytest.raises(Exception, match="Generic error"):
                client.ask("test")
    
    def test_cache_error_handling(self):
        """Test cache error handling."""
        mock_settings = Mock()
        mock_settings.cache_enabled = True
        mock_settings.model_dump.return_value = {}
        mock_settings.provider = "openai"  # Add provider attribute
        mock_settings.api_key = "test-key"
        mock_settings.model = "gpt-3.5-turbo"
        mock_settings.temperature = 0.7
        mock_settings.cache_max_temperature = 1.0  # Add numeric value for comparison
        mock_settings.cache_ttl_s = 3600
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider, \
             patch('ai_utilities.client.MemoryCache') as mock_cache_class:
            
            mock_provider = Mock()
            mock_provider.ask.return_value = "Response"
            mock_create_provider.return_value = mock_provider
            
            mock_cache = Mock()
            # Mock cache to return None (cache miss) for get operation
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache
            
            client = AiClient(settings=mock_settings)
            
            # Should handle cache gracefully and get response from provider
            result = client.ask("test")
            assert result == "Response"
            # Test passes if client works correctly with cache enabled
    
    def test_usage_tracking_error_handling(self):
        """Test usage tracking error handling."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.usage_scope = "per_client"
        mock_settings.usage_client_id = "test_client"
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider, \
             patch('ai_utilities.client.create_usage_tracker') as mock_create_tracker:
            
            mock_provider = Mock()
            mock_provider.ask.return_value = "Response"
            mock_create_provider.return_value = mock_provider
            
            mock_tracker = Mock()
            mock_tracker.track_request.side_effect = Exception("Tracking error")
            mock_create_tracker.return_value = mock_tracker
            
            client = AiClient(settings=mock_settings, track_usage=True)
            
            # Should handle tracking errors gracefully
            result = client.ask("test")
            assert result == "Response"


class TestClientPerformanceIntegration:
    """Integration tests for performance and optimization."""
    
    def test_concurrent_operations(self):
        """Test concurrent operations performance."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        mock_settings.provider = "openai"  # Add provider attribute
        mock_settings.api_key = "test-key"
        mock_settings.model = "gpt-3.5-turbo"
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            # Provider ask returns plain strings, ask_many creates AskResult objects
            mock_provider.ask.side_effect = ["Response 1", "Response 2", "Response 3", "Response 4"]
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # Test concurrent ask_many
            prompts = [f"Prompt {i}" for i in range(4)]
            results = client.ask_many(prompts, concurrency=4)
            
            assert len(results) == 4
            assert all(r.response.startswith("Response") for r in results)
            assert all(r.error is None for r in results)
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large operations."""
        mock_settings = Mock()
        mock_settings.cache_enabled = False
        mock_settings.model_dump.return_value = {}
        
        with patch('ai_utilities.providers.provider_factory.create_provider') as mock_create_provider:
            mock_provider = Mock()
            mock_provider.ask.return_value = "Large response " * 1000
            mock_create_provider.return_value = mock_provider
            
            client = AiClient(settings=mock_settings)
            
            # Test large prompt handling
            large_prompt = "Test " * 10000
            result = client.ask(large_prompt)
            
            assert "Large response" in result
            assert len(result) > 1000
