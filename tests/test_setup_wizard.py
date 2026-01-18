"""
Tests for setup/wizard.py module.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open, call, MagicMock
from pathlib import Path

from ai_utilities.setup.wizard import (
    SetupWizard, SetupMode, SetupResult, run_setup_wizard
)


class TestSetupMode:
    """Test SetupMode enum."""
    
    def test_setup_mode_values(self):
        """Test SetupMode enum values."""
        assert SetupMode.NORMAL.value == "normal"
        assert SetupMode.ENHANCED.value == "enhanced"
        assert SetupMode.IMPROVED.value == "improved"
    
    def test_setup_mode_creation(self):
        """Test creating SetupMode from string."""
        assert SetupMode("normal") == SetupMode.NORMAL
        assert SetupMode("enhanced") == SetupMode.ENHANCED
        assert SetupMode("improved") == SetupMode.IMPROVED


class TestSetupResult:
    """Test SetupResult dataclass."""
    
    def test_setup_result_creation(self):
        """Test SetupResult creation."""
        result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            dotenv_lines=["OPENAI_API_KEY=test-key"]
        )
        
        assert result.provider == "openai"
        assert result.api_key == "test-key"
        assert result.base_url == "https://api.openai.com/v1"
        assert result.model == "gpt-3.5-turbo"
        assert result.dotenv_lines == ["OPENAI_API_KEY=test-key"]
    
    def test_setup_result_with_optional_fields(self):
        """Test SetupResult with optional fields as None."""
        result = SetupResult(
            provider="ollama",
            api_key=None,
            base_url="http://localhost:11434/v1",
            model=None,
            dotenv_lines=[]
        )
        
        assert result.provider == "ollama"
        assert result.api_key is None
        assert result.base_url == "http://localhost:11434/v1"
        assert result.model is None
        assert result.dotenv_lines == []


class TestSetupWizard:
    """Test SetupWizard class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.wizard = SetupWizard()
    
    def test_wizard_initialization(self):
        """Test SetupWizard initialization."""
        assert isinstance(self.wizard.providers, dict)
        assert "openai" in self.wizard.providers
        assert "groq" in self.wizard.providers
        assert "together" in self.wizard.providers
        assert "openrouter" in self.wizard.providers
        assert "openai_compatible" in self.wizard.providers
        assert "ollama" in self.wizard.providers
        
        # Check provider structure
        openai_config = self.wizard.providers["openai"]
        assert openai_config["name"] == "OpenAI"
        assert openai_config["default_model"] == "gpt-3.5-turbo"
        assert openai_config["requires_api_key"] is True
        assert openai_config["base_url"] == "https://api.openai.com/v1"
    
    def test_is_interactive_true(self):
        """Test interactive detection when TTY is available."""
        with patch('sys.stdin.isatty', return_value=True):
            assert self.wizard._is_interactive() is True
    
    def test_is_interactive_false(self):
        """Test interactive detection when TTY is not available."""
        with patch('sys.stdin.isatty', return_value=False):
            assert self.wizard._is_interactive() is False
    
    def test_prompt_with_default(self):
        """Test prompting with default value."""
        with patch('builtins.input', return_value=''):
            result = self.wizard._prompt("Enter value", "default")
            assert result == "default"
        
        with patch('builtins.input', return_value='custom'):
            result = self.wizard._prompt("Enter value", "default")
            assert result == "custom"
    
    def test_prompt_without_default(self):
        """Test prompting without default value."""
        with patch('builtins.input', return_value='user_input'):
            result = self.wizard._prompt("Enter value")
            assert result == "user_input"
    
    def test_prompt_keyboard_interrupt(self):
        """Test prompt handling keyboard interrupt."""
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            with pytest.raises(KeyboardInterrupt):
                self.wizard._prompt("Enter value")
    
    def test_prompt_eof_error(self):
        """Test prompt handling EOF error."""
        with patch('builtins.input', side_effect=EOFError):
            with pytest.raises(EOFError):
                self.wizard._prompt("Enter value")
    
    def test_prompt_choice_with_default(self):
        """Test prompting choice with default selection."""
        choices = ["Option 1", "Option 2", "Option 3"]
        
        # Test default selection (empty input)
        with patch('builtins.input', return_value=''):
            result = self.wizard._prompt_choice("Choose", choices, "Option 1")
            assert result == "Option 1"
        
        # Test explicit selection
        with patch('builtins.input', return_value='2'):
            result = self.wizard._prompt_choice("Choose", choices, "Option 1")
            assert result == "Option 2"
    
    def test_prompt_choice_invalid_then_valid(self):
        """Test prompting choice with invalid input then valid."""
        choices = ["Option 1", "Option 2", "Option 3"]
        
        with patch('builtins.input', side_effect=['invalid', '2']):
            result = self.wizard._prompt_choice("Choose", choices)
            assert result == "Option 2"
    
    def test_select_mode_with_provided_mode(self):
        """Test selecting mode when mode is provided."""
        result = self.wizard._select_mode(SetupMode.ENHANCED)
        assert result == SetupMode.ENHANCED
    
    def test_select_mode_non_interactive(self):
        """Test selecting mode in non-interactive environment."""
        with patch.object(self.wizard, '_is_interactive', return_value=False):
            with pytest.raises(RuntimeError, match="Mode selection requires interactive environment"):
                self.wizard._select_mode(None)
    
    def test_select_provider_normal_mode(self):
        """Test provider selection in normal mode."""
        result = self.wizard._select_provider(SetupMode.NORMAL)
        assert result == "openai"
    
    def test_select_provider_enhanced_mode(self):
        """Test provider selection in enhanced mode."""
        with patch.object(self.wizard, '_is_interactive', return_value=True):
            with patch.object(self.wizard, '_prompt_choice', return_value="Groq - Fast inference with Groq API"):
                result = self.wizard._select_provider(SetupMode.ENHANCED)
                assert result == "groq"
    
    def test_run_wizard_non_interactive_no_mode(self):
        """Test running wizard in non-interactive mode without specifying mode."""
        with pytest.raises(ValueError, match="Mode must be specified in non-interactive mode"):
            self.wizard.run_wizard(non_interactive=True, mode=None)
    
    def test_run_wizard_non_interactive_with_mode(self):
        """Test running wizard in non-interactive mode with mode."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            result = self.wizard.run_wizard(
                mode=SetupMode.NORMAL,
                non_interactive=True,
                dry_run=True
            )
            
            assert result.provider == "openai"
            assert result.api_key == "test-key"
            assert result.base_url == "https://api.openai.com/v1"
            assert result.model == "gpt-3.5-turbo"
            assert isinstance(result.dotenv_lines, list)
    
    def test_run_wizard_non_interactive_env_var_fallback(self):
        """Test running wizard with AI_API_KEY fallback."""
        with patch.dict(os.environ, {'AI_API_KEY': 'fallback-key'}, clear=True):
            result = self.wizard.run_wizard(
                mode=SetupMode.NORMAL,
                non_interactive=True,
                dry_run=True
            )
            
            assert result.api_key == "fallback-key"
    
    def test_run_wizard_non_interactive_no_api_key(self):
        """Test running wizard without API key in environment."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.wizard.run_wizard(
                mode=SetupMode.NORMAL,
                non_interactive=True,
                dry_run=True
            )
            
            assert result.api_key is None
    
    def test_run_wizard_dry_run(self):
        """Test running wizard in dry run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = os.path.join(temp_dir, ".env")
            with patch('builtins.print') as mock_print:
                with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                    result = self.wizard.run_wizard(
                        mode=SetupMode.NORMAL,
                        non_interactive=True,
                        dry_run=True,
                        dotenv_path=dotenv_path
                    )
                    
                    # Should print dry run content
                    mock_print.assert_any_call("\n=== Dry Run: .env content ===")
                    # Should not write file
                    assert not os.path.exists(dotenv_path)
    
    def test_run_wizard_write_dotenv(self):
        """Test running wizard and writing .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = os.path.join(temp_dir, ".env")
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                result = self.wizard.run_wizard(
                    mode=SetupMode.NORMAL,
                    non_interactive=True,
                    dotenv_path=dotenv_path
                )
                
                # Should write file
                assert os.path.exists(dotenv_path)
                
                # Check content
                with open(dotenv_path, 'r') as f:
                    content = f.read()
                    assert "AI_API_KEY=test-key" in content
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_dotenv_creation(self, mock_file):
        """Test .env file writing."""
        dotenv_path = Path("/some/path/.env")
        lines = ["KEY=value", "OTHER=test"]
        
        self.wizard._write_dotenv(dotenv_path, lines)
        
        mock_file.assert_called_once_with(dotenv_path, 'w')
        # Each line is written separately with newline
        expected_calls = [
            call('KEY=value\n'),
            call('OTHER=test\n')
        ]
        mock_file().write.assert_has_calls(expected_calls)
    
    def test_build_dotenv_content_openai(self):
        """Test building .env content for OpenAI."""
        result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            dotenv_lines=[]
        )
        
        lines = self.wizard._build_dotenv_content(result)
        
        assert "AI_API_KEY=test-key" in lines
        assert "AI_PROVIDER=openai" in lines
        assert "AI_MODEL=gpt-3.5-turbo" in lines
    
    def test_build_dotenv_content_custom_base_url(self):
        """Test building .env content with custom base URL."""
        result = SetupResult(
            provider="openai_compatible",
            api_key="custom-key",
            base_url="https://custom.example.com/v1",
            model="custom-model",
            dotenv_lines=[]
        )
        
        lines = self.wizard._build_dotenv_content(result)
        
        assert "AI_API_KEY=custom-key" in lines
        assert "AI_PROVIDER=openai_compatible" in lines
        assert "AI_BASE_URL=https://custom.example.com/v1" in lines
        assert "AI_MODEL=custom-model" in lines
    
    def test_build_dotenv_content_no_api_key(self):
        """Test building .env content without API key."""
        result = SetupResult(
            provider="ollama",
            api_key=None,
            base_url="http://localhost:11434/v1",
            model=None,
            dotenv_lines=[]
        )
        
        lines = self.wizard._build_dotenv_content(result)
        
        assert "AI_PROVIDER=ollama" in lines
        # Base URL is fixed for ollama, so not included in dotenv
        assert "AI_BASE_URL" not in str(lines)
        # Should not include any API key lines
        api_key_lines = [line for line in lines if "API_KEY" in line]
        assert len(api_key_lines) == 0


class TestRunSetupWizard:
    """Test the module-level run_setup_wizard function."""
    
    def test_run_setup_wizard_function(self):
        """Test the convenience function."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            result = run_setup_wizard(
                mode=SetupMode.NORMAL,
                non_interactive=True,
                dry_run=True
            )
            
            assert isinstance(result, SetupResult)
            assert result.provider == "openai"
            assert result.api_key == "test-key"
    
    def test_run_setup_wizard_parameters_passed_through(self):
        """Test that parameters are passed through to wizard."""
        with patch('ai_utilities.setup.wizard.SetupWizard') as mock_wizard_class:
            mock_wizard = MagicMock()
            mock_wizard_class.return_value = mock_wizard
            mock_result = MagicMock()
            mock_wizard.run_wizard.return_value = mock_result
            
            result = run_setup_wizard(
                mode=SetupMode.ENHANCED,
                dotenv_path="custom.env",
                dry_run=True,
                non_interactive=True
            )
            
            mock_wizard.run_wizard.assert_called_once_with(
                mode=SetupMode.ENHANCED,
                dotenv_path="custom.env",
                dry_run=True,
                non_interactive=True
            )
            assert result == mock_result


class TestSetupWizardEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.wizard = SetupWizard()
    
    def test_provider_config_structure(self):
        """Test that all provider configs have required fields."""
        required_fields = ["name", "description", "default_model", "requires_api_key", "base_url"]
        
        for provider_id, config in self.wizard.providers.items():
            for field in required_fields:
                assert field in config, f"Provider {provider_id} missing field {field}"
    
    def test_openai_compatible_provider_config(self):
        """Test OpenAI compatible provider has nullable defaults."""
        config = self.wizard.providers["openai_compatible"]
        assert config["default_model"] is None
        assert config["base_url"] is None
        assert config["requires_api_key"] is False
    
    def test_ollama_provider_config(self):
        """Test Ollama provider config."""
        config = self.wizard.providers["ollama"]
        assert config["default_model"] is None
        assert config["requires_api_key"] is False
        assert config["base_url"] == "http://localhost:11434/v1"
    
    def test_setup_mode_string_conversion(self):
        """Test SetupMode string conversion edge cases."""
        # Test case sensitivity
        with pytest.raises(ValueError):
            SetupMode("Normal")  # Should be lowercase
        
        # Test invalid value
        with pytest.raises(ValueError):
            SetupMode("invalid")
    
    def test_prompt_choice_empty_choices(self):
        """Test prompting choice with empty choices list."""
        with pytest.raises(ValueError):
            self.wizard._prompt_choice("Choose", [])
    
    def test_prompt_choice_single_choice(self):
        """Test prompting choice with single option."""
        choices = ["Only Option"]
        
        with patch('builtins.input', return_value='1'):
            result = self.wizard._prompt_choice("Choose", choices)
            assert result == "Only Option"
