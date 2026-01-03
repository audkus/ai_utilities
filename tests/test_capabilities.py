"""Tests for capability matrix functionality."""

import pytest
from ai_utilities.capabilities import AiCapabilities
from ai_utilities import AiSettings, AiClient
from ai_utilities.providers.base_provider import BaseProvider
from unittest.mock import Mock


class TestAiCapabilities:
    """Test AiCapabilities model."""
    
    def test_default_capabilities(self):
        """Default capabilities should have text=True, everything else=False."""
        caps = AiCapabilities()
        
        assert caps.text is True
        assert caps.vision is False
        assert caps.audio is False
        assert caps.files is False
        assert caps.embeddings is False
        assert caps.tools is False
    
    def test_capabilities_repr(self):
        """String representation shows enabled capabilities."""
        caps = AiCapabilities(text=True, vision=True)
        repr_str = repr(caps)
        
        assert "text" in repr_str
        assert "vision" in repr_str
        assert "audio" not in repr_str  # Should not show False capabilities
    
    def test_capabilities_can_be_modified(self):
        """Capabilities can be customized."""
        caps = AiCapabilities(vision=True, audio=True)
        
        assert caps.text is True  # Default
        assert caps.vision is True
        assert caps.audio is True
        assert caps.files is False  # Default


class TestProviderCapabilities:
    """Test provider capability integration."""
    
    def test_base_provider_default_capabilities(self):
        """Base provider should return conservative default capabilities."""
        class TestProvider(BaseProvider):
            def ask(self, prompt, **kwargs):
                return "response"
            
            def ask_many(self, prompts, **kwargs):
                return ["response"]
            
            def upload_file(self, path, **kwargs):
                return Mock()
            
            def download_file(self, file_id):
                return b"content"
            
            def generate_image(self, prompt, **kwargs):
                return ["url"]
        
        provider = TestProvider()
        caps = provider.get_capabilities()
        
        assert isinstance(caps, AiCapabilities)
        assert caps.text is True
        assert caps.vision is False
        assert caps.audio is False
        assert caps.files is False
        assert caps.embeddings is False
        assert caps.tools is False
    
    @pytest.mark.skip(reason="Would require actual OpenAI API key")
    def test_real_provider_capabilities(self):
        """Real providers should return appropriate capabilities."""
        # This test would be skipped in CI but could be run manually
        # with real API keys to verify provider-specific capabilities
        pass


class TestAiClientCapabilities:
    """Test AiClient capability integration."""
    
    def test_client_capabilities_delegates_to_provider(self):
        """AiClient.capabilities() should delegate to provider."""
        # Create mock provider with custom capabilities
        mock_provider = Mock()
        custom_caps = AiCapabilities(vision=True, audio=True)
        mock_provider.get_capabilities.return_value = custom_caps
        
        # Create client with mock provider
        settings = AiSettings(provider="openai", api_key="fake-key")
        client = AiClient(settings)
        client.provider = mock_provider
        
        # Should delegate to provider
        caps = client.capabilities()
        assert caps == custom_caps
        assert caps.vision is True
        assert caps.audio is True
    
    def test_stub_methods_raise_not_implemented(self):
        """Stub methods should raise NotImplementedError with clear messages."""
        settings = AiSettings(provider="openai", api_key="fake-key")
        client = AiClient(settings)
        
        # Test analyze_image stub
        with pytest.raises(NotImplementedError, match="Image analysis is not yet implemented"):
            client.analyze_image("test.jpg", "What do you see?")
        
        # Test transcribe_audio stub
        with pytest.raises(NotImplementedError, match="Audio transcription is not yet implemented"):
            client.transcribe_audio("test.mp3")
    
    def test_stub_methods_accept_various_input_types(self):
        """Stub methods should accept different input types in signatures."""
        settings = AiSettings(provider="openai", api_key="fake-key")
        client = AiClient(settings)
        
        # These should raise NotImplementedError, not TypeError
        with pytest.raises(NotImplementedError):
            client.analyze_image("path/to/image.jpg", "describe")
        
        with pytest.raises(NotImplementedError):
            client.analyze_image(b"bytes", "describe")
        
        with pytest.raises(NotImplementedError):
            client.transcribe_audio("path/to/audio.mp3")
        
        with pytest.raises(NotImplementedError):
            client.transcribe_audio(b"bytes")
    
    def test_capabilities_are_conservative(self):
        """Capabilities should be conservative - only what library actually supports."""
        settings = AiSettings(provider="openai", api_key="fake-key")
        client = AiClient(settings)
        
        caps = client.capabilities()
        
        # Even though OpenAI supports vision/audio, library should return False
        # until those features are actually implemented and stable
        assert caps.text is True
        assert caps.vision is False
        assert caps.audio is False
        assert caps.files is False
        assert caps.embeddings is False
        assert caps.tools is False
