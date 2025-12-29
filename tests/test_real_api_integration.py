"""Real API integration tests.

These tests require actual API keys and make real network calls.
They should be run manually before releases, not in CI/CD.

The tests automatically load environment variables from .env file.
To run these tests:
    1. Ensure your .env file contains the required API keys
    2. python3 -m pytest tests/test_real_api_integration.py -v

For local AI testing, also add to .env:
    AI_PROVIDER=openai_compatible
    AI_BASE_URL=http://localhost:11434/v1
    AI_API_KEY=dummy-key
"""

import os
import pytest
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load .env file for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass  # dotenv not available, tests will need manual env setup

from ai_utilities import AiClient, AiSettings, create_provider, ProviderConfigurationError


class TestRealAPIIntegration:
    """Test real API integration with actual network calls."""
    
    @pytest.mark.skipif(
        not os.getenv("AI_API_KEY"),
        reason="Requires AI_API_KEY environment variable"
    )
    def test_openai_real_api_call(self):
        """Test real OpenAI API call."""
        # Use small model for testing
        settings = AiSettings(api_key=os.getenv("AI_API_KEY"), model="gpt-3.5-turbo")
        client = AiClient(settings)
        
        # Simple test call
        response = client.ask("What is 2+2? Answer with just the number.")
        
        # Basic validation
        assert response is not None
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        # Should contain "4" or some reference to the answer
        assert "4" in response or "four" in response.lower()
        
        print(f"✅ OpenAI API response: {response}")
    
    @pytest.mark.skipif(
        not os.getenv("AI_API_KEY"),
        reason="Requires AI_API_KEY environment variable"
    )
    def test_openai_json_mode_real(self):
        """Test OpenAI JSON mode with real API."""
        settings = AiSettings(api_key=os.getenv("AI_API_KEY"), model="gpt-3.5-turbo")
        client = AiClient(settings)
        
        # Test JSON response
        response = client.ask(
            'List 3 colors as a JSON array with format: ["red", "blue", "green"]',
            return_format="json"
        )
        
        # Validation
        assert response is not None
        assert isinstance(response, list) or isinstance(response, dict)
        if isinstance(response, list):
            assert len(response) == 3
            assert all(isinstance(item, str) for item in response)
        
        print(f"✅ OpenAI JSON response: {response}")
    
    @pytest.mark.skipif(
        not (os.getenv("AI_PROVIDER") == "openai_compatible" and os.getenv("AI_BASE_URL")),
        reason="Requires AI_PROVIDER=openai_compatible and AI_BASE_URL for local AI testing"
    )
    def test_openai_compatible_real_api(self):
        """Test OpenAI-compatible provider with real local server."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url=os.getenv("AI_BASE_URL"),
            api_key=os.getenv("AI_API_KEY", "dummy-key"),
            model=os.getenv("AI_MODEL", "llama3.2:latest")
        )
        
        client = AiClient(settings)
        
        # Simple test call
        response = client.ask("What is 2+2? Answer with just the number.")
        
        # Basic validation
        assert response is not None
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        
        print(f"✅ OpenAI-compatible API response: {response}")
    
    @pytest.mark.skipif(
        not os.getenv("AI_API_KEY"),
        reason="Requires AI_API_KEY environment variable"
    )
    def test_provider_factory_real_openai(self):
        """Test provider factory with real OpenAI."""
        settings = AiSettings(
            provider="openai",
            api_key=os.getenv("AI_API_KEY"),
            model="gpt-3.5-turbo"
        )
        
        provider = create_provider(settings)
        
        # Test provider directly
        response = provider.ask("What is 1+1? Answer with just the number.")
        
        assert response is not None
        assert isinstance(response, str)
        assert "1" in response or "one" in response.lower() or "2" in response or "two" in response.lower()
        
        print(f"✅ Provider factory OpenAI response: {response}")
    
    @pytest.mark.skipif(
        not (os.getenv("AI_PROVIDER") == "openai_compatible" and os.getenv("AI_BASE_URL")),
        reason="Requires AI_PROVIDER=openai_compatible and AI_BASE_URL for local AI testing"
    )
    def test_provider_factory_real_compatible(self):
        """Test provider factory with real OpenAI-compatible server."""
        settings = AiSettings(
            provider="openai_compatible",
            base_url=os.getenv("AI_BASE_URL"),
            api_key=os.getenv("AI_API_KEY", "dummy-key"),
            model=os.getenv("AI_MODEL", "llama3.2:latest")
        )
        
        provider = create_provider(settings)
        
        # Test provider directly
        response = provider.ask("What is 1+1? Answer with just the number.", model="llama3.2:latest")
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        
        print(f"✅ Provider factory compatible response: {response}")
    
    def test_error_handling_without_api_key(self):
        """Test that proper errors are raised without API keys (no network calls)."""
        # This should work without API keys since it's just validation
        with pytest.raises(ProviderConfigurationError) as exc_info:
            settings = AiSettings(provider="openai", api_key=None)
            create_provider(settings)
        
        assert "API key is required" in str(exc_info.value)
        print("✅ Proper error handling for missing API key")
    
    def test_error_handling_without_base_url(self):
        """Test that proper errors are raised without base URL (no network calls)."""
        with pytest.raises(ProviderConfigurationError) as exc_info:
            settings = AiSettings(provider="openai_compatible", base_url=None)
            create_provider(settings)
        
        assert "base_url is required" in str(exc_info.value)
        print("✅ Proper error handling for missing base URL")


if __name__ == "__main__":
    print("🧪 Running Real API Integration Tests")
    print("=" * 50)
    print("Note: These tests require actual API keys and make real network calls.")
    print("Set environment variables:")
    print("  For OpenAI: export AI_API_KEY='your-key'")
    print("  For Local: export AI_PROVIDER='openai_compatible' AI_BASE_URL='http://localhost:11434/v1'")
    print("=" * 50)
    
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
