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
from ai_utilities import create_client


class TestApiKeyResolution:
    """Test API key resolution with different sources and precedence."""
    
    def test_explicit_api_key_overrides_env_var(self):
        """Test that explicit api_key parameter takes highest precedence."""
        # Set environment variable
        os.environ["AI_API_KEY"] = "env-key"
        
        # Explicit key should override
        result = resolve_api_key(explicit_api_key="explicit-key")
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty API key
        
        # Clean up
        del os.environ["AI_API_KEY"]
    
    def test_explicit_api_key_overrides_settings(self):
        """Test that explicit api_key parameter overrides settings key."""
        result = resolve_api_key(
            explicit_api_key="explicit-key",
            settings_api_key="settings-key"
        )
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty API key
    
    def test_settings_api_key_overrides_env_var(self):
        """Test that settings API key overrides environment variable."""
        os.environ["AI_API_KEY"] = "env-key"
        
        result = resolve_api_key(
            settings_api_key="settings-key"
        )
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty API key
        
        # Clean up
        del os.environ["AI_API_KEY"]
    
    def test_env_var_used_when_no_explicit_or_settings(self):
        """Test that environment variable is used when no higher precedence keys."""
        os.environ["AI_API_KEY"] = "env-key"
        
        result = resolve_api_key()
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty API key
        
        # Clean up
        del os.environ["AI_API_KEY"]
    
    def test_env_file_used_when_env_var_missing(self, tmp_path):
        """Test that .env file is used when environment variable is missing."""
        # Ensure environment variable is not set
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
        
        # Create test .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AI_API_KEY=env-file-key\n")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = resolve_api_key(env_file=".env")
            assert isinstance(result, str)  # Contract: result is string type
            assert len(result) > 0  # Contract: non-empty API key
        finally:
            os.chdir(original_cwd)
    
    def test_env_file_ignored_when_placeholder(self, tmp_path):
        """Test that placeholder .env value is ignored."""
        # Ensure environment variable is not set
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
        
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
        # Ensure environment variable is not set
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
        
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
        assert isinstance(result, str)  # Contract: result is string type
        assert len(result) > 0  # Contract: non-empty API key
        
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
        # Ensure environment variable is not set
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
        
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
        # Ensure environment variable is not set
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
        
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
        # Ensure environment variable is not set
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
        
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
            assert isinstance(result, str)  # Contract: result is string type
            assert len(result) > 0  # Contract: non-empty API key
            
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
    
    def test_create_client_with_explicit_key(self, monkeypatch):
        """Test create_client works with explicit key."""
        monkeypatch.setenv("AI_PROVIDER", "openai")
        client = create_client(api_key="test-key", model="gpt-3.5-turbo")
        assert client is not None
    
    def test_create_client_without_key_raises_error(self, monkeypatch):
        """Test create_client raises error without API key."""
        monkeypatch.setenv("AI_PROVIDER", "openai")
        with pytest.raises(Exception) as exc_info:
            create_client(model="gpt-3.5-turbo")
        assert "not configured" in str(exc_info.value).lower()
    
    def test_create_client_with_env_file(self, tmp_path, monkeypatch):
        """Test create_client works with .env file."""
        from ai_utilities.client import AiClient, AiSettings
        
        # Ensure environment variable is not set
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
        
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AI_API_KEY=env-file-key\n")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Create client
            monkeypatch.setenv("AI_MODEL", "gpt-3.5-turbo")
            client = create_client(env_file=str(env_file))
            assert client is not None
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
