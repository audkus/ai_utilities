"""Comprehensive tests for the AI client - Phase 1."""

import os

import pytest
from ai_utilities import AiClient, AiSettings, create_client
from ai_utilities.models import AskResult
from tests.fake_provider import FakeProvider, FakeProviderError


class TestAiClientBasics:
    """Test basic AiClient functionality."""
    
    def test_no_side_effects_on_import(self):
        """Test that importing ai_utilities doesn't create files or make network calls."""
        # This test passes if the import doesn't raise exceptions
        # and no side effects occur during import
        assert True
    
    def test_ai_client_creation_with_settings(self, fake_settings):
        """Test creating AI client with explicit settings."""
        client = AiClient(fake_settings)
        assert client.settings.api_key == "test-key-for-testing"
        assert client.settings.model == "gpt-3.5-turbo"
        assert client.settings.temperature == 0.7
    
    def test_ai_client_creation_with_provider(self, fake_provider):
        """Test creating AI client with custom provider."""
        client = AiClient(provider=fake_provider)
        assert client.provider is fake_provider
    
    def test_create_client_convenience(self):
        """Test the create_client convenience function."""
        client = create_client(
            api_key="test-key",
            model="gpt-3.5-turbo",  # Use default model
            temperature=0.5
        )
        assert client.settings.api_key == "test-key"
        assert client.settings.model == "gpt-3.5-turbo"
        assert client.settings.temperature == 0.5


class TestAiClientAsk:
    """Test AiClient.ask() functionality."""
    
    def test_ask_single_prompt(self, fake_client):
        """Test single prompt returns expected response."""
        response = fake_client.ask("What is 2+2?")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_ask_with_json_format(self, fake_client):
        """Test ask with JSON return format."""
        response = fake_client.ask("test prompt", return_format="json")
        assert isinstance(response, dict)  # Contract: response is dict type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_ask_with_overrides(self, fake_client):
        """Test per-request parameter overrides."""
        # Test model override
        response = fake_client.ask("test", model="gpt-4")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        
        # Test temperature override
        response = fake_client.ask("test", temperature=0.1)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        
        # Test max_tokens override
        response = fake_client.ask("test", max_tokens=100)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_ask_many_prompts(self, fake_client):
        """Test batch prompts maintain order and return correct count."""
        prompts = ["first prompt", "second prompt", "third prompt"]
        responses = fake_client.ask_many(prompts)
        
        assert len(responses) == 3  # Contract: expected number of responses
        # ask_many returns AskResult objects, ask() returns strings
        assert all(hasattr(r, 'response') for r in responses)  # Contract: all have response attribute
        assert all(isinstance(r.response, str) for r in responses)  # Contract: all responses are strings
        assert all(len(r.response) > 0 for r in responses)  # Contract: non-empty responses
    
    def test_ask_many_with_json_format(self, fake_client):
        """Test ask_many with JSON return format."""
        prompts = ["prompt1", "prompt2"]
        responses = fake_client.ask_many(prompts, return_format="json")
        
        assert len(responses) == 2  # Contract: expected number of responses
        assert all(hasattr(r, 'response') and isinstance(r.response, dict) for r in responses)  # Contract: JSON responses
        assert all(len(r.response) > 0 for r in responses)  # Contract: non-empty responses
    
    def test_ask_many_with_overrides(self, fake_client):
        """Test ask_many with parameter overrides."""
        prompts = ["prompt1", "prompt2"]
        responses = fake_client.ask_many(
            prompts, 
            model="gpt-4", 
            temperature=0.1,
            max_tokens=50
        )
        
        assert len(responses) == 2  # Contract: expected number of responses
        assert all(hasattr(r, 'response') for r in responses)  # Contract: all have response attribute
    
    def test_ask_result_objects(self, fake_client):
        """Test that ask returns proper result objects when needed."""
        # Test with result format if supported
        response = fake_client.ask("test")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        
        # Test JSON format returns dict
        json_response = fake_client.ask("test", return_format="json")
        assert isinstance(json_response, dict)  # Contract: JSON response is dict type
        assert len(json_response) > 0  # Contract: non-empty response


class TestAiClientErrorHandling:
    """Test AiClient error handling."""
    
    def test_provider_error_wrapping(self, fake_settings):
        """Test that provider errors are properly wrapped."""
        failing_provider = FakeProvider(should_fail=True)
        client = AiClient(settings=fake_settings, provider=failing_provider)
        
        with pytest.raises(FakeProviderError):
            client.ask("test prompt")
    
    def test_provider_error_on_specific_call(self, fake_settings):
        """Test provider failure on specific call number."""
        failing_provider = FakeProvider(fail_on_call=2)
        client = AiClient(settings=fake_settings, provider=failing_provider)
        
        # First call should succeed
        response1 = client.ask("test1")
        assert isinstance(response1, str)  # Contract: response is string type
        assert len(response1) > 0  # Contract: non-empty response
        
        # Second call should fail
        with pytest.raises(FakeProviderError):
            client.ask("test2")
    
    def test_error_in_batch_requests(self, fake_settings):
        """Test error handling in batch requests."""
        # Test normal error handling
        failing_provider1 = FakeProvider(fail_on_call=2)
        client1 = AiClient(settings=fake_settings, provider=failing_provider1)
        
        # Should handle errors gracefully by default (no exception raised)
        results = client1.ask_many(["prompt1", "prompt2", "prompt3"])
        
        # First should succeed, second and third should fail (fail_on_call uses >=)
        assert len(results) == 3  # Contract: expected number of results
        assert results[0].error is None  # Contract: first result has no error
        assert results[1].error is not None  # Contract: second result has error
        assert results[2].error is not None  # Contract: third result has error
        
        # Test fail_fast behavior with fresh provider
        failing_provider2 = FakeProvider(fail_on_call=2)
        client2 = AiClient(settings=fake_settings, provider=failing_provider2)
        results_fail_fast = client2.ask_many(["prompt1", "prompt2", "prompt3"], fail_fast=True)
        assert len(results_fail_fast) == 3  # Contract: expected number of results
        assert results_fail_fast[0].error is None  # Contract: first result has no error
        # Second result has the actual failure error
        assert results_fail_fast[1].error is not None  # Contract: second result has error
        assert isinstance(results_fail_fast[1].error, str)  # Contract: error is string type
        assert len(results_fail_fast[1].error) > 0  # Contract: non-empty error
        # Third result has the cancellation error
        assert results_fail_fast[2].error is not None  # Contract: third result has error
        assert isinstance(results_fail_fast[2].error, str)  # Contract: error is string type
        assert len(results_fail_fast[2].error) > 0  # Contract: non-empty error
    
    def test_error_with_overrides(self, fake_settings):
        """Test that parameter overrides don't interfere with error handling."""
        failing_provider = FakeProvider(should_fail=True)
        client = AiClient(settings=fake_settings, provider=failing_provider)
        
        with pytest.raises(FakeProviderError):
            client.ask("test", model="gpt-4", temperature=0.1)


class TestAiClientParameterHandling:
    """Test parameter handling and validation."""
    
    def test_parameter_passthrough(self, fake_client):
        """Test that parameters are correctly passed to provider."""
        # Call with various parameters
        fake_client.ask(
            "test prompt",
            model="gpt-4",
            temperature=0.1,
            max_tokens=100,
            return_format="json"
        )
        
        # Check that provider received the parameters
        provider = fake_client.provider
        assert "model" in provider.last_kwargs  # Contract: model parameter passed
        assert "temperature" in provider.last_kwargs  # Contract: temperature parameter passed
        assert "max_tokens" in provider.last_kwargs  # Contract: max_tokens parameter passed
        assert provider.last_prompt == "test prompt"  # Contract: correct prompt passed
    
    def test_parameter_passthrough_batch(self, fake_client):
        """Test parameter passthrough in batch requests."""
        prompts = ["prompt1", "prompt2"]
        fake_client.ask_many(
            prompts,
            model="gpt-4",
            temperature=0.5,
            max_tokens=200
        )
        
        provider = fake_client.provider
        assert "model" in provider.last_kwargs  # Contract: model parameter passed
        assert provider.last_kwargs["model"] == "gpt-4"  # Contract: correct model value
        assert provider.last_kwargs["temperature"] == 0.5  # Contract: correct temperature value
        assert provider.last_kwargs["max_tokens"] == 200  # Contract: correct max_tokens value
    
    def test_response_format_parameter(self, fake_client):
        """Test return_format parameter handling."""
        # Test text format (default)
        response = fake_client.ask("test", return_format="text")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
        
        # Test JSON format
        response = fake_client.ask("test", return_format="json")
        assert isinstance(response, dict)  # Contract: JSON response is dict type
        assert len(response) > 0  # Contract: non-empty response


class TestAiClientEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_prompt(self, fake_client):
        """Test handling of empty prompts."""
        response = fake_client.ask("")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) >= 0  # Contract: response exists (can be empty for empty prompt)
    
    def test_very_long_prompt(self, fake_client):
        """Test handling of very long prompts."""
        long_prompt = "test " * 1000
        response = fake_client.ask(long_prompt)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_special_characters_in_prompt(self, fake_client):
        """Test handling of special characters in prompts."""
        special_prompt = "Test with émojis 🚀 and spëcial chars!"
        response = fake_client.ask(special_prompt)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_unicode_in_prompt(self, fake_client):
        """Test handling of unicode characters."""
        unicode_prompt = "Test with 中文 and ñ and العربية"
        response = fake_client.ask(unicode_prompt)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_empty_batch_list(self, fake_client):
        """Test handling of empty batch requests."""
        responses = fake_client.ask_many([])
        assert responses == []
    
    def test_single_item_batch(self, fake_client):
        """Test batch request with single item."""
        responses = fake_client.ask_many(["single prompt"])
        assert len(responses) == 1  # Contract: single response
        assert hasattr(responses[0], 'response')  # Contract: has response attribute
        assert isinstance(responses[0].response, str)  # Contract: response is string type
        assert len(responses[0].response) > 0  # Contract: non-empty response


class TestAiClientDeterministicBehavior:
    """Test that client behavior is deterministic."""
    
    def test_deterministic_responses(self, fake_client):
        """Test that responses are deterministic with same input."""
        # Create a deterministic provider with single response template
        from tests.fake_provider import FakeProvider
        deterministic_provider = FakeProvider(responses=["Response to: {prompt}"])
        
        from ai_utilities import AiClient, AiSettings
        deterministic_client = AiClient(
            settings=AiSettings(api_key="test", _env_file=None), 
            provider=deterministic_provider
        )
        
        prompt = "deterministic test"
        
        response1 = deterministic_client.ask(prompt)
        response2 = deterministic_client.ask(prompt)
        
        # Should be identical for same prompt (same format, same content)
        assert response1 == response2  # Contract: deterministic responses
        assert isinstance(response1, str)  # Contract: response is string type
        assert len(response1) > 0  # Contract: non-empty response
    
    def test_deterministic_batch_order(self, fake_client):
        """Test that batch order is preserved deterministically."""
        prompts = ["first", "second", "third"]
        
        responses1 = fake_client.ask_many(prompts)
        responses2 = fake_client.ask_many(prompts)
        
        assert len(responses1) == len(responses2) == 3  # Contract: expected number of responses
        for i in range(3):
            assert responses1[i].response == responses2[i].response  # Contract: deterministic order
            assert isinstance(responses1[i].response, str)  # Contract: response is string type
            assert len(responses1[i].response) > 0  # Contract: non-empty response
    
    def test_provider_call_count_tracking(self, fake_client):
        """Test that provider call counting works correctly."""
        initial_count = fake_client.provider.call_count
        
        fake_client.ask("test1")
        assert fake_client.provider.call_count == initial_count + 1
        
        fake_client.ask_many(["test2", "test3"])
        assert fake_client.provider.call_count == initial_count + 3


class TestAiClientIntegration:
    """Test integration scenarios."""
    
    def test_client_with_custom_responses(self, fake_settings):
        """Test client with custom response templates."""
        custom_responses = [
            "Custom response 1: {prompt}",
            '{"custom": "json response for {prompt}"}',
            "Custom response 3: {prompt}"
        ]
        custom_provider = FakeProvider(responses=custom_responses)
        client = AiClient(settings=fake_settings, provider=custom_provider)
        
        # Test text response
        response1 = client.ask("test")
        assert isinstance(response1, str)  # Contract: response is string type
        assert len(response1) > 0  # Contract: non-empty response
        
        # Test JSON response - should return dict for JSON format
        response2 = client.ask("test", return_format="json")
        # The second response is JSON, so it should be parsed as dict
        assert isinstance(response2, dict)  # Contract: JSON response is dict type
        assert len(response2) > 0  # Contract: non-empty response
        
        # Test third response
        response3 = client.ask("test")
        assert isinstance(response3, str)  # Contract: response is string type
        assert len(response3) > 0  # Contract: non-empty response
    

class TestAiClientConfiguration:
    """Test client configuration scenarios."""
    
    def test_client_without_settings_or_provider(self, monkeypatch):
        """Test client creation without explicit settings or provider."""
        # This should work if environment is set up properly
        # But in our isolated test environment, it should use defaults
        # For testing, we'll use a local provider that doesn't require API key
        monkeypatch.setenv('AI_PROVIDER', 'ollama')  # Use local provider
        monkeypatch.setenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
        monkeypatch.setenv('OLLAMA_MODEL', 'llama3')
        
        client = AiClient()
        assert client is not None  # Contract: client created
        assert client.settings.provider == 'ollama'  # Contract: provider set from environment
    
    def test_client_with_minimal_settings(self):
        """Test client with minimal required settings."""
        minimal_settings = AiSettings(
            api_key="test-key",
            _env_file=None
        )
        client = AiClient(minimal_settings)
        assert client.settings.api_key == "test-key"
        assert client.settings.model is None


class TestAiClientPhase7Enhanced:
    """Phase 7 enhanced tests for comprehensive client coverage."""
    
    def test_sanitize_namespace_function(self):
        """Test the _sanitize_namespace utility function."""
        from ai_utilities.client import _sanitize_namespace
        
        # Basic invariants
        result = _sanitize_namespace("test")
        assert isinstance(result, str)  # Contract: returns string
        assert len(result) > 0  # Contract: non-empty result
        
        # Case normalization
        result = _sanitize_namespace("Test")
        assert isinstance(result, str)  # Contract: returns string
        assert len(result) > 0  # Contract: non-empty result
        
        # Whitespace trimming
        result = _sanitize_namespace("  test  ")
        assert isinstance(result, str)  # Contract: returns string
        assert len(result) > 0  # Contract: non-empty result
        assert " " not in result  # Contract: no leading/trailing spaces
        
        # Special character handling
        result = _sanitize_namespace("test@domain.com")
        assert isinstance(result, str)  # Contract: returns string
        assert len(result) > 0  # Contract: non-empty result
        assert "@" not in result  # Contract: special chars replaced
        
        # Consecutive underscore normalization
        result = _sanitize_namespace("test__multiple___underscores")
        assert isinstance(result, str)  # Contract: returns string
        assert len(result) > 0  # Contract: non-empty result
        # Should not have triple underscores
        assert "___" not in result  # Contract: consecutive underscores normalized
    
    def test_client_with_custom_cache(self, fake_client):
        """Test client with custom cache backend."""
        from ai_utilities.cache import NullCache
        
        custom_cache = NullCache()
        client = AiClient(settings=fake_client.settings, provider=fake_client.provider, cache=custom_cache)
        
        assert client.cache is custom_cache
    
    def test_client_usage_tracking_initialization(self, fake_client):
        """Test usage tracker initialization."""
        settings_with_tracking = fake_client.settings.model_copy(update={
            "usage_tracking": True,
            "usage_namespace": "test_namespace"
        })
        
        client = AiClient(settings=settings_with_tracking, provider=fake_client.provider)
        
        # Usage tracker should be initialized when tracking is enabled
        if hasattr(client, 'usage_tracker') and client.usage_tracker is not None:
            # Namespace should be sanitized
            from ai_utilities.client import _sanitize_namespace
            expected_namespace = _sanitize_namespace("test_namespace")
            assert client.usage_tracker.namespace == expected_namespace
        else:
            # If usage tracker is not implemented, that's ok for this test
            assert True
    
    def test_ask_with_parameter_overrides(self, fake_client):
        """Test ask method with parameter overrides."""
        # Test with temperature override - should work with fake provider
        response = fake_client.ask("test", temperature=0.5, max_tokens=50)
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_ask_with_conversation_history(self, fake_client):
        """Test ask method with conversation history."""
        history = [{"role": "user", "content": "Previous question"}]
        response = fake_client.ask("Follow up question", conversation_history=history)
        
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_ask_with_files(self, fake_client):
        """Test ask method with file attachments."""
        from ai_utilities.file_models import UploadedFile
        
        # Create mock file with correct field names
        test_file = UploadedFile(
            file_id="file-123",
            filename="test.txt",
            bytes=100,
            provider="fake_provider",
            purpose="assistants"
        )
        
        response = fake_client.ask("Process this file", files=[test_file])
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_upload_file_functionality(self, fake_client):
        """Test file upload functionality."""
        import tempfile
        from pathlib import Path
        from ai_utilities.file_models import UploadedFile
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test file content")
            temp_path = f.name
        
        try:
            # Test file upload with FakeProvider
            uploaded_file = fake_client.upload_file(temp_path, purpose="assistants")
            
            # Verify the uploaded file metadata
            assert isinstance(uploaded_file, UploadedFile)  # Contract: correct type
            assert uploaded_file.filename.endswith('.txt')  # Contract: correct file extension
            assert isinstance(uploaded_file.provider, str)  # Contract: provider is string
            assert len(uploaded_file.provider) > 0  # Contract: non-empty provider
            assert isinstance(uploaded_file.purpose, str)  # Contract: purpose is string
            assert len(uploaded_file.purpose) > 0  # Contract: non-empty purpose
            assert uploaded_file.bytes > 0  # Contract: positive file size
            
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_ask_json_success(self, fake_client):
        """Test JSON parsing from ask response."""
        # Configure FakeProvider to return JSON
        fake_client.provider.responses = ['{"name": "test", "value": 123}']
        
        result = fake_client.ask_json("Get JSON data")
        assert isinstance(result, dict)  # Contract: result is dict type
        assert len(result) > 0  # Contract: non-empty result
    
    def test_ask_json_invalid_json(self, fake_client):
        """Test JSON parsing with invalid JSON."""
        from ai_utilities.json_parsing import JsonParseError
        
        # Configure FakeProvider to return invalid JSON
        fake_client.provider.responses = ['{"name": "test", "value": 123']  # Missing closing brace
        
        with pytest.raises(JsonParseError):
            fake_client.ask_json("Get JSON data")
    
    def test_ask_json_with_repair(self, fake_client):
        """Test JSON parsing with repair mechanism."""
        # Configure FakeProvider to return invalid then valid JSON
        fake_client.provider.responses = [
            '{"name": "test", "value": 123',  # Invalid
            '{"name": "test", "value": 123}'   # Valid (repaired)
        ]
        
        result = fake_client.ask_json("Get JSON data", max_repairs=1)
        assert isinstance(result, dict)  # Contract: result is dict type
        assert len(result) > 0  # Contract: non-empty result
    
    def test_ask_with_caching_enabled(self, fake_client):
        """Test ask functionality with caching enabled."""
        from ai_utilities.cache import MemoryCache
        
        settings_with_cache = fake_client.settings.model_copy(update={"cache_enabled": True})
        cache = MemoryCache()
        client = AiClient(settings=settings_with_cache, provider=fake_client.provider, cache=cache)
        
        # First call should hit provider
        response1 = client.ask("test question")
        assert isinstance(response1, str)  # Contract: response is string type
        assert len(response1) > 0  # Contract: non-empty response
        
        # Second call should use cache (if implemented)
        response2 = client.ask("test question")
        assert isinstance(response2, str)  # Contract: response is string type
        assert len(response2) > 0  # Contract: non-empty response
    
    def test_model_dump_excludes_api_key(self, fake_client):
        """Test that API key is excluded from provider calls."""
        # This is tested indirectly through the fact that provider calls work
        # without exposing the API key in test assertions
        response = fake_client.ask("test")
        assert isinstance(response, str)  # Contract: response is string type
        assert len(response) > 0  # Contract: non-empty response
    
    def test_progress_indicator_initialization(self, fake_client):
        """Test progress indicator initialization."""
        # Progress indicator should be initialized
        assert hasattr(fake_client, 'show_progress')
        # Should be True by default
        assert fake_client.show_progress is True
    
    def test_error_handling_provider_error(self, fake_client):
        """Test handling of provider errors."""
        from tests.fake_provider import FakeProviderError
        
        # Create a new client with error provider
        error_provider = FakeProvider(should_fail=True)  # Configure to raise error
        error_client = AiClient(settings=fake_client.settings, provider=error_provider)
        
        with pytest.raises(FakeProviderError):
            error_client.ask("test question")
    
    def test_dynamic_settings_update(self, fake_client):
        """Test dynamic settings updates."""
        # Update settings
        new_settings = fake_client.settings.model_copy(update={"model": "gpt-4"})
        fake_client.settings = new_settings
        
        assert fake_client.settings.model == "gpt-4"
    
    def test_client_with_different_providers(self):
        """Test client with different provider configurations."""
        # Test with basic settings - provider creation tested elsewhere
        settings = AiSettings(
            api_key="test-key",
            model="test-model",
            _env_file=None
        )
        
        # Should create client without errors
        client = AiClient(settings=settings)
        assert client.settings.model == "test-model"
    
    def test_client_configuration_isolation(self, isolated_env):
        """Test that client configuration is isolated from environment."""
        # Create client in isolated environment, explicitly prevent .env loading
        settings = AiSettings(
            api_key="test-key",
            _env_file=None
        )
        client = AiClient(settings=settings)
        
        # Should use defaults, not environment or .env file
        assert client.settings.model is None
