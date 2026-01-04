#!/usr/bin/env python3
"""
Tests for fastchat_setup.py script.

Tests the FastChat setup helper functionality including detection,
configuration generation, and interactive setup.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add scripts to path for imports
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)


class TestFastChatSetupHelper:
    """Test FastChat setup helper functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_fastchat_setup_helper_initialization(self):
        """Test FastChatSetupHelper initialization."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        
        assert helper.default_ports == [8000, 8001, 7860, 5000, 5001]
        assert "/v1/models" in helper.health_endpoints
        assert "/models" in helper.health_endpoints
    
    def test_check_fastchat_installation_found(self):
        """Test FastChat installation detection when found."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        
        # Mock import fastchat
        with patch.dict('sys.modules', {'fastchat': Mock(__version__='1.0.0')}):
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
                      Mock(__version__='1.0.0') if name == 'fastchat' else ImportError):
                installed, info = helper.check_fastchat_installation()
        
        # Test with actual import simulation
        with patch('builtins.__import__') as mock_import:
            mock_fastchat = Mock()
            mock_fastchat.__version__ = '1.0.0'
            mock_import.return_value = mock_fastchat
            
            installed, info = helper.check_fastchat_installation()
            assert installed is True
            assert "FastChat v1.0.0" in info
    
    def test_check_fastchat_installation_not_found(self):
        """Test FastChat installation detection when not found."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        
        with patch('builtins.__import__', side_effect=ImportError("No module")):
            installed, info = helper.check_fastchat_installation()
        
        assert installed is False
        assert info == "FastChat not installed"
    
    @patch('requests.get')
    def test_check_fastchat_running_found(self, mock_get):
        """Test FastChat running detection when found."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        running, info, url = helper.check_fastchat_running()
        
        assert running is True
        assert "FastChat running at" in info
        assert url.startswith("http://")
    
    @patch('requests.get')
    def test_check_fastchat_running_not_found(self, mock_get):
        """Test FastChat running detection when not found."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        
        # Mock failed response
        mock_get.side_effect = Exception("Connection failed")
        
        running, info, url = helper.check_fastchat_running()
        
        assert running is False
        assert info == "FastChat server not found"
        assert url == ""
    
    @patch('requests.get')
    def test_test_fastchat_api_success(self, mock_get):
        """Test FastChat API testing success."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        base_url = "http://127.0.0.1:8000"
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "vicuna-7b-v1.5"},
                {"id": "llama-2-7b"}
            ]
        }
        mock_get.return_value = mock_response
        
        success, info = helper.test_fastchat_api(base_url)
        
        assert success is True
        assert "API working" in info
        assert "vicuna-7b-v1.5" in info
    
    @patch('requests.get')
    def test_test_fastchat_api_no_models(self, mock_get):
        """Test FastChat API testing with no models."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        base_url = "http://127.0.0.1:8000"
        
        # Mock API response with no models
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response
        
        success, info = helper.test_fastchat_api(base_url)
        
        assert success is False
        assert "no models found" in info
    
    @patch('requests.get')
    def test_test_fastchat_api_failure(self, mock_get):
        """Test FastChat API testing failure."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        base_url = "http://127.0.0.1:8000"
        
        # Mock failed API response
        mock_get.side_effect = Exception("API error")
        
        success, info = helper.test_fastchat_api(base_url)
        
        assert success is False
        assert "API test error" in info
    
    def test_generate_env_config(self):
        """Test environment configuration generation."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        base_url = "http://127.0.0.1:8000"
        api_key = "test-key"
        
        config = helper.generate_env_config(base_url, api_key)
        
        assert "AI_PROVIDER=openai_compatible" in config
        assert f"AI_BASE_URL={base_url}" in config
        assert f"AI_API_KEY={api_key}" in config
        assert "AI_MODEL=vicuna-7b-v1.5" in config
    
    def test_generate_setup_commands(self):
        """Test setup commands generation."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        base_url = "http://127.0.0.1:8000"
        
        commands = helper.generate_setup_commands(base_url)
        
        assert any("export AI_PROVIDER=openai_compatible" in cmd for cmd in commands)
        assert any(f"export AI_BASE_URL={base_url}" in cmd for cmd in commands)
        assert any("$env:AI_PROVIDER='openai_compatible'" in cmd for cmd in commands)
    
    def test_start_fastchat_server(self):
        """Test FastChat server startup guidance."""
        from fastchat_setup import FastChatSetupHelper
        from io import StringIO
        import sys
        
        helper = FastChatSetupHelper()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        result = helper.start_fastchat_server(
            model_path="/path/to/model",
            host="127.0.0.1",
            port=8000
        )
        
        sys.stdout = sys.__stdout__  # Restore stdout
        
        output = captured_output.getvalue()
        assert result is True
        assert "FastChat Server Setup Guidance" in output
        assert "/path/to/model" in output
        assert "--host 127.0.0.1" in output
        assert "--port 8000" in output
    
    @patch('requests.get')
    def test_troubleshoot_connection(self, mock_get):
        """Test connection troubleshooting."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        base_url = "http://127.0.0.1:8000"
        
        # Mock connection error
        mock_get.side_effect = Exception("Connection failed")
        
        issues = helper.troubleshoot_connection(base_url)
        
        assert len(issues) > 0
        assert any("Cannot connect to server" in issue for issue in issues)
        assert any("Make sure FastChat API server is running" in issue for issue in issues)
    
    @patch('builtins.input')
    @patch('builtins.__import__')
    @patch('requests.get')
    def test_run_diagnostic_success(self, mock_get, mock_import, mock_input):
        """Test successful diagnostic run."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        
        # Mock FastChat installation
        mock_fastchat = Mock()
        mock_fastchat.__version__ = '1.0.0'
        mock_import.return_value = mock_fastchat
        
        # Mock running server
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "vicuna-7b-v1.5"}]
        }
        mock_get.return_value = mock_response
        
        # Capture stdout
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        
        result = helper.run_diagnostic()
        
        sys.stdout = sys.__stdout__  # Restore stdout
        
        assert result is True
        
        output = captured_output.getvalue()
        assert "FastChat v1.0.0" in output
        assert "API working" in output
    
    @patch('builtins.input')
    @patch('subprocess.run')
    @patch('requests.get')
    def test_interactive_setup_success(self, mock_get, mock_subprocess, mock_input):
        """Test successful interactive setup."""
        from fastchat_setup import FastChatSetupHelper
        
        helper = FastChatSetupHelper()
        
        # Mock user inputs
        mock_input.side_effect = ['y', 'y']  # Install FastChat, save config
        
        # Mock subprocess for installation
        mock_subprocess.return_value = Mock(returncode=0)
        
        # Mock running server
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "vicuna-7b-v1.5"}]
        }
        mock_get.return_value = mock_response
        
        # Create mock .env file
        env_file = self.temp_dir / ".env"
        env_file.write_text("# Existing config\n")
        
        with patch('pathlib.Path.cwd', return_value=self.temp_dir):
            result = helper.interactive_setup()
        
        assert result is True
    
    def test_cli_help(self):
        """Test CLI help functionality."""
        result = subprocess.run(
            [sys.executable, 'scripts/fastchat_setup.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "FastChat setup and diagnostic tool" in result.stdout
        assert "--diagnostic" in result.stdout
        assert "--interactive" in result.stdout
    
    @patch('fastchat_setup.FastChatSetupHelper.run_diagnostic')
    def test_main_function_default(self, mock_diagnostic):
        """Test main function default behavior."""
        from fastchat_setup import main
        
        mock_diagnostic.return_value = True
        
        with patch('sys.argv', ['fastchat_setup.py']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)
    
    @patch('fastchat_setup.FastChatSetupHelper.check_fastchat_running')
    def test_main_function_check(self, mock_check):
        """Test main function with --check option."""
        from fastchat_setup import main
        
        mock_check.return_value = (True, "FastChat running", "http://127.0.0.1:8000")
        
        with patch('sys.argv', ['fastchat_setup.py', '--check']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    pytest.main([__file__])
