#!/usr/bin/env python3
"""
Tests for text_generation_webui_setup.py script.

Tests the Text-Generation-WebUI setup helper functionality including detection,
configuration generation, and interactive setup.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

# Add scripts to path for imports
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)


class TestTextGenerationWebUISetupHelper:
    """Test Text-Generation-WebUI setup helper functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_webui_setup_helper_initialization(self):
        """Test TextGenerationWebUISetupHelper initialization."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        assert 7860 in helper.default_ports
        assert "/v1/models" in helper.api_endpoints
        assert "/api/v1/models" in helper.api_endpoints
        assert helper.webui_port == 7860
    
    def test_check_webui_installation_found(self):
        """Test WebUI installation detection when found."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        # Mock Path.exists() to return True for all calls
        with patch('pathlib.Path.exists', return_value=True):
            installed, info = helper.check_webui_installation()
        
        assert installed is True
        assert "text-generation-webui/" in info
    
    def test_check_webui_installation_not_found(self):
        """Test WebUI installation detection when not found."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        with patch('pathlib.Path.cwd', return_value=self.temp_dir):
            installed, info = helper.check_webui_installation()
        
        assert installed is False
        assert "not found" in info
    
    @patch('requests.get')
    def test_check_webui_running_found_web_interface(self, mock_get):
        """Test WebUI running detection via web interface."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        # Mock successful web interface response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<title>text-generation-webui</title>"
        mock_get.return_value = mock_response
        
        running, info, url = helper.check_webui_running()
        
        assert running is True
        assert "WebUI running" in info
        assert url.startswith("http://")
    
    @patch('requests.get')
    def test_check_webui_running_found_api(self, mock_get):
        """Test WebUI running detection via API."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        # Mock web interface fails, API succeeds
        def side_effect(*args, **kwargs):
            if "/models" in args[0]:
                mock_response = Mock()
                mock_response.status_code = 200
                return mock_response
            else:
                raise Exception("Web interface not found")
        
        mock_get.side_effect = side_effect
        
        running, info, url = helper.check_webui_running()
        
        assert running is True
        assert "API running" in info
    
    @patch('requests.get')
    def test_check_webui_running_not_found(self, mock_get):
        """Test WebUI running detection when not found."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        # Mock failed response with the correct exception type
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")
        
        running, info, url = helper.check_webui_running()
        
        assert running is False
        assert "not found" in info
        assert url == ""
    
    @patch('requests.get')
    def test_test_webui_api_success(self, mock_get):
        """Test WebUI API testing success."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama-2-7b-chat"},
                {"id": "vicuna-13b"}
            ]
        }
        mock_get.return_value = mock_response
        
        success, info = helper.test_webui_api(base_url)
        
        assert success is True
        assert "API working" in info
        assert "llama-2-7b-chat" in info
    
    @patch('requests.get')
    def test_test_webui_api_alternative_format(self, mock_get):
        """Test WebUI API testing with alternative response format."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        
        # Mock API response with list format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "model-1"},
            {"id": "model-2"}
        ]
        mock_get.return_value = mock_response
        
        success, info = helper.test_webui_api(base_url)
        
        assert success is True
        assert "API working" in info
    
    @patch('requests.get')
    def test_test_webui_api_no_models(self, mock_get):
        """Test WebUI API testing with no models."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        
        # Mock API response with empty models
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response
        
        success, info = helper.test_webui_api(base_url)
        
        assert success is False
        assert "no models found" in info
    
    def test_generate_env_config(self):
        """Test environment configuration generation."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        api_key = "test-key"
        
        config = helper.generate_env_config(base_url, api_key)
        
        assert "AI_PROVIDER=openai_compatible" in config
        assert "AI_BASE_URL=http://127.0.0.1:5000/v1" in config
        assert "AI_API_KEY=test-key" in config
        assert "AI_MODEL=local-model" in config
        assert "AI_CACHE_ENABLED=true" in config
    
    def test_install_webui(self):
        """Test WebUI installation guidance."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        from io import StringIO
        import sys
        
        helper = TextGenerationWebUISetupHelper()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        result = helper.install_webui()
        
        sys.stdout = sys.__stdout__  # Restore stdout
        
        output = captured_output.getvalue()
        assert result is True
        assert "Installation Guide" in output
        assert "git clone" in output
        assert "oobabooga/text-generation-webui" in output
    
    def test_start_webui_server(self):
        """Test WebUI server startup guidance."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        from io import StringIO
        import sys
        
        helper = TextGenerationWebUISetupHelper()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        result = helper.start_webui_server(
            model_path="/path/to/model",
            host="127.0.0.1",
            port=7860,
            api_port=5000
        )
        
        sys.stdout = sys.__stdout__  # Restore stdout
        
        output = captured_output.getvalue()
        assert result is True
        assert "Server Setup" in output
        assert "--api" in output
        assert "--listen" in output
        assert "--api-port 5000" in output
        assert "/path/to/model" in output
    
    @patch('requests.get')
    def test_troubleshoot_connection(self, mock_get):
        """Test connection troubleshooting."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        
        # Mock connection error with the correct exception type that the script catches
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        issues = helper.troubleshoot_connection(base_url)
        
        assert len(issues) > 0
        assert any("Cannot connect to server" in issue for issue in issues)
        assert any("--api flag" in issue for issue in issues)
    
    @patch('requests.get')
    def test_detect_models(self, mock_get):
        """Test model detection."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        
        # Mock successful model response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama-2-7b-chat"},
                {"id": "vicuna-13b"},
                {"id": "wizard-7b"}
            ]
        }
        mock_get.return_value = mock_response
        
        models = helper.detect_models(base_url)
        
        assert len(models) == 3
        assert "llama-2-7b-chat" in models
        assert "vicuna-13b" in models
        assert "wizard-7b" in models
    
    @patch('requests.get')
    def test_detect_models_empty(self, mock_get):
        """Test model detection with no models."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response
        
        models = helper.detect_models(base_url)
        
        assert len(models) == 0
    
    def test_run_diagnostic_success(self):
        """Test successful diagnostic run."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        # Mock the helper methods to return expected values
        helper.check_webui_installation = Mock(return_value=(True, "Text-Generation-WebUI found at text-generation-webui/"))
        helper.check_webui_running = Mock(return_value=(True, "API running at http://127.0.0.1:5000", "http://127.0.0.1:5000"))
        helper.test_webui_api = Mock(return_value=(True, "API working"))
        
        # Capture stdout
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        
        result = helper.run_diagnostic()
        
        sys.stdout = sys.__stdout__  # Restore stdout
        
        assert result is True
        
        output = captured_output.getvalue()
        assert "API working" in output
    
    @patch('builtins.input')
    @patch('requests.get')
    def test_interactive_setup_success(self, mock_get, mock_input):
        """Test successful interactive setup."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        
        # Mock check_webui_installation to return True
        helper.check_webui_installation = Mock(return_value=(True, "Text-Generation-WebUI found at text-generation-webui/"))
        
        # Mock user inputs
        mock_input.side_effect = ['2', 'http://127.0.0.1:5000', 'llama-2-7b', 'y']
        
        # Mock running server
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "llama-2-7b"}]
        }
        mock_get.return_value = mock_response
        
        result = helper.interactive_setup()
        
        assert result is True
    
    def test_generate_test_script(self):
        """Test test script generation."""
        from text_generation_webui_setup import TextGenerationWebUISetupHelper
        
        helper = TextGenerationWebUISetupHelper()
        base_url = "http://127.0.0.1:5000"
        model = "llama-2-7b"
        
        script = helper.generate_test_script(base_url, model)
        
        assert "from ai_utilities import create_client" in script
        assert 'os.environ["AI_BASE_URL"] = "http://127.0.0.1:5000/v1"' in script
        assert 'os.environ["AI_MODEL"] = "llama-2-7b"' in script
        assert "test_webui()" in script
    
    def test_cli_help(self):
        """Test CLI help functionality."""
        result = subprocess.run(
            [sys.executable, 'scripts/text_generation_webui_setup.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Text-Generation-WebUI setup and diagnostic tool" in result.stdout
        assert "--diagnostic" in result.stdout
        assert "--interactive" in result.stdout
        assert "--install-guide" in result.stdout
    
    @patch('text_generation_webui_setup.TextGenerationWebUISetupHelper.run_diagnostic')
    def test_main_function_default(self, mock_diagnostic):
        """Test main function default behavior."""
        from text_generation_webui_setup import main
        
        mock_diagnostic.return_value = True
        
        with patch('sys.argv', ['text_generation_webui_setup.py']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)
    
    @patch('text_generation_webui_setup.TextGenerationWebUISetupHelper.install_webui')
    def test_main_function_install_guide(self, mock_install):
        """Test main function with --install-guide option."""
        from text_generation_webui_setup import main
        
        mock_install.return_value = True
        
        with patch('sys.argv', ['text_generation_webui_setup.py', '--install-guide']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    pytest.main([__file__])
