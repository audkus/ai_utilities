#!/usr/bin/env python3
"""
Tests for webui_api_helper.py script.

Tests the WebUI API helper functionality including:
- API endpoint detection
- Configuration generation
- Health checks
- Integration utilities
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add scripts to path for imports
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, src_dir)


class TestWebUIAPIHelper:
    """Test WebUI API helper functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "webui_config.json"
        self.output_file = self.temp_dir / "generated_config.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_webui_helper_initialization(self):
        """Test WebUIAPIHelper initialization."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        assert hasattr(helper, 'supported_webuis')
        assert hasattr(helper, 'default_ports')
        assert hasattr(helper, 'health_endpoints')
        assert hasattr(helper, 'config_templates')
    
    def test_webui_helper_with_config(self):
        """Test WebUIAPIHelper with configuration file."""
        from webui_api_helper import WebUIAPIHelper
        
        # Create test config
        test_config = {
            "webuis": {
                "text-generation-webui": {
                    "default_port": 7860,
                    "health_endpoint": "/api/v1/models",
                    "api_format": "openai_compatible"
                },
                "fastchat": {
                    "default_port": 8000,
                    "health_endpoint": "/v1/models",
                    "api_format": "openai_compatible"
                }
            },
            "detection": {
                "timeout": 10,
                "retry_attempts": 3
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        helper = WebUIAPIHelper(config_file=str(self.config_file))
        
        assert len(helper.supported_webuis) == 2
        assert "text-generation-webui" in helper.supported_webuis
        assert "fastchat" in helper.supported_webuis
        assert helper.default_ports["text-generation-webui"] == 7860
    
    @patch('webui_api_helper.requests.get')
    def test_detect_webui_on_port_success(self, mock_get):
        """Test successful WebUI detection on port."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "llama-2-7b"}]}
        mock_get.return_value = mock_response
        
        helper = WebUIAPIHelper()
        result = helper.detect_webui_on_port(7860)
        
        assert result["detected"] is True
        assert result["webui_type"] in ["text-generation-webui", "fastchat", "unknown"]
        assert result["port"] == 7860
        assert result["endpoint"] is not None
        assert result["response_time_ms"] > 0
    
    @patch('webui_api_helper.requests.get')
    def test_detect_webui_on_port_failure(self, mock_get):
        """Test failed WebUI detection on port."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock failed response
        mock_get.side_effect = Exception("Connection refused")
        
        helper = WebUIAPIHelper()
        result = helper.detect_webui_on_port(7860)
        
        assert result["detected"] is False
        assert "error" in result
        assert result["port"] == 7860
    
    @patch('webui_api_helper.WebUIAPIHelper.detect_webui_on_port')
    def test_scan_for_webuis(self, mock_detect):
        """Test scanning for WebUIs on multiple ports."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock detection results
        mock_detect.side_effect = [
            {"detected": True, "webui_type": "text-generation-webui", "port": 7860},
            {"detected": False, "port": 8000},
            {"detected": True, "webui_type": "fastchat", "port": 5000}
        ]
        
        helper = WebUIAPIHelper()
        results = helper.scan_for_webuis([7860, 8000, 5000])
        
        assert len(results) == 3
        assert results[0]["detected"] is True
        assert results[1]["detected"] is False
        assert results[2]["detected"] is True
        assert mock_detect.call_count == 3
    
    @patch('webui_api_helper.requests.get')
    def test_identify_webui_type_by_response(self, mock_get):
        """Test WebUI type identification by API response."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock text-generation-webui response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "llama-2-7b-chat"}]}
        mock_response.headers = {"server": "uvicorn"}
        mock_get.return_value = mock_response
        
        helper = WebUIAPIHelper()
        webui_type = helper.identify_webui_type("http://localhost:7860")
        
        assert webui_type in ["text-generation-webui", "fastchat", "unknown"]
    
    def test_generate_ai_utilities_config(self):
        """Test AI Utilities configuration generation."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        webui_info = {
            "type": "text-generation-webui",
            "host": "localhost",
            "port": 7860,
            "endpoint": "http://localhost:7860/api/v1",
            "models": ["llama-2-7b", "llama-2-13b"]
        }
        
        config = helper.generate_ai_utilities_config(webui_info)
        
        assert "provider" in config
        assert "base_url" in config
        assert "api_key" in config
        assert "models" in config
        
        assert config["provider"] == "openai_compatible"
        assert config["base_url"] == "http://localhost:7860/api/v1"
        assert config["api_key"] == "not_required"
        assert len(config["models"]) == 2
    
    def test_generate_env_file_content(self):
        """Test .env file content generation."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        webui_info = {
            "type": "fastchat",
            "host": "localhost",
            "port": 8000,
            "endpoint": "http://localhost:8000/v1"
        }
        
        env_content = helper.generate_env_file_content(webui_info)
        
        assert "AI_PROVIDER=openai_compatible" in env_content
        assert "AI_BASE_URL=http://localhost:8000/v1" in env_content
        assert "AI_API_KEY=not_required" in env_content
        assert "# Generated by WebUI API Helper" in env_content
    
    @patch('webui_api_helper.WebUIAPIHelper.scan_for_webuis')
    def test_auto_detect_and_configure(self, mock_scan):
        """Test automatic WebUI detection and configuration."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock successful detection
        mock_scan.return_value = [
            {
                "detected": True,
                "webui_type": "text-generation-webui",
                "port": 7860,
                "endpoint": "http://localhost:7860/api/v1",
                "models": ["llama-2-7b"]
            }
        ]
        
        helper = WebUIAPIHelper()
        config = helper.auto_detect_and_configure()
        
        assert config is not None
        assert config["provider"] == "openai_compatible"
        assert config["base_url"] == "http://localhost:7860/api/v1"
        mock_scan.assert_called_once()
    
    @patch('webui_api_helper.requests.get')
    def test_test_webui_connection(self, mock_get):
        """Test WebUI connection testing."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock successful API call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"text": "Test response"}]}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_get.return_value = mock_response
        
        helper = WebUIAPIHelper()
        
        config = {
            "provider": "openai_compatible",
            "base_url": "http://localhost:7860/api/v1",
            "api_key": "not_required"
        }
        
        result = helper.test_webui_connection(config)
        
        assert result["status"] == "success"
        assert result["response_time_ms"] == 500
        assert result["test_response"] is not None
    
    @patch('webui_api_helper.requests.get')
    def test_test_webui_connection_failure(self, mock_get):
        """Test WebUI connection testing with failure."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock failed API call
        mock_get.side_effect = Exception("Connection failed")
        
        helper = WebUIAPIHelper()
        
        config = {
            "provider": "openai_compatible",
            "base_url": "http://localhost:7860/api/v1",
            "api_key": "not_required"
        }
        
        result = helper.test_webui_connection(config)
        
        assert result["status"] == "failed"
        assert "error" in result
    
    def test_save_configuration_files(self):
        """Test saving configuration files."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        config = {
            "provider": "openai_compatible",
            "base_url": "http://localhost:7860/api/v1",
            "api_key": "not_required",
            "models": ["llama-2-7b"]
        }
        
        # Save JSON config
        helper.save_config_json(config, self.output_file)
        
        assert self.output_file.exists()
        
        # Verify content
        with open(self.output_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config["provider"] == "openai_compatible"
        assert saved_config["base_url"] == "http://localhost:7860/api/v1"
        
        # Save .env file
        env_file = self.temp_dir / ".env"
        helper.save_config_env(config, str(env_file))
        
        assert env_file.exists()
        env_content = env_file.read_text()
        assert "AI_PROVIDER=openai_compatible" in env_content
    
    @patch('webui_api_helper.WebUIAPIHelper.auto_detect_and_configure')
    @patch('webui_api_helper.WebUIAPIHelper.test_webui_connection')
    @patch('webui_api_helper.WebUIAPIHelper.save_config_json')
    def test_run_full_discovery_process(self, mock_save, mock_test, mock_detect):
        """Test full WebUI discovery process."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock the discovery process
        mock_detect.return_value = {
            "provider": "openai_compatible",
            "base_url": "http://localhost:7860/api/v1"
        }
        mock_test.return_value = {"status": "success"}
        
        helper = WebUIAPIHelper()
        result = helper.run_discovery_process(output_file=str(self.output_file))
        
        assert result["success"] is True
        assert result["config"] is not None
        assert result["connection_test"]["status"] == "success"
        
        mock_detect.assert_called_once()
        mock_test.assert_called_once()
        mock_save.assert_called_once()
    
    def test_get_supported_webuis_info(self):
        """Test getting supported WebUIs information."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        info = helper.get_supported_webuis()
        
        assert isinstance(info, list)
        assert len(info) > 0
        
        for webui in info:
            assert "name" in webui
            assert "type" in webui
            assert "default_port" in webui
            assert "description" in webui
    
    def test_validate_webui_config(self):
        """Test WebUI configuration validation."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        # Valid config
        valid_config = {
            "provider": "openai_compatible",
            "base_url": "http://localhost:7860/api/v1",
            "api_key": "not_required"
        }
        
        result = helper.validate_config(valid_config)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # Invalid config
        invalid_config = {
            "provider": "openai_compatible",
            # Missing base_url
            "api_key": ""
        }
        
        result = helper.validate_config(invalid_config)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    @patch('webui_api_helper.WebUIAPIHelper.scan_for_webuis')
    def test_continuous_monitoring(self, mock_scan):
        """Test continuous WebUI monitoring."""
        from webui_api_helper import WebUIAPIHelper
        import time
        
        # Mock detection results
        mock_scan.return_value = [
            {"detected": True, "webui_type": "text-generation-webui", "port": 7860}
        ]
        
        helper = WebUIAPIHelper()
        
        # Test monitoring (short duration for testing)
        start_time = time.time()
        results = helper.run_continuous_monitoring(interval=0.1, duration=0.3)
        end_time = time.time()
        
        assert len(results) >= 2  # Should run at least twice
        assert end_time - start_time >= 0.2
        assert mock_scan.call_count >= 2
    
    def test_get_webui_status_summary(self):
        """Test WebUI status summary generation."""
        from webui_api_helper import WebUIAPIHelper
        
        helper = WebUIAPIHelper()
        
        # Mock scan results
        scan_results = [
            {
                "detected": True,
                "webui_type": "text-generation-webui",
                "port": 7860,
                "response_time_ms": 150
            },
            {
                "detected": False,
                "port": 8000,
                "error": "Connection refused"
            },
            {
                "detected": True,
                "webui_type": "fastchat",
                "port": 5000,
                "response_time_ms": 200
            }
        ]
        
        summary = helper.get_status_summary(scan_results)
        
        assert "total_scanned" in summary
        assert "detected_count" in summary
        assert "healthy_count" in summary
        assert "webuis" in summary
        
        assert summary["total_scanned"] == 3
        assert summary["detected_count"] == 2
        assert len(summary["webuis"]) == 2


class TestWebUIAPIHelperCLI:
    """Test WebUI API helper command line interface."""
    
    @patch('webui_api_helper.WebUIAPIHelper.run_discovery_process')
    def test_cli_discover_command(self, mock_discover):
        """Test CLI discover command."""
        from webui_api_helper import main
        
        with patch('sys.argv', ['webui_api_helper.py', '--discover']):
            main()
        
        mock_discover.assert_called_once()
    
    @patch('webui_api_helper.WebUIAPIHelper.scan_for_webuis')
    def test_cli_scan_command(self, mock_scan):
        """Test CLI scan command."""
        from webui_api_helper import main
        
        with patch('sys.argv', ['webui_api_helper.py', '--scan', '--ports', '7860,8000,5000']):
            main()
        
        mock_scan.assert_called_once()
    
    @patch('webui_api_helper.WebUIAPIHelper.test_webui_connection')
    def test_cli_test_command(self, mock_test):
        """Test CLI test command."""
        from webui_api_helper import main
        
        with patch('sys.argv', [
            'webui_api_helper.py', 
            '--test',
            '--url', 'http://localhost:7860/api/v1'
        ]):
            main()
        
        mock_test.assert_called_once()
    
    def test_cli_list_supported(self):
        """Test CLI list supported command."""
        from webui_api_helper import main
        
        with patch('sys.argv', ['webui_api_helper.py', '--list-supported']):
            with patch('builtins.print') as mock_print:
                main()
                mock_print.assert_called()
    
    def test_cli_help_output(self):
        """Test CLI help output."""
        from webui_api_helper import main
        
        with patch('sys.argv', ['webui_api_helper.py', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Help command exits with 0
