"""
test_coverage_wizard.py

Additional tests for setup/wizard.py to improve coverage.
Focuses on uncovered lines and edge cases.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_utilities.setup.wizard import SetupWizard, SetupMode, SetupResult


class TestWizardCoverage:
    """Tests for wizard.py coverage gaps."""
    
    def setup_method(self):
        """Set up test environment."""
        self.wizard = SetupWizard()
    
    def test_wizard_initialization(self):
        """Test SetupWizard initialization."""
        wizard = SetupWizard()
        assert hasattr(wizard, 'providers')
        assert 'openai' in wizard.providers
        assert 'groq' in wizard.providers
    
    def test_is_interactive_true(self):
        """Test _is_interactive returns True in interactive environment."""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            assert self.wizard._is_interactive() is True
    
    def test_is_interactive_false(self):
        """Test _is_interactive returns False in non-interactive environment."""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False
            assert self.wizard._is_interactive() is False
    
    def test_select_mode_with_provided_mode(self):
        """Test _select_mode when mode is provided."""
        result = self.wizard._select_mode(SetupMode.NORMAL)
        assert result == SetupMode.NORMAL
    
    @patch('ai_utilities.setup.wizard.SetupWizard._is_interactive')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_select_mode_non_interactive_error(self, mock_print, mock_input, mock_is_interactive):
        """Test _select_mode raises error in non-interactive environment."""
        mock_is_interactive.return_value = False
        
        with pytest.raises(RuntimeError, match="Mode selection requires interactive environment"):
            self.wizard._select_mode(None)
    
    @patch('ai_utilities.setup.wizard.SetupWizard._is_interactive')
    @patch('ai_utilities.setup.wizard.SetupWizard._prompt_choice')
    @patch('builtins.print')
    def test_select_mode_interactive_success(self, mock_print, mock_prompt_choice, mock_is_interactive):
        """Test _select_mode interactive success."""
        mock_is_interactive.return_value = True
        mock_prompt_choice.return_value = 'enhanced'
        
        result = self.wizard._select_mode(None)
        
        assert result == SetupMode.ENHANCED
        mock_print.assert_any_call("=== AI Utilities Setup Wizard ===\n")
        mock_print.assert_any_call("Choose setup mode:")
    
    def test_get_api_key_not_required(self):
        """Test _get_api_key when API key is not required."""
        result = self.wizard._get_api_key('ollama', SetupMode.NORMAL)  # Ollama doesn't require API key
        assert result is None
    
    def test_get_base_url_with_default(self):
        """Test _get_base_url with default value."""
        result = self.wizard._get_base_url('openai', SetupMode.NORMAL)
        assert result == 'https://api.openai.com/v1'
    
    def test_get_model_with_default(self):
        """Test _get_model with default model."""
        result = self.wizard._get_model('openai', SetupMode.NORMAL, 'https://api.openai.com/v1')
        assert result == 'gpt-3.5-turbo'
    
    def test_build_dotenv_content_openai(self):
        """Test _build_dotenv_content for OpenAI."""
        setup_result = SetupResult(
            provider='openai',
            api_key='test-key',
            base_url='https://api.openai.com/v1',
            model='gpt-4',
            dotenv_lines=[]
        )
        
        lines = self.wizard._build_dotenv_content(setup_result)
        
        assert 'AI_API_KEY=test-key' in lines
        assert 'AI_PROVIDER=openai' in lines
        assert 'AI_MODEL=gpt-4' in lines
    
    def test_build_dotenv_content_openai_compatible(self):
        """Test _build_dotenv_content for OpenAI compatible."""
        setup_result = SetupResult(
            provider='openai_compatible',
            api_key='test-key',
            base_url='https://custom.com/v1',
            model='custom-model',
            dotenv_lines=[]
        )
        
        lines = self.wizard._build_dotenv_content(setup_result)
        
        assert 'AI_API_KEY=test-key' in lines
        assert 'AI_PROVIDER=openai_compatible' in lines
        assert 'AI_BASE_URL=https://custom.com/v1' in lines
        assert 'AI_MODEL=custom-model' in lines
    
    def test_wizard_provider_configs(self):
        """Test that wizard has proper provider configurations."""
        assert 'openai' in self.wizard.providers
        assert 'groq' in self.wizard.providers
        assert 'ollama' in self.wizard.providers
        
        # Check OpenAI config
        openai_config = self.wizard.providers['openai']
        assert openai_config['requires_api_key'] is True
        assert openai_config['default_model'] == 'gpt-3.5-turbo'
        
        # Check Ollama config
        ollama_config = self.wizard.providers['ollama']
        assert ollama_config['requires_api_key'] is False
        assert ollama_config['base_url'] == 'http://localhost:11434/v1'
