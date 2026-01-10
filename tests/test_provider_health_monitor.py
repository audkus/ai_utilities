#!/usr/bin/env python3
"""
Tests for provider_health_monitor.py script.

Tests the provider health monitoring functionality including:
- Health check execution
- Provider status tracking
- Alert generation
- Report generation
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


class TestProviderHealthMonitor:
    """Test provider health monitor functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "test_config.json"
        self.report_file = self.temp_dir / "test_report.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_health_monitor_initialization(self):
        """Test ProviderHealthMonitor initialization."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        assert hasattr(monitor, 'providers')
        assert hasattr(monitor, 'health_checks')
        assert hasattr(monitor, 'alert_thresholds')
    
    @patch('provider_health_monitor.requests.get')
    def test_check_provider_health_success(self, mock_get):
        """Test successful health check for a provider."""
        from provider_health_monitor import ProviderHealthMonitor
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "models": ["gpt-4"]}
        mock_get.return_value = mock_response
        
        monitor = ProviderHealthMonitor()
        result = monitor.check_provider_health("openai", "https://api.openai.com/v1/models")
        
        assert result["status"] == "healthy"
        assert result["response_time"] > 0
        assert "models" in result
    
    @patch('provider_health_monitor.requests.get')
    def test_check_provider_health_failure(self, mock_get):
        """Test failed health check for a provider."""
        from provider_health_monitor import ProviderHealthMonitor
        
        # Mock failed response
        mock_get.side_effect = Exception("Connection failed")
        
        monitor = ProviderHealthMonitor()
        result = monitor.check_provider_health("openai", "https://api.openai.com/v1/models")
        
        assert result["status"] == "unhealthy"
        assert "error" in result
    
    @patch('provider_health_monitor.ProviderHealthMonitor.check_provider_health')
    def test_run_health_checks_all_providers(self, mock_check):
        """Test running health checks for all providers."""
        from provider_health_monitor import ProviderHealthMonitor
        
        # Mock health check results
        mock_check.side_effect = [
            {"status": "healthy", "response_time": 100},
            {"status": "unhealthy", "error": "Connection failed"},
            {"status": "healthy", "response_time": 200}
        ]
        
        monitor = ProviderHealthMonitor()
        results = monitor.run_health_checks()
        
        assert len(results) == 3
        assert mock_check.call_count == 3
        assert any(r["status"] == "healthy" for r in results)
        assert any(r["status"] == "unhealthy" for r in results)
    
    def test_generate_health_report(self):
        """Test health report generation."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Mock health check results
        health_results = [
            {"provider": "openai", "status": "healthy", "response_time": 100},
            {"provider": "groq", "status": "unhealthy", "error": "Connection failed"},
            {"provider": "together", "status": "healthy", "response_time": 200}
        ]
        
        report = monitor.generate_health_report(health_results)
        
        assert "summary" in report
        assert "providers" in report
        assert report["summary"]["total"] == 3
        assert report["summary"]["healthy"] == 2
        assert report["summary"]["unhealthy"] == 1
        assert len(report["providers"]) == 3
    
    def test_save_report_to_file(self):
        """Test saving health report to file."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        test_report = {
            "summary": {"total": 2, "healthy": 1, "unhealthy": 1},
            "providers": [
                {"provider": "openai", "status": "healthy"},
                {"provider": "groq", "status": "unhealthy"}
            ]
        }
        
        monitor.save_report(test_report, self.report_file)
        
        assert self.report_file.exists()
        
        # Verify content
        with open(self.report_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["summary"]["total"] == 2
        assert len(saved_report["providers"]) == 2
    
    @patch('provider_health_monitor.ProviderHealthMonitor.run_health_checks')
    @patch('provider_health_monitor.ProviderHealthMonitor.generate_health_report')
    @patch('provider_health_monitor.ProviderHealthMonitor.save_report')
    def test_run_full_monitoring_cycle(self, mock_save, mock_generate, mock_run):
        """Test full monitoring cycle."""
        from provider_health_monitor import ProviderHealthMonitor
        
        # Mock the monitoring cycle
        mock_run.return_value = [{"status": "healthy"}]
        mock_generate.return_value = {"summary": {"total": 1}}
        
        monitor = ProviderHealthMonitor()
        monitor.run_monitoring_cycle(output_file=str(self.report_file))
        
        mock_run.assert_called_once()
        mock_generate.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('provider_health_monitor.ProviderHealthMonitor.check_provider_health')
    def test_alert_generation_for_unhealthy_providers(self, mock_check):
        """Test alert generation for unhealthy providers."""
        from provider_health_monitor import ProviderHealthMonitor
        
        # Mock unhealthy provider
        mock_check.return_value = {
            "status": "unhealthy",
            "error": "Connection timeout",
            "response_time": 5000
        }
        
        monitor = ProviderHealthMonitor()
        alerts = monitor.check_alerts(["openai"])
        
        assert len(alerts) > 0
        assert any("unhealthy" in alert["message"].lower() for alert in alerts)
    
    def test_config_loading(self):
        """Test configuration loading from file."""
        from provider_health_monitor import ProviderHealthMonitor
        
        # Create test config
        test_config = {
            "providers": {
                "openai": {
                    "url": "https://api.openai.com/v1/models",
                    "timeout": 10
                }
            },
            "alert_thresholds": {
                "response_time": 1000,
                "consecutive_failures": 3
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        monitor = ProviderHealthMonitor(config_file=str(self.config_file))
        
        assert "openai" in monitor.providers
        assert monitor.providers["openai"]["url"] == "https://api.openai.com/v1/models"
        assert monitor.alert_thresholds["response_time"] == 1000
    
    @patch('provider_health_monitor.ProviderHealthMonitor.run_health_checks')
    def test_continuous_monitoring(self, mock_run):
        """Test continuous monitoring mode."""
        from provider_health_monitor import ProviderHealthMonitor
        import time
        
        mock_run.return_value = [{"status": "healthy"}]
        
        monitor = ProviderHealthMonitor()
        
        # Test continuous monitoring (short duration for testing)
        start_time = time.time()
        monitor.run_continuous_monitoring(interval=0.1, duration=0.3)
        end_time = time.time()
        
        # Should run approximately 3 times in 0.3 seconds
        assert mock_run.call_count >= 2
        assert end_time - start_time >= 0.2


class TestHealthMonitorCLI:
    """Test health monitor command line interface."""
    
    @patch('provider_health_monitor.ProviderHealthMonitor.run_monitoring_cycle')
    def test_cli_single_check(self, mock_run):
        """Test CLI single health check."""
        from provider_health_monitor import main
        
        with patch('sys.argv', ['provider_health_monitor.py', '--single']):
            main()
        
        mock_run.assert_called_once()
    
    @patch('provider_health_monitor.ProviderHealthMonitor.run_continuous_monitoring')
    def test_cli_continuous_mode(self, mock_continuous):
        """Test CLI continuous monitoring mode."""
        from provider_health_monitor import main
        
        with patch('sys.argv', ['provider_health_monitor.py', '--continuous', '--interval', '60']):
            main()
        
        mock_continuous.assert_called_once()
    
    def test_cli_help_output(self):
        """Test CLI help output."""
        from provider_health_monitor import main
        
        with patch('sys.argv', ['provider_health_monitor.py', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Help command exits with 0
