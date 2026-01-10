#!/usr/bin/env python3
"""
Tests for daily_provider_check.py script.

Tests the daily provider checking functionality including:
- Scheduled health checks
- Provider status tracking
- Alert notifications
- Historical data management
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


class TestDailyProviderCheck:
    """Test daily provider check functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "daily_config.json"
        self.history_file = self.temp_dir / "provider_history.json"
        self.report_file = self.temp_dir / "daily_report.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_daily_checker_initialization(self):
        """Test DailyProviderChecker initialization."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        assert hasattr(checker, 'providers')
        assert hasattr(checker, 'check_schedule')
        assert hasattr(checker, 'alert_thresholds')
        assert hasattr(checker, 'history_file')
    
    def test_daily_checker_with_config(self):
        """Test DailyProviderChecker with configuration file."""
        from daily_provider_check import DailyProviderChecker
        
        # Create test config
        test_config = {
            "providers": {
                "openai": {
                    "url": "https://api.openai.com/v1/models",
                    "timeout": 10,
                    "expected_status": 200
                },
                "groq": {
                    "url": "https://api.groq.com/openai/v1/models",
                    "timeout": 15,
                    "expected_status": 200
                }
            },
            "schedule": {
                "time": "09:00",
                "timezone": "UTC",
                "retry_interval": 300
            },
            "alerts": {
                "consecutive_failures": 3,
                "response_time_threshold": 5000
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        checker = DailyProviderChecker(config_file=str(self.config_file))
        
        assert len(checker.providers) == 2
        assert "openai" in checker.providers
        assert "groq" in checker.providers
        assert checker.check_schedule["time"] == "09:00"
        assert checker.alert_thresholds["consecutive_failures"] == 3
    
    @patch('daily_provider_check.requests.get')
    def test_provider_health_check_success(self, mock_get):
        """Test successful provider health check."""
        from daily_provider_check import DailyProviderChecker
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
        mock_response.elapsed.total_seconds.return_value = 0.15
        mock_get.return_value = mock_response
        
        checker = DailyProviderChecker()
        result = checker.check_provider_health("openai")
        
        assert result["status"] == "healthy"
        assert result["response_code"] == 200
        assert result["response_time_ms"] == 150
        assert result["timestamp"] is not None
    
    @patch('daily_provider_check.requests.get')
    def test_provider_health_check_failure(self, mock_get):
        """Test failed provider health check."""
        from daily_provider_check import DailyProviderChecker
        
        # Mock failed response
        mock_get.side_effect = Exception("Connection timeout")
        
        checker = DailyProviderChecker()
        result = checker.check_provider_health("openai")
        
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert result["timestamp"] is not None
    
    @patch('daily_provider_check.requests.get')
    def test_provider_health_check_slow_response(self, mock_get):
        """Test provider health check with slow response."""
        from daily_provider_check import DailyProviderChecker
        
        # Mock slow response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 6.0  # 6 seconds
        mock_get.return_value = mock_response
        
        checker = DailyProviderChecker()
        result = checker.check_provider_health("openai")
        
        assert result["status"] == "degraded"
        assert result["response_time_ms"] == 6000
        assert "warning" in result
    
    @patch('daily_provider_check.DailyProviderChecker.check_provider_health')
    def test_run_all_provider_checks(self, mock_check):
        """Test running health checks for all providers."""
        from daily_provider_check import DailyProviderChecker
        
        # Mock health check results
        mock_check.side_effect = [
            {"status": "healthy", "response_time_ms": 150, "timestamp": "2026-01-10T09:00:00Z"},
            {"status": "unhealthy", "error": "Connection failed", "timestamp": "2026-01-10T09:00:01Z"},
            {"status": "degraded", "response_time_ms": 6000, "timestamp": "2026-01-10T09:00:02Z"}
        ]
        
        checker = DailyProviderChecker()
        results = checker.run_all_checks()
        
        assert len(results) == 3
        assert mock_check.call_count == 3
        
        # Check results
        healthy_count = sum(1 for r in results if r["status"] == "healthy")
        unhealthy_count = sum(1 for r in results if r["status"] == "unhealthy")
        degraded_count = sum(1 for r in results if r["status"] == "degraded")
        
        assert healthy_count == 1
        assert unhealthy_count == 1
        assert degraded_count == 1
    
    def test_save_check_results_to_history(self):
        """Test saving check results to history file."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker(history_file=str(self.history_file))
        
        # Mock check results
        check_results = {
            "date": "2026-01-10",
            "timestamp": "2026-01-10T09:00:00Z",
            "providers": {
                "openai": {"status": "healthy", "response_time_ms": 150},
                "groq": {"status": "unhealthy", "error": "Connection failed"}
            }
        }
        
        checker.save_to_history(check_results)
        
        assert self.history_file.exists()
        
        # Verify content
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        assert "2026-01-10" in history
        assert history["2026-01-10"]["providers"]["openai"]["status"] == "healthy"
    
    def test_load_historical_data(self):
        """Test loading historical data from file."""
        from daily_provider_check import DailyProviderChecker
        
        # Create test history file
        test_history = {
            "2026-01-09": {
                "timestamp": "2026-01-09T09:00:00Z",
                "providers": {
                    "openai": {"status": "healthy", "response_time_ms": 120}
                }
            },
            "2026-01-08": {
                "timestamp": "2026-01-08T09:00:00Z",
                "providers": {
                    "openai": {"status": "degraded", "response_time_ms": 8000}
                }
            }
        }
        
        with open(self.history_file, 'w') as f:
            json.dump(test_history, f)
        
        checker = DailyProviderChecker(history_file=str(self.history_file))
        history = checker.load_history()
        
        assert len(history) == 2
        assert "2026-01-09" in history
        assert "2026-01-08" in history
        assert history["2026-01-09"]["providers"]["openai"]["status"] == "healthy"
    
    def test_analyze_historical_trends(self):
        """Test historical trend analysis."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        # Mock historical data
        checker.historical_data = {
            "2026-01-09": {"providers": {"openai": {"status": "healthy", "response_time_ms": 150}}},
            "2026-01-08": {"providers": {"openai": {"status": "healthy", "response_time_ms": 120}}},
            "2026-01-07": {"providers": {"openai": {"status": "degraded", "response_time_ms": 6000}}},
            "2026-01-06": {"providers": {"openai": {"status": "healthy", "response_time_ms": 100}}},
        }
        
        trends = checker.analyze_trends("openai", days=7)
        
        assert "availability_percentage" in trends
        assert "average_response_time" in trends
        assert "status_changes" in trends
        assert "recommendations" in trends
        
        # Should show 75% availability (3/4 healthy days)
        assert trends["availability_percentage"] == 75.0
    
    def test_generate_daily_report(self):
        """Test daily report generation."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        # Mock check results
        check_results = {
            "date": "2026-01-10",
            "timestamp": "2026-01-10T09:00:00Z",
            "providers": {
                "openai": {"status": "healthy", "response_time_ms": 150},
                "groq": {"status": "unhealthy", "error": "Connection failed"},
                "together": {"status": "healthy", "response_time_ms": 200}
            }
        }
        
        # Mock historical data for trend analysis
        checker.historical_data = {
            "2026-01-09": {"providers": {"openai": {"status": "healthy"}}},
            "2026-01-08": {"providers": {"openai": {"status": "healthy"}}}
        }
        
        report = checker.generate_daily_report(check_results)
        
        assert "summary" in report
        assert "provider_status" in report
        assert "trends" in report
        assert "alerts" in report
        assert "recommendations" in report
        
        assert report["summary"]["total_providers"] == 3
        assert report["summary"]["healthy_providers"] == 2
        assert report["summary"]["unhealthy_providers"] == 1
    
    def test_check_alert_conditions(self):
        """Test alert condition checking."""
        from daily_provider_check import DailyProviderChecker
        
        checker = DailyProviderChecker()
        
        # Test consecutive failures alert
        recent_results = [
            {"status": "unhealthy", "timestamp": "2026-01-10T09:00:00Z"},
            {"status": "unhealthy", "timestamp": "2026-01-09T09:00:00Z"},
            {"status": "unhealthy", "timestamp": "2026-01-08T09:00:00Z"},
        ]
        
        alerts = checker.check_alert_conditions("openai", recent_results)
        
        assert len(alerts) > 0
        assert any("consecutive failures" in alert["message"].lower() for alert in alerts)
    
    @patch('daily_provider_check.DailyProviderChecker.run_all_checks')
    @patch('daily_provider_check.DailyProviderChecker.generate_daily_report')
    @patch('daily_provider_check.DailyProviderChecker.save_to_history')
    def test_run_daily_check_cycle(self, mock_save, mock_report, mock_checks):
        """Test complete daily check cycle."""
        from daily_provider_check import DailyProviderChecker
        
        # Mock the cycle components
        mock_checks.return_value = {
            "date": "2026-01-10",
            "providers": {"openai": {"status": "healthy"}}
        }
        mock_report.return_value = {"summary": {"total_providers": 1}}
        
        checker = DailyProviderChecker()
        checker.run_daily_cycle()
        
        mock_checks.assert_called_once()
        mock_report.assert_called_once()
        mock_save.assert_called_once()
    
    def test_cleanup_old_history(self):
        """Test cleanup of old historical data."""
        from daily_provider_check import DailyProviderChecker
        
        # Create old history file (90 days old)
        old_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        recent_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        test_history = {
            old_date: {"providers": {"openai": {"status": "healthy"}}},
            recent_date: {"providers": {"openai": {"status": "healthy"}}}
        }
        
        with open(self.history_file, 'w') as f:
            json.dump(test_history, f)
        
        checker = DailyProviderChecker(history_file=str(self.history_file))
        checker.cleanup_old_history(days_to_keep=30)
        
        # Reload and verify old data was removed
        updated_history = checker.load_history()
        
        assert len(updated_history) == 1
        assert recent_date in updated_history
        assert old_date not in updated_history


class TestDailyCheckScheduler:
    """Test daily check scheduling functionality."""
    
    @patch('daily_provider_check.DailyProviderChecker.run_daily_cycle')
    def test_scheduled_execution(self, mock_cycle):
        """Test scheduled execution of daily checks."""
        from daily_provider_check import DailyCheckScheduler
        
        scheduler = DailyCheckScheduler()
        
        # Mock current time to be 09:00 UTC
        with patch('daily_provider_check.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 9
            mock_datetime.now.return_value.minute = 0
            
            scheduler.check_and_run()
        
        mock_cycle.assert_called_once()
    
    @patch('daily_provider_check.DailyProviderChecker.run_daily_cycle')
    def test_scheduled_execution_wrong_time(self, mock_cycle):
        """Test that checks don't run at wrong time."""
        from daily_provider_check import DailyCheckScheduler
        
        scheduler = DailyCheckScheduler()
        
        # Mock current time to be 14:00 UTC (not 09:00)
        with patch('daily_provider_check.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 14
            mock_datetime.now.return_value.minute = 0
            
            scheduler.check_and_run()
        
        mock_cycle.assert_not_called()
    
    def test_scheduler_configuration(self):
        """Test scheduler configuration."""
        from daily_provider_check import DailyCheckScheduler
        
        scheduler = DailyCheckScheduler(
            run_time="10:30",
            timezone="America/New_York",
            retry_interval=600
        )
        
        assert scheduler.run_time == "10:30"
        assert scheduler.timezone == "America/New_York"
        assert scheduler.retry_interval == 600


class TestDailyCheckCLI:
    """Test daily check command line interface."""
    
    @patch('daily_provider_check.DailyProviderChecker.run_daily_cycle')
    def test_cli_run_now(self, mock_cycle):
        """Test CLI run now command."""
        from daily_provider_check import main
        
        with patch('sys.argv', ['daily_provider_check.py', '--run-now']):
            main()
        
        mock_cycle.assert_called_once()
    
    @patch('daily_provider_check.DailyCheckScheduler.start_scheduler')
    def test_cli_start_scheduler(self, mock_scheduler):
        """Test CLI start scheduler command."""
        from daily_provider_check import main
        
        with patch('sys.argv', ['daily_provider_check.py', '--start-scheduler']):
            main()
        
        mock_scheduler.assert_called_once()
    
    @patch('daily_provider_check.DailyProviderChecker.analyze_trends')
    def test_cli_analyze_trends(self, mock_trends):
        """Test CLI analyze trends command."""
        from daily_provider_check import main
        
        with patch('sys.argv', ['daily_provider_check.py', '--analyze', '--provider', 'openai']):
            main()
        
        mock_trends.assert_called_once()
    
    def test_cli_help_output(self):
        """Test CLI help output."""
        from daily_provider_check import main
        
        with patch('sys.argv', ['daily_provider_check.py', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Help command exits with 0
