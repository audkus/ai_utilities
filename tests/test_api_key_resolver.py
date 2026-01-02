"""
Tests for API key resolution functionality.

These tests ensure that API keys are resolved with proper precedence
and that helpful error messages are provided when keys are missing.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from ai_utilities.api_key_resolver import resolve_api_key, MissingApiKeyError


class TestApiKeyResolution:
    """Test API key resolution with different sources and precedence."""
    
    def test_explicit_api_key_overrides_env_var(self):
        """Test that explicit api_key parameter takes highest precedence."""
        # Set environment variable
        os.environ["AI_API_KEY"] = "env-key"
        
        # Explicit key should override
        result = resolve_api_key(explicit_api_key="explicit-key")
        assert result == "explicit-key"
        
        # Clean up
        del os.environ["AI_API_KEY"]
    
    def test_explicit_api_key_overrides_settings(self):
        """Test that explicit api_key parameter overrides settings key."""
        result = resolve_api_key(
            explicit_api_key="explicit-key",
            settings_api_key="settings-key"
        )
        assert result == "explicit-key"
    
    def test_settings_api_key_overrides_env_var(self):
        """Test that settings API key overrides environment variable."""
        os.environ["AI_API_KEY"] = "env-key"
        
        result = resolve_api_key(
            settings_api_key="settings-key"
        )
        assert result == "settings-key"
        
        # Clean up
        del os.environ["AI_API_KEY"]
    
    def test_env_var_used_when_no_explicit_or_settings(self):
        """Test that environment variable is used when no higher precedence keys."""
        os.environ["AI_API_KEY"] = "env-key"
        
        result = resolve_api_key()
        assert result == "env-key"
        
        # Clean up
        del os.environ["AI_API_KEY"]
    
    def test_env_file_used_when_env_var_missing(self, tmp_path):
        """Test that .env file is used when environment variable is missing."""
        # Create test .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AI_API_KEY=env-file-key\n")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = resolve_api_key(env_file=".env")
            assert result == "env-file-key"
        finally:
            os.chdir(original_cwd)
    
    def test_env_file_ignored_when_placeholder(self, tmp_path):
        """Test that placeholder .env value is ignored."""
        # Create test .env file with placeholder
        env_file = tmp_path / ".env"
        env_file.write_text("AI_API_KEY=your-key-here\n")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(MissingApiKeyError):
                resolve_api_key(env_file=".env")
        finally:
            os.chdir(original_cwd)
    
    def test_missing_api_key_raises_error(self, tmp_path):
        """Test that MissingApiKeyError is raised when no key is found."""
        # Change to temp directory to avoid .env file interference
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(MissingApiKeyError) as exc_info:
                resolve_api_key()
        finally:
            os.chdir(original_cwd)
        
        # Check that error message contains key information
        error_message = str(exc_info.value)
        assert "AI_API_KEY" in error_message
        assert "PyCharm" in error_message
    
    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from API keys."""
        os.environ["AI_API_KEY"] = "  spaced-key  "
        
        result = resolve_api_key()
        assert result == "spaced-key"
        
        # Clean up
        del os.environ["AI_API_KEY"]
    
    def test_empty_values_ignored(self, tmp_path):
        """Test that empty string values are ignored."""
        # Change to temp directory to avoid .env file interference
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            os.environ["AI_API_KEY"] = ""
            
            with pytest.raises(MissingApiKeyError):
                resolve_api_key()
        finally:
            os.chdir(original_cwd)
            if "AI_API_KEY" in os.environ:
                del os.environ["AI_API_KEY"]
    
    def test_env_file_read_error_silently_ignored(self, tmp_path):
        """Test that .env file read errors are silently ignored."""
        # Create a file that can't be read properly
        env_file = tmp_path / ".env"
        env_file.write_text("AI_API_KEY=valid-key\n")
        
        # Mock open to raise an exception
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(MissingApiKeyError):
                resolve_api_key(env_file=str(env_file))
    
    def test_precedence_order_complete(self, tmp_path):
        """Test complete precedence order with all sources available."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AI_API_KEY=env-file-key\n")
        
        # Set environment variable
        os.environ["AI_API_KEY"] = "env-var-key"
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Test each precedence level
            result1 = resolve_api_key()  # Should use env var
            assert result1 == "env-var-key"
            
            result2 = resolve_api_key(settings_api_key="settings-key")  # Should use settings
            assert result2 == "settings-key"
            
            result3 = resolve_api_key(explicit_api_key="explicit-key")  # Should use explicit
            assert result3 == "explicit-key"
            
        finally:
            os.chdir(original_cwd)
            del os.environ["AI_API_KEY"]


class TestMissingApiKeyError:
    """Test MissingApiKeyError exception messages."""
    
    def test_error_message_contains_required_elements(self, tmp_path):
        """Test that error message contains all required elements."""
        # Change to temp directory to avoid .env file interference
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(MissingApiKeyError) as exc_info:
                resolve_api_key()
            
            error_message = str(exc_info.value)
            
            # Check for required elements
            required_elements = [
                "AI_API_KEY",
                "PyCharm",
                ".env",
                "export AI_API_KEY",  # macOS/Linux command
                "$env:AI_API_KEY",    # Windows PowerShell command
            ]
            
            for element in required_elements:
                assert element in error_message, f"Missing element: {element}"
        finally:
            os.chdir(original_cwd)
    
    def test_error_message_platform_specific(self, tmp_path):
        """Test that error message is platform-specific."""
        # Change to temp directory to avoid .env file interference
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(MissingApiKeyError) as exc_info:
                resolve_api_key()
            
            error_message = str(exc_info.value)
            
            if sys.platform == "win32":
                # Windows should show Windows commands first
                assert "$env:AI_API_KEY" in error_message
                assert "setx AI_API_KEY" in error_message
            else:
                # macOS/Linux should show Unix commands first
                assert "export AI_API_KEY" in error_message
                assert "source ~/.zshrc" in error_message or "source ~/.bashrc" in error_message
        finally:
            os.chdir(original_cwd)
    
    def test_error_message_no_key_leakage(self):
        """Test that no actual API key is ever printed in error messages."""
        # Set a real-looking key
        os.environ["AI_API_KEY"] = "sk-1234567890abcdef"
        
        try:
            # This should not raise an error since key is set
            result = resolve_api_key()
            assert result == "sk-1234567890abcdef"
            
            # Force the error by calling resolver with no sources
            with patch("ai_utilities.api_key_resolver.resolve_api_key") as mock_resolve:
                mock_resolve.side_effect = MissingApiKeyError()
                
                # Import the exception directly to test its message
                error = MissingApiKeyError()
                error_message = str(error)
                
                # Ensure the actual key is not in the error message
                assert "sk-1234567890abcdef" not in error_message
        
        finally:
            del os.environ["AI_API_KEY"]


class TestIntegrationWithClient:
    """Test integration with client creation."""
    
    def test_create_client_with_explicit_key(self):
        """Test create_client with explicit API key."""
        from ai_utilities import create_client
        
        # This should work without environment variables
        client = create_client(api_key="test-key", provider="openai_compatible", base_url="http://localhost:11434/v1")
        assert client.settings.api_key == "test-key"
    
    def test_create_client_without_key_raises_error(self, tmp_path):
        """Test create_client without API key raises MissingApiKeyError for OpenAI provider."""
        from ai_utilities import create_client
        from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
        
        # Change to temp directory to avoid .env file interference
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Remove any existing API keys from environment
            api_keys_to_remove = ["AI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
            removed_keys = []
            for key in api_keys_to_remove:
                if key in os.environ:
                    del os.environ[key]
                    removed_keys.append(key)
            
            # Create an empty .env file to ensure no keys are loaded from it
            env_file = tmp_path / ".env"
            env_file.write_text("# Empty .env file for testing\n")
            
            # Test that OpenAI provider requires API key
            # The provider factory now converts MissingApiKeyError to ProviderConfigurationError
            # Disable auto_setup to prevent interactive prompts and disable .env loading
            with pytest.raises(ProviderConfigurationError) as exc_info:
                create_client(provider="openai", _env_file=None, auto_setup=False)
            
            # Check that the error message is still helpful
            error_message = str(exc_info.value)
            assert "API key is required" in error_message
        finally:
            os.chdir(original_cwd)
    
    def test_create_client_with_env_file(self, tmp_path):
        """Test create_client works with .env file."""
        from ai_utilities.client import AiClient, AiSettings
        
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AI_API_KEY=env-file-key\n")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Use explicit settings with from_dotenv since auto-loading is disabled during pytest
            settings = AiSettings.from_dotenv(str(env_file), provider="openai_compatible", base_url="http://localhost:11434/v1")
            
            # Use AiClient directly instead of create_client
            client = AiClient(settings=settings, auto_setup=False)
            assert client.settings.api_key == "env-file-key"
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
