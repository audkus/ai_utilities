"""Integration tests for setup wizard with real network access.

These tests are marked with @pytest.mark.integration and only run when
explicitly enabled via -m integration or --run-integration flag.
They test real connectivity behavior and network-dependent functionality.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from ai_utilities.cli.setup_wizard import SetupWizard, SetupMode


pytestmark = pytest.mark.integration


class TestSetupWizardIntegration:
    """Integration tests for SetupWizard with real network access."""
    
    def test_integration_multi_provider_with_real_connectivity(self):
        """Test multi-provider setup with real connectivity checks enabled."""
        # Skip if network not explicitly allowed
        if not os.getenv("ALLOW_NETWORK") and not os.getenv("RUN_INTEGRATION"):
            pytest.skip("Network access not enabled. Set ALLOW_NETWORK=1 or RUN_INTEGRATION=1")
        
        # Mock user responses for realistic multi-provider setup
        mock_responses = [
            "2",  # Choose multi-provider mode
            "1",  # Select ollama (local, should work if running)
            "",   # Default ollama URL
            "llama3.1",  # ollama model
            "",   # Don't test ollama connectivity individually (default=False)
            "10",  # Done selecting providers (numeric option)
            "",   # Use default auto-select order
            "",   # Don't test connectivity to all providers (default=False)
            "n",  # Don't write API keys to .env for this test
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard(allow_network=True)  # Enable real network calls
            
            with patch('builtins.input', side_effect=mock_responses):
                with patch('sys.stdin.isatty', return_value=True):
                    result = wizard.run_interactive_setup(env_path)
            
            # Should return multi-provider configuration
            assert result.provider == "auto"
            assert "ollama" in result.auto_select_order
            
            # Should write configuration without API keys
            content = env_path.read_text()
            assert "AI_PROVIDER=auto" in content
            assert "AI_AUTO_SELECT_ORDER=" in content
            assert "OLLAMA_BASE_URL=http://localhost:11434/v1" in content
            assert "OLLAMA_MODEL=llama3.1" in content
    
    def test_integration_connectivity_probe_with_real_endpoints(self):
        """Test connectivity probing with real endpoints."""
        # Skip if network not explicitly allowed
        if not os.getenv("ALLOW_NETWORK") and not os.getenv("RUN_INTEGRATION"):
            pytest.skip("Network access not enabled. Set ALLOW_NETWORK=1 or RUN_INTEGRATION=1")
        
        wizard = SetupWizard(allow_network=True)
        
        # Test a real public endpoint that should be reachable
        result = wizard._probe_connection(
            provider="openrouter", 
            base_url="https://openrouter.ai/api/v1",
            api_key="fake-key-for-testing"
        )
        
        # Should get a meaningful response (likely 401 for bad API key, but not connection error)
        assert result.provider == "openrouter"
        assert result.base_url == "https://openrouter.ai/api/v1"
        assert result.status_code is not None  # Should get a HTTP response
        assert "authentication" in result.message.lower() or result.success
    
    def test_integration_local_provider_connectivity(self):
        """Test local provider connectivity (ollama)."""
        # This test works even without network access as it tests local endpoints
        wizard = SetupWizard(allow_network=True)
        
        # Test ollama endpoint (likely not running, should fail gracefully)
        result = wizard._probe_connection(
            provider="ollama", 
            base_url="http://localhost:11434/v1"
        )
        
        # Should handle connection failure gracefully
        assert result.provider == "ollama"
        assert result.base_url == "http://localhost:11434/v1"
        assert not result.success  # Ollama probably not running
        assert "connection" in result.message.lower() or "refused" in result.message.lower()
    
    def test_integration_network_policy_enforcement(self):
        """Test that network policy is properly enforced."""
        wizard_with_network = SetupWizard(allow_network=True)
        wizard_without_network = SetupWizard(allow_network=False)
        
        # Test with network disabled
        result_no_network = wizard_without_network._probe_connection(
            provider="openai",
            base_url="https://api.openai.com/v1",
            api_key="fake-key"
        )
        
        assert not result_no_network.success
        assert "blocked by default" in result_no_network.message
        assert result_no_network.response_time_ms is None
        
        # Test with network enabled (but don't actually make calls if integration disabled)
        if os.getenv("ALLOW_NETWORK") or os.getenv("RUN_INTEGRATION"):
            result_with_network = wizard_with_network._probe_connection(
                provider="openai",
                base_url="https://api.openai.com/v1", 
                api_key="fake-key"
            )
            
            # Should attempt real connection (probably get 401 auth error)
            assert result_with_network.provider == "openai"
            assert result_with_network.status_code is not None or "connection" in result_with_network.message.lower()
    
    def test_integration_setup_wizard_with_real_env_file(self):
        """Test setup wizard with real .env file interactions."""
        # Skip if network not explicitly allowed
        if not os.getenv("ALLOW_NETWORK") and not os.getenv("RUN_INTEGRATION"):
            pytest.skip("Network access not enabled. Set ALLOW_NETWORK=1 or RUN_INTEGRATION=1")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            
            # Create existing .env with some content
            existing_content = """# Existing configuration
EXISTING_VAR=value
UNRELATED_SETTING=keep_this

# Old AI config
OPENAI_API_KEY=old-key
"""
            env_path.write_text(existing_content)
            
            # Mock responses for single provider setup
            mock_responses = [
                "1",  # Choose single provider mode  
                "6",  # Choose openai
                "sk-new-test-key",  # New API key
                "",   # Default base URL
                "",   # Default model
                "",   # Don't test connectivity (default=False)
                "y",  # Write API key to .env
            ]
            
            wizard = SetupWizard(allow_network=True)
            
            with patch('builtins.input', side_effect=mock_responses):
                with patch('sys.stdin.isatty', return_value=True):
                    result = wizard.run_interactive_setup(env_path)
            
            # Should preserve existing content and update AI config
            content = env_path.read_text()
            
            # Should preserve comments and unrelated vars
            assert "# Existing configuration" in content
            assert "EXISTING_VAR=value" in content
            assert "UNRELATED_SETTING=keep_this" in content
            
            # Should update AI provider config
            assert "AI_PROVIDER=openai" in content
            assert "OPENAI_API_KEY=sk-new-test-key" in content
            
            # Should create backup
            backup_path = Path(tmp_dir) / ".env.bak"
            assert backup_path.exists()
            assert backup_path.read_text() == existing_content
    
    def test_integration_non_interactive_mode(self):
        """Test non-interactive setup mode with network access."""
        wizard = SetupWizard(allow_network=True)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            
            result = wizard.run_non_interactive_setup(
                env_path,
                mode=SetupMode.SINGLE_PROVIDER,
                provider="groq",
                model="llama3-70b-8192",
                api_key="gsk-integration-test-key"
            )
            
            # Should return correct configuration
            assert result.provider == "groq"
            assert result.model == "llama3-70b-8192"
            assert result.api_key == "gsk-integration-test-key"
            assert result.base_url == "https://api.groq.com/openai/v1"
            
            # Should write to .env file
            content = env_path.read_text()
            assert "AI_PROVIDER=groq" in content
            assert "GROQ_API_KEY=gsk-integration-test-key" in content
            assert "GROQ_MODEL=llama3-70b-8192" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
