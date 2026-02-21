"""Tests for SetupWizard connectivity probing functionality.

Contract-first tests for optional connectivity probing with strict isolation.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from ai_utilities.cli.setup_wizard import SetupWizard, SetupMode


@dataclass
class MockProbeResult:
    """Mock ProbeResult for testing."""
    success: bool
    provider: str
    base_url: str
    message: str
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None


class TestSetupProbe:
    """Test SetupWizard connectivity probing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.wizard = SetupWizard()
        self.dotenv_path = Path("/tmp/test.env")
    
    def test_probe_not_called_in_non_interactive(self):
        """Test probing is not called in non-interactive mode."""
        with patch.object(self.wizard, '_is_interactive', return_value=False), \
             patch.object(self.wizard, '_probe_connection') as mock_probe:
            
            # Run non-interactive setup
            self.wizard.run_non_interactive_setup(
                self.dotenv_path,
                mode=SetupMode.SINGLE_PROVIDER,
                provider="openai",
                api_key="test-key"
            )
            
            # Probing should not be called
            mock_probe.assert_not_called()
    
    def test_probe_skipped_in_dry_run(self):
        """Test probing is skipped in dry-run mode."""
        with patch.object(self.wizard, '_is_interactive', return_value=True), \
             patch.object(self.wizard, '_prompt_yes_no', return_value=False), \
             patch.object(self.wizard, '_probe_connection') as mock_probe, \
             patch.object(self.wizard, 'check_optional_dependencies'):
            
            # Mock interactive setup but user declines probing
            with patch.object(self.wizard, '_select_setup_mode', return_value=SetupMode.SINGLE_PROVIDER), \
                 patch.object(self.wizard, '_prompt_choice', return_value="OpenAI - Official OpenAI API"), \
                 patch.object(self.wizard, '_configure_provider', return_value={"api_key": "test-key", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"}):
                
                result = self.wizard.run_interactive_setup(self.dotenv_path)
                
                # Probing should not be called since user declined
                mock_probe.assert_not_called()
    
    @patch('requests.get')
    def test_hosted_probe_success(self, mock_get):
        """Test successful hosted provider probe."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4o-mini"}]}
        mock_get.return_value = mock_response
        
        result = self.wizard._probe_hosted("openai", "https://api.openai.com/v1", "test-key")
        
        assert result.success is True
        assert result.provider == "openai"
        assert result.base_url == "https://api.openai.com/v1"
        assert "connected successfully" in result.message.lower() or "connected to openai successfully" in result.message.lower()
        assert result.status_code == 200
        assert result.response_time_ms is not None
        
        # Verify correct API call
        mock_get.assert_called_once_with(
            "https://api.openai.com/v1/models",
            headers={"Authorization": "Bearer test-key"},
            timeout=3
        )
    
    @patch('requests.get')
    def test_hosted_probe_invalid_key(self, mock_get):
        """Test hosted provider probe with invalid API key."""
        # Mock authentication failure
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = self.wizard._probe_hosted("openai", "https://api.openai.com/v1", "invalid-key")
        
        assert result.success is False
        assert result.provider == "openai"
        assert result.base_url == "https://api.openai.com/v1"
        assert "authentication failed" in result.message.lower() or "unauthorized" in result.message.lower()
        assert result.status_code == 401
    
    @patch('requests.get')
    def test_local_probe_unreachable(self, mock_get):
        """Test local provider probe when unreachable."""
        # Mock connection error
        mock_get.side_effect = Exception("Connection failed")
        
        result = self.wizard._probe_ollama("http://localhost:11434/v1")
        
        assert result.success is False
        assert result.provider == "ollama"
        assert result.base_url == "http://localhost:11434/v1"
        assert "connection failed" in result.message.lower() or "unreachable" in result.message.lower()
    
    @patch('requests.get')
    def test_probe_never_raises(self, mock_get):
        """Test that probing never raises exceptions."""
        # Mock various exception scenarios
        exceptions = [
            Exception("General error"),
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out"),
        ]
        
        for exc in exceptions:
            mock_get.side_effect = exc
            
            # All probe methods should handle exceptions gracefully
            result1 = self.wizard._probe_hosted("openai", "https://api.openai.com/v1", "test-key")
            assert result1.success is False
            assert isinstance(result1.message, str)
            
            result2 = self.wizard._probe_ollama("http://localhost:11434/v1")
            assert result2.success is False
            assert isinstance(result2.message, str)
            
            result3 = self.wizard._probe_generic("http://example.com")
            assert result3.success is False
            assert isinstance(result3.message, str)
    
    @patch('requests.get')
    def test_generic_probe_success(self, mock_get):
        """Test generic probe success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.wizard._probe_generic("http://example.com")
        
        assert result.success is True
        assert result.provider == "generic"
        assert result.base_url == "http://example.com"
        assert "connected" in result.message.lower()
        assert result.status_code == 200
    
    @patch('requests.get')
    def test_probe_dispatcher(self, mock_get):
        """Test the probe dispatcher routes to correct methods."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Create wizard with network access enabled for this test
        wizard = SetupWizard(allow_network=True)
        
        # Test hosted provider routing
        result = wizard._probe_connection("openai", "https://api.openai.com/v1", "test-key")
        assert result.provider == "openai"
        mock_get.assert_called_with(
            "https://api.openai.com/v1/models",
            headers={"Authorization": "Bearer test-key"},
            timeout=3
        )
        
        # Reset mock
        mock_get.reset_mock()
        
        # Test ollama routing
        result = wizard._probe_connection("ollama", "http://localhost:11434/v1")
        assert result.provider == "ollama"
        mock_get.assert_called_with("http://localhost:11434/v1/api/tags", timeout=3)
        
        # Reset mock
        mock_get.reset_mock()
        
        # Test generic routing for unknown providers
        result = wizard._probe_connection("unknown", "http://example.com")
        assert result.provider == "generic"
        mock_get.assert_called_with("http://example.com", timeout=3)
    
    def test_probe_result_structure(self):
        """Test ProbeResult dataclass structure."""
        # Now that ProbeResult is implemented, test its structure
        from ai_utilities.cli.setup_wizard import ProbeResult
        
        result = ProbeResult(
            success=True,
            provider="test",
            base_url="http://test.com",
            message="Test message",
            response_time_ms=100.0,
            status_code=200
        )
        
        assert result.success is True
        assert result.provider == "test"
        assert result.base_url == "http://test.com"
        assert result.message == "Test message"
        assert result.response_time_ms == 100.0
        assert result.status_code == 200
