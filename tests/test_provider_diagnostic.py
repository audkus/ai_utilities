#!/usr/bin/env python3
"""
Tests for provider_diagnostic.py script.

Tests the provider diagnostic functionality including:
- Provider connectivity testing
- Configuration validation
- API key validation
- Diagnostic report generation
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add scripts to path for imports
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)


class TestProviderDiagnostic:
    """Test provider diagnostic functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "test_config.json"
        self.report_file = self.temp_dir / "diagnostic_report.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_diagnostic_tool_initialization(self):
        """Test ProviderDiagnostic initialization."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        assert hasattr(diagnostic, 'providers')
        assert hasattr(diagnostic, 'test_functions')
        assert hasattr(diagnostic, 'results')
    
    @patch('provider_diagnostic.requests.get')
    def test_connectivity_test_success(self, mock_get):
        """Test successful connectivity test."""
        from provider_diagnostic import ProviderDiagnostic
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
        mock_get.return_value = mock_response
        
        diagnostic = ProviderDiagnostic()
        result = diagnostic.test_connectivity("openai", "https://api.openai.com/v1/models", "test-key")
        
        assert result["status"] == "success"
        assert result["response_code"] == 200
        assert result["response_time"] > 0
    
    @patch('provider_diagnostic.requests.get')
    def test_connectivity_test_failure(self, mock_get):
        """Test failed connectivity test."""
        from provider_diagnostic import ProviderDiagnostic
        
        # Mock failed response
        mock_get.side_effect = Exception("Connection failed")
        
        diagnostic = ProviderDiagnostic()
        result = diagnostic.test_connectivity("openai", "https://api.openai.com/v1/models", "test-key")
        
        assert result["status"] == "failed"
        assert "error" in result
    
    @patch('provider_diagnostic.requests.get')
    def test_connectivity_test_auth_error(self, mock_get):
        """Test connectivity test with authentication error."""
        from provider_diagnostic import ProviderDiagnostic
        
        # Mock auth error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_get.return_value = mock_response
        
        diagnostic = ProviderDiagnostic()
        result = diagnostic.test_connectivity("openai", "https://api.openai.com/v1/models", "invalid-key")
        
        assert result["status"] == "auth_error"
        assert result["response_code"] == 401
    
    def test_api_key_validation_valid_key(self):
        """Test API key validation for valid key."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        # Test various valid key formats
        valid_keys = [
            "sk-1234567890abcdef",
            "sk-proj-1234567890abcdef1234567890abcdef",
            "gqr_1234567890abcdef",
            "1234567890abcdef"  # Generic format
        ]
        
        for key in valid_keys:
            result = diagnostic.validate_api_key("openai", key)
            assert result["valid"] is True
    
    def test_api_key_validation_invalid_key(self):
        """Test API key validation for invalid key."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        # Test invalid key formats
        invalid_keys = [
            "",
            "short",
            "invalid-key-format",
            "no_numbers_here"
        ]
        
        for key in invalid_keys:
            result = diagnostic.validate_api_key("openai", key)
            assert result["valid"] is False
    
    def test_configuration_validation_complete_config(self):
        """Test configuration validation for complete configuration."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        complete_config = {
            "provider": "openai",
            "api_key": "sk-1234567890abcdef",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4",
            "timeout": 30
        }
        
        result = diagnostic.validate_configuration(complete_config)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
    
    def test_configuration_validation_missing_fields(self):
        """Test configuration validation with missing fields."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        incomplete_config = {
            "provider": "openai",
            # Missing api_key, base_url, model
        }
        
        result = diagnostic.validate_configuration(incomplete_config)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("api_key" in error for error in result["errors"])
    
    @patch('provider_diagnostic.ProviderDiagnostic.test_connectivity')
    @patch('provider_diagnostic.ProviderDiagnostic.validate_api_key')
    @patch('provider_diagnostic.ProviderDiagnostic.validate_configuration')
    def test_run_comprehensive_diagnostic(self, mock_config, mock_key, mock_connectivity):
        """Test comprehensive diagnostic run."""
        from provider_diagnostic import ProviderDiagnostic
        
        # Mock diagnostic components
        mock_config.return_value = {"valid": True, "errors": [], "warnings": []}
        mock_key.return_value = {"valid": True}
        mock_connectivity.return_value = {"status": "success", "response_time": 100}
        
        diagnostic = ProviderDiagnostic()
        
        test_config = {
            "provider": "openai",
            "api_key": "sk-1234567890abcdef",
            "base_url": "https://api.openai.com/v1"
        }
        
        results = diagnostic.run_diagnostic(test_config)
        
        assert "configuration" in results
        assert "api_key" in results
        assert "connectivity" in results
        assert "overall_status" in results
        
        mock_config.assert_called_once()
        mock_key.assert_called_once()
        mock_connectivity.assert_called_once()
    
    def test_generate_diagnostic_report(self):
        """Test diagnostic report generation."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        # Mock diagnostic results
        diagnostic.results = {
            "configuration": {"valid": True, "errors": [], "warnings": []},
            "api_key": {"valid": True},
            "connectivity": {"status": "success", "response_time": 100}
        }
        
        report = diagnostic.generate_report()
        
        assert "summary" in report
        assert "details" in report
        assert "timestamp" in report
        assert report["summary"]["overall_status"] == "healthy"
        assert report["summary"]["tests_passed"] == 3
        assert report["summary"]["tests_failed"] == 0
    
    def test_save_diagnostic_report(self):
        """Test saving diagnostic report to file."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        test_report = {
            "summary": {"overall_status": "healthy", "tests_passed": 3, "tests_failed": 0},
            "details": {
                "configuration": {"valid": True},
                "api_key": {"valid": True},
                "connectivity": {"status": "success"}
            },
            "timestamp": "2026-01-10T12:00:00Z"
        }
        
        diagnostic.save_report(test_report, self.report_file)
        
        assert self.report_file.exists()
        
        # Verify content
        with open(self.report_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["summary"]["overall_status"] == "healthy"
        assert saved_report["summary"]["tests_passed"] == 3
    
    @patch('provider_diagnostic.ProviderDiagnostic.run_diagnostic')
    @patch('provider_diagnostic.ProviderDiagnostic.generate_report')
    @patch('provider_diagnostic.ProviderDiagnostic.save_report')
    def test_run_diagnostic_with_config_file(self, mock_save, mock_generate, mock_run):
        """Test running diagnostic with configuration file."""
        from provider_diagnostic import ProviderDiagnostic
        
        # Create test config file
        test_config = {
            "provider": "openai",
            "api_key": "sk-1234567890abcdef",
            "base_url": "https://api.openai.com/v1"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Mock diagnostic results
        mock_run.return_value = {"overall_status": "healthy"}
        mock_generate.return_value = {"summary": {"overall_status": "healthy"}}
        
        diagnostic = ProviderDiagnostic()
        diagnostic.run_from_config_file(str(self.config_file), str(self.report_file))
        
        mock_run.assert_called_once()
        mock_generate.assert_called_once()
        mock_save.assert_called_once()
    
    def test_test_specific_provider(self):
        """Test diagnostic for specific provider."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        # Test with different providers
        providers = ["openai", "groq", "together", "anthropic"]
        
        for provider in providers:
            config = {
                "provider": provider,
                "api_key": "test-key-1234567890abcdef",
                "base_url": f"https://api.{provider}.com/v1"
            }
            
            # Should not raise an exception
            result = diagnostic.validate_configuration(config)
            assert isinstance(result, dict)
            assert "valid" in result
    
    @patch('provider_diagnostic.ProviderDiagnostic.test_connectivity')
    def test_performance_benchmarking(self, mock_connectivity):
        """Test performance benchmarking functionality."""
        from provider_diagnostic import ProviderDiagnostic
        
        # Mock different response times
        mock_connectivity.side_effect = [
            {"status": "success", "response_time": 100},
            {"status": "success", "response_time": 150},
            {"status": "success", "response_time": 120}
        ]
        
        diagnostic = ProviderDiagnostic()
        
        config = {
            "provider": "openai",
            "api_key": "sk-1234567890abcdef",
            "base_url": "https://api.openai.com/v1"
        }
        
        benchmark_results = diagnostic.run_performance_benchmark(config, iterations=3)
        
        assert len(benchmark_results) == 3
        assert all(result["status"] == "success" for result in benchmark_results)
        
        # Calculate average response time
        avg_time = sum(r["response_time"] for r in benchmark_results) / len(benchmark_results)
        assert 100 <= avg_time <= 150  # Should be between min and max mock values


class TestDiagnosticCLI:
    """Test diagnostic command line interface."""
    
    @patch('provider_diagnostic.ProviderDiagnostic.run_from_config_file')
    def test_cli_with_config_file(self, mock_run):
        """Test CLI with configuration file."""
        from provider_diagnostic import main
        
        with patch('sys.argv', ['provider_diagnostic.py', '--config', 'test_config.json']):
            main()
        
        mock_run.assert_called_once()
    
    @patch('provider_diagnostic.ProviderDiagnostic.run_diagnostic')
    def test_cli_with_provider_params(self, mock_run):
        """Test CLI with provider parameters."""
        from provider_diagnostic import main
        
        with patch('sys.argv', [
            'provider_diagnostic.py', 
            '--provider', 'openai',
            '--api-key', 'sk-test-key',
            '--base-url', 'https://api.openai.com/v1'
        ]):
            main()
        
        mock_run.assert_called_once()
    
    def test_cli_help_output(self):
        """Test CLI help output."""
        from provider_diagnostic import main
        
        with patch('sys.argv', ['provider_diagnostic.py', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Help command exits with 0
    
    @patch('provider_diagnostic.ProviderDiagnostic.run_performance_benchmark')
    def test_cli_benchmark_mode(self, mock_benchmark):
        """Test CLI benchmark mode."""
        from provider_diagnostic import main
        
        with patch('sys.argv', [
            'provider_diagnostic.py',
            '--benchmark',
            '--provider', 'openai',
            '--api-key', 'sk-test-key',
            '--iterations', '5'
        ]):
            main()
        
        mock_benchmark.assert_called_once()
