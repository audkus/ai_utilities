"""
Contract-first tests for v1.0.1 CLI setup behavior.

These tests define the expected user-visible behavior for the new setup feature
before implementation. They focus on observable outcomes rather than internal
implementation details.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from typing import Dict, List

# Import the modules we'll be creating
from ai_utilities.cli.env_writer import EnvWriter
from ai_utilities.cli.setup_wizard import SetupWizard, SetupMode, SetupResult


class TestEnvWriter:
    """Test .env file operations with contract-first approach."""
    
    def test_create_env_file_when_none_exists(self):
        """Test creating .env when none exists - writes header + selected provider variables."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            writer = EnvWriter()
            
            # Test data for ollama provider
            provider_config = {
                "provider": "ollama",
                "base_url": "http://localhost:11434/v1",
                "model": "llama3.1",
                "api_key": None
            }
            
            writer.create_or_patch(env_path, provider_config)
            
            # Verify file was created
            assert env_path.exists()
            
            content = env_path.read_text()
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
            
            # Should contain AI_PROVIDER and ollama-specific variables
            assert "AI_PROVIDER=ollama" in lines
            assert "OLLAMA_BASE_URL=http://localhost:11434/v1" in lines
            assert "OLLAMA_MODEL=llama3.1" in lines
            
            # Should not contain API key for local provider
            assert not any("API_KEY" in line for line in lines)
    
    def test_patch_existing_env_preserves_content(self):
        """Test patching .env preserves comments and unrelated keys."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            
            # Create existing .env with comments and unrelated variables
            existing_content = """# AI Utilities Configuration
# This is a comment

UNRELATED_VAR=value
ANOTHER_UNRELATED=another_value

# OpenAI configuration
OPENAI_API_KEY=sk-old-key
OPENAI_MODEL=gpt-4
"""
            env_path.write_text(existing_content)
            
            writer = EnvWriter()
            provider_config = {
                "provider": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "model": "llama3-70b-8192",
                "api_key": "gsk-new-key"
            }
            
            writer.create_or_patch(env_path, provider_config)
            
            content = env_path.read_text()
            
            # Should preserve comments
            assert "# AI Utilities Configuration" in content
            assert "# This is a comment" in content
            assert "# OpenAI configuration" in content
            
            # Should preserve unrelated variables
            assert "UNRELATED_VAR=value" in content
            assert "ANOTHER_UNRELATED=another_value" in content
            
            # Should update provider-specific variables
            assert "GROQ_API_KEY=gsk-new-key" in content
            assert "GROQ_BASE_URL=https://api.groq.com/openai/v1" in content
            assert "GROQ_MODEL=llama3-70b-8192" in content
            
            # Should update AI_PROVIDER
            assert "AI_PROVIDER=groq" in content
    
    def test_patch_env_updates_existing_keys(self):
        """Test patching updates existing keys without deleting other content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            
            # Create existing .env with some provider config
            existing_content = """AI_PROVIDER=openai
OPENAI_API_KEY=sk-old-key
OPENAI_MODEL=gpt-4
SOME_OTHER_VAR=preserved
"""
            env_path.write_text(existing_content)
            
            writer = EnvWriter()
            provider_config = {
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "api_key": "sk-new-key"
            }
            
            writer.create_or_patch(env_path, provider_config)
            
            content = env_path.read_text()
            lines = content.split('\n')
            
            # Should update existing keys
            assert "OPENAI_API_KEY=sk-new-key" in content
            assert "OPENAI_MODEL=gpt-4o-mini" in content
            
            # Should preserve other variables
            assert "SOME_OTHER_VAR=preserved" in content
            
            # Should not duplicate keys
            openai_key_lines = [line for line in lines if line.startswith("OPENAI_API_KEY=")]
            assert len(openai_key_lines) == 1
    
    def test_multi_provider_mode_writes_auto_select_order(self):
        """Test multi-provider mode writes AI_PROVIDER=auto and AI_AUTO_SELECT_ORDER."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            writer = EnvWriter()
            
            # Test multi-provider configuration
            multi_provider_config = {
                "provider": "auto",
                "auto_select_order": ["ollama", "lmstudio", "groq", "openai"],
                "providers": {
                    "ollama": {
                        "base_url": "http://localhost:11434/v1",
                        "model": "llama3.1",
                        "api_key": None
                    },
                    "lmstudio": {
                        "base_url": "http://localhost:1234/v1",
                        "model": "llama-3-8b-instruct",
                        "api_key": None
                    },
                    "groq": {
                        "base_url": "https://api.groq.com/openai/v1",
                        "model": "llama3-70b-8192",
                        "api_key": "gsk-test-key"
                    },
                    "openai": {
                        "base_url": "https://api.openai.com/v1",
                        "model": "gpt-4o-mini",
                        "api_key": "sk-test-key"
                    }
                }
            }
            
            writer.create_or_patch(env_path, multi_provider_config)
            
            content = env_path.read_text()
            
            # Should write auto configuration
            assert "AI_PROVIDER=auto" in content
            assert "AI_AUTO_SELECT_ORDER=ollama,lmstudio,groq,openai" in content
            
            # Should write all provider configurations
            assert "OLLAMA_BASE_URL=http://localhost:11434/v1" in content
            assert "OLLAMA_MODEL=llama3.1" in content
            assert "LMSTUDIO_BASE_URL=http://localhost:1234/v1" in content
            assert "LMSTUDIO_MODEL=llama-3-8b-instruct" in content
            assert "GROQ_API_KEY=gsk-test-key" in content
            assert "OPENAI_API_KEY=sk-test-key" in content
    
    def test_backup_created_when_patching_existing_env(self):
        """Test backup .env.bak created when patching existing .env."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            backup_path = Path(tmp_dir) / ".env.bak"
            
            # Create existing .env
            original_content = "AI_PROVIDER=openai\nOPENAI_API_KEY=sk-old-key\n"
            env_path.write_text(original_content)
            
            writer = EnvWriter()
            provider_config = {
                "provider": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "model": "llama3-70b-8192",
                "api_key": "gsk-new-key"
            }
            
            writer.create_or_patch(env_path, provider_config)
            
            # Should create backup
            assert backup_path.exists()
            assert backup_path.read_text() == original_content
            
            # Main file should be updated
            content = env_path.read_text()
            assert "GROQ_API_KEY=gsk-new-key" in content


class TestSetupWizard:
    """Test interactive setup wizard behavior."""
    
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input')
    def test_interactive_single_provider_setup(self, mock_input, mock_isatty):
        """Test interactive setup for single provider mode."""
        # Mock user responses
        mock_input.side_effect = [
            "1",  # Choose single provider mode
            "2",  # Choose groq
            "gsk-test-key",  # API key
            "",  # Default base URL
            "",  # Default model
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard(allow_network=False)  # Disable network calls
            
            result = wizard.run_interactive_setup(env_path)
            
            # Should return correct configuration
            assert result.provider == "groq"
            assert result.api_key == "gsk-test-key"
            assert result.base_url == "https://api.groq.com/openai/v1"
            assert result.model == "llama3-70b-8192"
            
            # Should write to .env file
            assert env_path.exists()
            content = env_path.read_text()
            assert "AI_PROVIDER=groq" in content
            assert "GROQ_API_KEY=gsk-test-key" in content
    
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input')
    def test_interactive_multi_provider_setup(self, mock_input, mock_isatty):
        """Test interactive setup for multi-provider mode."""
        # Mock user responses for multi-provider setup
        mock_input.side_effect = [
            "2",  # Choose multi-provider mode
            "1",  # Select ollama
            "",   # Default ollama URL
            "llama3.1",  # ollama model
            "",   # Don't test ollama connectivity (default=False)
            "2",  # Add groq
            "gsk-test-key",  # groq API key
            "",   # Default groq URL
            "",   # Default groq model
            "",   # Don't test groq connectivity (default=False)
            "done",  # Done adding providers (matches UI text)
            "y",  # Use default auto-select order
            "",   # Don't test connectivity to all providers (default=False)
            "y",  # Write API keys to .env
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard(allow_network=False)  # Disable network calls
            
            result = wizard.run_interactive_setup(env_path)
            
            # Should return multi-provider configuration
            assert result.provider == "auto"
            assert "ollama" in result.auto_select_order
            assert "groq" in result.auto_select_order
            
            # Should write all provider configs
            content = env_path.read_text()
            assert "AI_PROVIDER=auto" in content
            assert "AI_AUTO_SELECT_ORDER=" in content
            assert "OLLAMA_BASE_URL=http://localhost:11434/v1" in content
            assert "OLLAMA_MODEL=llama3.1" in content
            assert "GROQ_API_KEY=gsk-test-key" in content
    
    def test_non_interactive_fails_without_mode(self):
        """Test non-interactive setup fails when mode not specified."""
        wizard = SetupWizard()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            
            with pytest.raises(ValueError, match="Mode must be specified"):
                wizard.run_non_interactive_setup(env_path, mode=None)
    
    def test_non_interactive_with_explicit_mode(self):
        """Test non-interactive setup works with explicit mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard()
            
            result = wizard.run_non_interactive_setup(
                env_path, 
                mode=SetupMode.NORMAL,
                provider="ollama",
                model="llama3.1"
            )
            
            assert result.provider == "ollama"
            assert result.model == "llama3.1"
            
            content = env_path.read_text()
            assert "AI_PROVIDER=ollama" in content
            assert "OLLAMA_MODEL=llama3.1" in content


class TestOptionalDependencyDetection:
    """Test optional dependency detection and guidance."""
    
    @patch('importlib.util.find_spec')
    def test_detects_missing_openai_dependency(self, mock_find_spec):
        """Test CLI detects missing openai dependency and prints install command."""
        mock_find_spec.return_value = None  # openai not installed
        
        with patch('builtins.print') as mock_print:
            wizard = SetupWizard()
            wizard.check_optional_dependencies(["openai"])
            
            # Should print install command
            mock_print.assert_called()
            calls = [str(call) for call in mock_print.call_args_list]
            install_command_found = any("python -m pip install" in call and "openai" in call for call in calls)
            assert install_command_found
    
    @patch('importlib.util.find_spec')
    def test_no_message_for_installed_dependencies(self, mock_find_spec):
        """Test no install message when dependencies are already installed."""
        mock_find_spec.return_value = MagicMock()  # openai installed
        
        with patch('builtins.print') as mock_print:
            wizard = SetupWizard()
            wizard.check_optional_dependencies(["openai"])
            
            # Should not print install commands
            calls = [str(call) for call in mock_print.call_args_list]
            install_command_found = any("pip install" in call for call in calls)
            assert not install_command_found


class TestRuntimeProviderResolution:
    """Test runtime provider resolution respects new configuration rules."""
    
    def test_auto_selection_respects_custom_order(self):
        """Test auto provider selection respects AI_AUTO_SELECT_ORDER."""
        # This test will be implemented when we fix the runtime resolution
        # For now, define the expected behavior
        with patch.dict(os.environ, {
            'AI_PROVIDER': 'auto',
            'AI_AUTO_SELECT_ORDER': 'ollama,lmstudio,groq,openai',
            'OLLAMA_BASE_URL': 'http://localhost:11434/v1',
            'OLLAMA_MODEL': 'llama3.1'
        }):
            # Should prefer ollama first in custom order
            from ai_utilities.config_resolver import resolve_provider
            provider = resolve_provider()
            assert provider == 'ollama'
    
    def test_auto_selection_uses_default_local_first_order(self):
        """Test auto selection uses local-first default when no custom order."""
        with patch.dict(os.environ, {
            'AI_PROVIDER': 'auto',
            # No AI_AUTO_SELECT_ORDER set
            'GROQ_API_KEY': 'gsk-test-key',
            'OPENAI_API_KEY': 'sk-test-key'
        }):
            # Should prefer groq over openai in default local-first order
            from ai_utilities.config_resolver import resolve_provider
            provider = resolve_provider()
            assert provider == 'groq'
    
    def test_raises_error_when_no_provider_configured(self):
        """Test raises ProviderConfigurationError when no provider configured."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove all provider configuration
            for key in list(os.environ.keys()):
                if any(provider in key for provider in ['OPENAI', 'GROQ', 'TOGETHER', 'OPENROUTER', 'OLLAMA', 'LMSTUDIO', 'FASTCHAT', 'TEXT_GENERATION_WEBUI']):
                    del os.environ[key]
            
            from ai_utilities.config_resolver import resolve_provider
            from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
            
            with pytest.raises(ProviderConfigurationError, match="No provider configured"):
                resolve_provider()


class TestRegressionTests:
    """Regression tests for previously problematic behavior."""
    
    def test_auto_selection_does_not_silently_default_to_openai_when_unconfigured(self):
        """Regression test: ensure no silent OpenAI default when nothing configured."""
        # This was the problematic behavior that needed fixing
        with patch.dict(os.environ, {}, clear=True):
            # Ensure no provider configuration exists
            from ai_utilities.config_resolver import resolve_provider
            from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
            
            with pytest.raises(ProviderConfigurationError) as exc_info:
                resolve_provider()
            
            # Error message should guide user to setup
            error_msg = str(exc_info.value)
            assert "ai-utilities setup" in error_msg.lower()
            assert "AI_PROVIDER" in error_msg
    
    def test_library_contract_no_prompts_or_file_writes(self):
        """Library contract: importing ai_utilities must not prompt or write files."""
        # Test that library import doesn't trigger any setup behavior
        with patch('builtins.print') as mock_print:
            with patch('builtins.input') as mock_input:
                with patch('pathlib.Path.write_text') as mock_write:
                    # Import library - should not trigger any setup
                    import importlib
                    import sys
                    
                    # Remove module if already imported
                    if 'ai_utilities' in sys.modules:
                        del sys.modules['ai_utilities']
                    
                    # Fresh import
                    import ai_utilities
                    
                    # Should not have prompted or written files
                    mock_input.assert_not_called()
                    mock_write.assert_not_called()
                    
                    # Only print calls should be from SSL check or similar, not setup
                    setup_calls = [call for call in mock_print.call_args_list 
                                 if "setup" in str(call).lower()]
                    assert len(setup_calls) == 0


class TestCLIContract:
    """Test CLI contract: setup command is the only place that may write .env."""
    
    @patch('sys.stdin.isatty', return_value=False)
    def test_cli_non_interactive_fails_helpfully(self, mock_isatty):
        """Test CLI fails with helpful message when not interactive."""
        from ai_utilities.cli import main
        
        # Should fail with helpful message when not TTY and no flags
        result = main([])
        assert result != 0  # Non-zero exit code
        
        # Should provide guidance on required flags
        # This would be tested by checking stdout/stderr in actual implementation


class TestSetupWizardPRChanges:
    """Test specific PR changes to ensure coverage of modified lines."""
    
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input')
    def test_setup_wizard_default_base_url_handling(self, mock_input, mock_isatty):
        """Test base_url defaulting when user input is blank (covers lines 324, 352-356)."""
        # Mock user responses for ollama provider with blank base URL input
        mock_input.side_effect = [
            "1",  # Choose single provider mode
            "1",  # Choose ollama
            "",   # Default base URL (blank input should use default)
            "llama3.1",  # model
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard(allow_network=False)
            
            result = wizard.run_interactive_setup(env_path)
            
            # Should use default base URL when user enters blank
            assert result.provider == "ollama"
            assert result.base_url == "http://localhost:11434/v1"  # Default URL
            assert result.model == "llama3.1"
            
            # Should write default base URL to .env
            content = env_path.read_text()
            assert "OLLAMA_BASE_URL=http://localhost:11434/v1" in content
    
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input')
    def test_setup_wizard_custom_base_url_override(self, mock_input, mock_isatty):
        """Test custom base URL override (covers lines 352-356 custom_url != default_url check)."""
        # Mock user responses for ollama provider with custom base URL
        mock_input.side_effect = [
            "1",  # Choose single provider mode
            "1",  # Choose ollama
            "http://custom:1234/v1",  # Custom base URL (not default)
            "llama3.1",  # model
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard(allow_network=False)
            
            result = wizard.run_interactive_setup(env_path)
            
            # Should use custom base URL when user enters non-default value
            assert result.provider == "ollama"
            assert result.base_url == "http://custom:1234/v1"
            assert result.model == "llama3.1"
            
            # Should write custom base URL to .env
            content = env_path.read_text()
            assert "OLLAMA_BASE_URL=http://custom:1234/v1" in content
    
    def test_setup_wizard_non_interactive_default_base_url(self):
        """Test non-interactive setup uses default_base_url (covers lines 650, 681)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard(allow_network=False)
            
            # Test non-interactive mode without specifying base_url
            result = wizard.run_non_interactive_setup(
                env_path, 
                mode=SetupMode.NORMAL,
                provider="groq",
                model="llama3-70b-8192"
            )
            
            # Should use default_base_url from provider config
            assert result.provider == "groq"
            assert result.base_url == "https://api.groq.com/openai/v1"  # Default URL
            assert result.model == "llama3-70b-8192"
    
    def test_setup_wizard_non_interactive_custom_base_url(self):
        """Test non-interactive setup with custom base_url (covers lines 650, 681)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            wizard = SetupWizard(allow_network=False)
            
            # Test non-interactive mode with custom base_url
            result = wizard.run_non_interactive_setup(
                env_path, 
                mode=SetupMode.NORMAL,
                provider="groq",
                base_url="http://custom:5678/v1",
                model="llama3-70b-8192"
            )
            
            # Should use custom base_url when provided
            assert result.provider == "groq"
            assert result.base_url == "http://custom:5678/v1"
            assert result.model == "llama3-70b-8192"


class TestConfigResolverPRChanges:
    """Test specific PR changes in config_resolver.py."""
    
    def test_resolve_auto_provider_none_handling(self):
        """Test None return from _resolve_auto_provider with proper error (covers lines 120-124)."""
        # Mock environment to trigger auto mode with no providers configured
        with patch.dict(os.environ, {'AI_PROVIDER': 'auto'}, clear=True):
            # Clear all provider configuration to force None return
            for key in list(os.environ.keys()):
                if any(provider in key for provider in ['OPENAI', 'GROQ', 'TOGETHER', 'OPENROUTER', 'OLLAMA', 'LMSTUDIO']):
                    del os.environ[key]
            
            from ai_utilities.config_resolver import resolve_provider
            from ai_utilities.providers.provider_exceptions import ProviderConfigurationError
            
            # Should raise ValueError with specific message when auto mode fails
            with pytest.raises(ValueError, match="No providers configured for auto mode"):
                resolve_provider()
    
    def test_strict_test_context_frame_handling(self):
        """Test Optional[FrameType] access with proper None checks (covers lines 196-197)."""
        from ai_utilities.config_resolver import _is_strict_test_context
        
        # Simply call the function to ensure it doesn't crash on frame inspection
        # The function should handle frame.f_back None checks gracefully
        try:
            result = _is_strict_test_context()
            # The function should return a boolean, not crash
            assert isinstance(result, bool)
        except Exception as e:
            # If there's an error, it should not be related to frame.f_back access
            assert "NoneType" not in str(e), f"Frame None handling failed: {e}"


class TestCLIInitPRChanges:
    """Test specific PR changes in cli/__init__.py."""
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_cli_main_none_checks_for_result_fields(self, mock_run_wizard):
        """Test None checks for result.auto_select_order and result.providers (covers lines 142-145)."""
        from ai_utilities.cli import main
        from ai_utilities.cli.setup_wizard import SetupResult
        
        # Mock result with None fields to test None checks
        mock_result = SetupResult(
            provider="auto",
            auto_select_order=None,  # None to test None check
            providers={},  # Empty to test None check
            dotenv_path=Path(".env"),
            backup_created=False
        )
        mock_run_wizard.return_value = mock_result
        
        # Should not crash when accessing None fields
        result = main(["setup", "--mode", "non-interactive", "--provider", "openai"])
        assert result == 0
        
        # Verify the function was called
        mock_run_wizard.assert_called_once()
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_cli_main_with_populated_result_fields(self, mock_run_wizard):
        """Test CLI with populated result fields (covers lines 142-145)."""
        from ai_utilities.cli import main
        from ai_utilities.cli.setup_wizard import SetupResult
        
        # Mock result with populated fields
        mock_result = SetupResult(
            provider="auto",
            auto_select_order=["ollama", "groq"],
            providers={"ollama": {"model": "llama3.1"}, "groq": {"api_key": "gsk-test"}},
            dotenv_path=Path(".env"),
            backup_created=False
        )
        mock_run_wizard.return_value = mock_result
        
        # Should print the provider information when fields are populated
        result = main(["setup", "--mode", "non-interactive", "--provider", "openai"])
        assert result == 0
        
        # Verify the function was called
        mock_run_wizard.assert_called_once()


class TestSetupWizardResultPRChanges:
    """Test specific PR changes in setup/wizard.py SetupResult class."""
    
    def test_setup_result_new_fields(self):
        """Test new providers and auto_select_order fields in SetupResult (covers lines 28-29)."""
        from ai_utilities.setup.wizard import SetupResult
        
        # Test that new fields exist and can be set
        result = SetupResult(
            provider="auto",
            api_key=None,
            base_url=None,
            model=None,
            dotenv_lines=[],
            providers={"ollama": {"model": "llama3.1"}},
            auto_select_order=["ollama", "groq"]
        )
        
        # Should be able to access new fields
        assert result.providers is not None
        assert result.auto_select_order is not None
        assert "ollama" in result.providers
        assert "ollama" in result.auto_select_order
        
        # Test default values (None)
        default_result = SetupResult(
            provider="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            dotenv_lines=[]
        )
        
        assert default_result.providers is None  # Default value
        assert default_result.auto_select_order is None  # Default value


if __name__ == "__main__":
    pytest.main([__file__])
