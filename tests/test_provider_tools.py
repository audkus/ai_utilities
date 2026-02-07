#!/usr/bin/env python3
"""
Tests for provider_tools.py script.

Tests the consolidated provider tools functionality including:
- Provider health monitoring
- Change detection and alerting
- Diagnostic tools
- CLI interface and argument parsing
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytest

# Add scripts to path for imports
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)


class TestProviderTools:
    """Test provider tools functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "test_config.json"
        self.report_file = self.temp_dir / "test_report.json"
        
        # Mock environment variables
        self.env_vars = {
            'OPENAI_API_KEY': 'test-openai-key',
            'GROQ_API_KEY': 'test-groq-key'
        }
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.dict(os.environ, env_vars)
    def test_provider_monitor_initialization(self):
        """Test ProviderMonitor initialization."""
        from provider_tools import ProviderMonitor
        
        monitor = ProviderMonitor()
        
        assert hasattr(monitor, 'providers')
        assert hasattr(monitor, 'alert_thresholds')
        assert len(monitor.providers) >= 2  # At least OpenAI and Groq
        assert monitor.alert_thresholds['response_time'] == 10.0
    
    def test_provider_status_dataclass(self):
        """Test ProviderStatus dataclass."""
        from provider_tools import ProviderStatus
        from datetime import datetime
        
        now = datetime.now()
        status = ProviderStatus(
            name="Test Provider",
            endpoint="https://api.test.com",
            api_key_env="TEST_API_KEY",
            test_model="test-model",
            last_check=now,
            status="healthy",
            issues=[],
            response_time=0.5
        )
        
        assert status.name == "Test Provider"
        assert status.status == "healthy"
        assert status.response_time == 0.5
        assert status.issues == []
    
    @patch.dict(os.environ, env_vars)
    @patch('provider_tools.create_client')
    def test_health_check_success(self, mock_create_client):
        """Test successful health check."""
        from provider_tools import ProviderMonitor
        
        # Mock successful client
        mock_client = Mock()
        mock_client.ask.return_value = "Test response"
        mock_create_client.return_value = mock_client
        
        monitor = ProviderMonitor()
        results = monitor.run_health_check()
        
        assert 'providers' in results
        assert 'timestamp' in results
        assert 'summary' in results
        assert len(results['providers']) >= 2
    
    @patch.dict(os.environ, {})
    def test_health_check_missing_api_key(self):
        """Test health check with missing API key."""
        from provider_tools import ProviderMonitor
        
        monitor = ProviderMonitor()
        results = monitor.run_health_check()
        
        # Should still run but show providers as down
        assert 'providers' in results
        assert 'summary' in results
    
    def test_diagnostics_initialization(self):
        """Test ProviderDiagnostics initialization."""
        from provider_tools import ProviderDiagnostics
        
        diagnostics = ProviderDiagnostics()
        assert hasattr(diagnostics, 'monitor')
    
    @patch.dict(os.environ, env_vars)
    @patch('provider_tools.requests.get')
    def test_connectivity_check_success(self, mock_get):
        """Test successful connectivity check."""
        from provider_tools import ProviderDiagnostics
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        diagnostics = ProviderDiagnostics()
        results = diagnostics.run_diagnostics()
        
        assert 'environment' in results
        assert 'connectivity' in results
        assert 'configuration' in results
        assert 'dependencies' in results
    
    @patch.dict(os.environ, env_vars)
    @patch('provider_tools.requests.get')
    def test_connectivity_check_failure(self, mock_get):
        """Test connectivity check with failure."""
        from provider_tools import ProviderDiagnostics
        
        # Mock failed HTTP response
        mock_get.side_effect = Exception("Connection failed")
        
        diagnostics = ProviderDiagnostics()
        results = diagnostics.run_diagnostics()
        
        assert 'connectivity' in results
        # Should show connection issues
    
    def test_change_detector_initialization(self):
        """Test ChangeDetector initialization."""
        from provider_tools import ChangeDetector
        
        detector = ChangeDetector()
        assert hasattr(detector, 'monitor')
    
    @patch.dict(os.environ, env_vars)
    @patch('provider_tools.create_client')
    def test_change_detection(self, mock_create_client):
        """Test change detection functionality."""
        from provider_tools import ChangeDetector
        
        # Mock client
        mock_client = Mock()
        mock_client.ask.return_value = "Test response"
        mock_create_client.return_value = mock_client
        
        detector = ChangeDetector()
        results = detector.detect_changes()
        
        assert 'results' in results
        assert 'changes' in results
        assert 'alerts' in results
        assert 'timestamp' in results
    
    def test_cli_argument_parsing(self):
        """Test CLI argument parsing."""
        from provider_tools import main
        import argparse
        
        # Test help
        with patch('sys.argv', ['provider_tools.py', '--help']):
            with patch('argparse.ArgumentParser.print_help') as mock_help:
                try:
                    main()
                except SystemExit:
                    pass  # Expected for --help
                mock_help.assert_called_once()
    
    @patch.dict(os.environ, env_vars)
    @patch('provider_tools.create_client')
    def test_cli_health_check(self, mock_create_client):
        """Test CLI health check execution."""
        from provider_tools import main
        
        # Mock successful client
        mock_client = Mock()
        mock_client.ask.return_value = "Test response"
        mock_create_client.return_value = mock_client
        
        with patch('sys.argv', ['provider_tools.py', '--health-check']):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0  # Success exit code
    
    @patch.dict(os.environ, env_vars)
    def test_cli_diagnose(self):
        """Test CLI diagnostics execution."""
        from provider_tools import main
        
        with patch('sys.argv', ['provider_tools.py', '--diagnose']):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0  # Success exit code
    
    def test_json_serialization(self):
        """Test JSON serialization of results."""
        from provider_tools import ProviderStatus
        from datetime import datetime
        import json
        
        now = datetime.now()
        status = ProviderStatus(
            name="Test Provider",
            endpoint="https://api.test.com",
            api_key_env="TEST_API_KEY",
            test_model="test-model",
            last_check=now,
            status="healthy",
            issues=[],
            response_time=0.5
        )
        
        # Should be serializable with datetime handling
        with patch('provider_tools.asdict') as mock_asdict:
            mock_asdict.return_value = {
                'name': 'Test Provider',
                'last_check': now.isoformat(),
                'changed_since': None
            }
            
            # Test that the save_status method handles datetime serialization
            from provider_tools import ProviderMonitor
            monitor = ProviderMonitor()
            
            # This should not raise an exception
            monitor._save_status({'test': status})
    
    def test_error_handling(self):
        """Test error handling in provider tools."""
        from provider_tools import ProviderMonitor
        
        # Test with invalid provider configuration
        monitor = ProviderMonitor()
        
        # Should handle missing API keys gracefully
        with patch.dict(os.environ, {}, clear=True):
            results = monitor.run_health_check()
            assert 'providers' in results
            assert 'summary' in results
    
    @patch.dict(os.environ, env_vars)
    def test_alert_generation(self):
        """Test alert generation for changes."""
        from provider_tools import ChangeDetector
        
        detector = ChangeDetector()
        
        # Test change analysis
        changes = {
            "status_changes": [
                {
                    "provider": "Test Provider",
                    "from": "healthy",
                    "to": "down",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "new_issues": [],
            "performance_changes": []
        }
        
        alerts = detector._generate_alerts(changes)
        
        assert len(alerts) == 1
        assert alerts[0]['severity'] == 'high'
        assert alerts[0]['type'] == 'status_change'
        assert 'down' in alerts[0]['message']


class TestProviderToolsIntegration:
    """Integration tests for provider tools."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('provider_tools.create_client')
    def test_full_workflow(self, mock_create_client):
        """Test full workflow from health check to change detection."""
        from provider_tools import ProviderMonitor, ChangeDetector
        
        # Mock successful client
        mock_client = Mock()
        mock_client.ask.return_value = "Test response"
        mock_create_client.return_value = mock_client
        
        # Run health check
        monitor = ProviderMonitor()
        health_results = monitor.run_health_check()
        
        # Run change detection
        detector = ChangeDetector()
        change_results = detector.detect_changes()
        
        # Verify both operations completed successfully
        assert 'providers' in health_results
        assert 'changes' in change_results
        assert 'alerts' in change_results
    
    def test_report_generation(self):
        """Test report file generation."""
        from provider_tools import ProviderMonitor
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('provider_tools.create_client') as mock_create:
                mock_client = Mock()
                mock_client.ask.return_value = "Test response"
                mock_create.return_value = mock_client
                
                monitor = ProviderMonitor()
                
                # Change working directory to temp dir
                original_cwd = os.getcwd()
                try:
                    os.chdir(self.temp_dir)
                    
                    # Run health check (should generate report)
                    results = monitor.run_health_check()
                    
                    # Check if report file was created
                    report_files = list(Path('.').glob('provider_*_report.json'))
                    assert len(report_files) > 0
                    
                finally:
                    os.chdir(original_cwd)


if __name__ == '__main__':
    # Run tests when executed directly
    pytest.main([__file__])
