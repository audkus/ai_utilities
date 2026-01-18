#!/usr/bin/env python3
"""
Tests for provider_change_detector.py script.

Tests the provider change detection functionality including:
- Model availability monitoring
- API endpoint changes
- Pricing updates detection
- Configuration change notifications
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


class TestProviderChangeDetector:
    """Test provider change detector functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "detector_config.json"
        self.baseline_file = self.temp_dir / "provider_baseline.json"
        self.report_file = self.temp_dir / "change_report.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_change_detector_initialization(self):
        """Test ProviderChangeDetector initialization."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        assert hasattr(detector, 'providers')
        assert hasattr(detector, 'baseline_data')
        assert hasattr(detector, 'change_thresholds')
        assert hasattr(detector, 'notification_methods')
    
    def test_change_detector_with_config(self):
        """Test ProviderChangeDetector with configuration file."""
        from provider_change_detector import ProviderChangeDetector
        
        # Create test config
        test_config = {
            "providers": {
                "openai": {
                    "models_endpoint": "https://api.openai.com/v1/models",
                    "pricing_endpoint": "https://openai.com/pricing",
                    "check_interval": 3600
                },
                "groq": {
                    "models_endpoint": "https://api.groq.com/openai/v1/models",
                    "pricing_endpoint": "https://groq.com/pricing",
                    "check_interval": 1800
                }
            },
            "thresholds": {
                "model_count_change": 5,
                "price_change_percent": 10,
                "endpoint_response_time": 5000
            },
            "notifications": {
                "email": {"enabled": False},
                "webhook": {"enabled": True, "url": "https://hooks.slack.com/test"}
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        detector = ProviderChangeDetector(config_file=str(self.config_file))
        
        assert len(detector.providers) == 2
        assert "openai" in detector.providers
        assert "groq" in detector.providers
        assert detector.change_thresholds["model_count_change"] == 5
        assert detector.notification_methods["webhook"]["enabled"] is True
    
    @patch('provider_change_detector.requests.get')
    def test_fetch_provider_models_success(self, mock_get):
        """Test successful provider models fetch."""
        from provider_change_detector import ProviderChangeDetector
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4", "object": "model"},
                {"id": "gpt-3.5-turbo", "object": "model"},
                {"id": "text-davinci-003", "object": "model"}
            ]
        }
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_get.return_value = mock_response
        
        detector = ProviderChangeDetector()
        result = detector.fetch_provider_models("openai", "https://api.openai.com/v1/models")
        
        assert result["status"] == "success"
        assert len(result["models"]) == 3
        assert result["response_time_ms"] == 200
        assert result["timestamp"] is not None
        assert "gpt-4" in [model["id"] for model in result["models"]]
    
    @patch('provider_change_detector.requests.get')
    def test_fetch_provider_models_failure(self, mock_get):
        """Test failed provider models fetch."""
        from provider_change_detector import ProviderChangeDetector
        
        # Mock failed response
        mock_get.side_effect = Exception("API unavailable")
        
        detector = ProviderChangeDetector()
        result = detector.fetch_provider_models("openai", "https://api.openai.com/v1/models")
        
        assert result["status"] == "failed"
        assert "error" in result
        assert result["timestamp"] is not None
    
    @patch('provider_change_detector.requests.get')
    def test_fetch_pricing_information(self, mock_get):
        """Test fetching pricing information."""
        from provider_change_detector import ProviderChangeDetector
        
        # Mock pricing page response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <body>
            <div class="pricing-table">
                <div class="model-price" data-model="gpt-4">$0.03/1K tokens</div>
                <div class="model-price" data-model="gpt-3.5-turbo">$0.002/1K tokens</div>
            </div>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        detector = ProviderChangeDetector()
        result = detector.fetch_pricing_info("openai", "https://openai.com/pricing")
        
        assert result["status"] == "success"
        assert "pricing" in result
        assert "gpt-4" in result["pricing"]
        assert result["pricing"]["gpt-4"] == "$0.03/1K tokens"
    
    def test_create_baseline_snapshot(self):
        """Test creating baseline snapshot."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Mock current provider data
        current_data = {
            "openai": {
                "models": [
                    {"id": "gpt-4", "object": "model"},
                    {"id": "gpt-3.5-turbo", "object": "model"}
                ],
                "pricing": {"gpt-4": "$0.03/1K tokens"},
                "endpoint_status": "healthy",
                "last_checked": "2026-01-10T12:00:00Z"
            },
            "groq": {
                "models": [
                    {"id": "mixtral-8x7b-32768", "object": "model"}
                ],
                "pricing": {"mixtral-8x7b-32768": "$0.24/1K tokens"},
                "endpoint_status": "healthy",
                "last_checked": "2026-01-10T12:00:00Z"
            }
        }
        
        baseline = detector.create_baseline(current_data)
        
        assert "timestamp" in baseline
        assert "providers" in baseline
        assert "metadata" in baseline
        assert baseline["providers"]["openai"]["model_count"] == 2
        assert baseline["providers"]["groq"]["model_count"] == 1
    
    def test_save_and_load_baseline(self):
        """Test saving and loading baseline data."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector(baseline_file=str(self.baseline_file))
        
        # Create test baseline
        test_baseline = {
            "timestamp": "2026-01-10T12:00:00Z",
            "providers": {
                "openai": {
                    "models": ["gpt-4", "gpt-3.5-turbo"],
                    "model_count": 2,
                    "pricing": {"gpt-4": "$0.03/1K tokens"}
                }
            },
            "metadata": {"version": "1.0"}
        }
        
        detector.save_baseline(test_baseline)
        
        assert self.baseline_file.exists()
        
        # Load and verify
        loaded_baseline = detector.load_baseline()
        
        assert loaded_baseline["timestamp"] == "2026-01-10T12:00:00Z"
        assert loaded_baseline["providers"]["openai"]["model_count"] == 2
        assert loaded_baseline["metadata"]["version"] == "1.0"
    
    def test_detect_model_changes(self):
        """Test detecting model changes."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Baseline data
        baseline = {
            "openai": {
                "models": ["gpt-4", "gpt-3.5-turbo", "text-davinci-003"],
                "model_count": 3
            }
        }
        
        # Current data
        current = {
            "openai": {
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],  # text-davinci-003 removed, gpt-4-turbo added
                "model_count": 3
            }
        }
        
        changes = detector.detect_model_changes(baseline, current)
        
        assert "openai" in changes
        assert "added_models" in changes["openai"]
        assert "removed_models" in changes["openai"]
        assert "gpt-4-turbo" in changes["openai"]["added_models"]
        assert "text-davinci-003" in changes["openai"]["removed_models"]
    
    def test_detect_pricing_changes(self):
        """Test detecting pricing changes."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Baseline pricing
        baseline = {
            "openai": {
                "pricing": {"gpt-4": "$0.03/1K tokens", "gpt-3.5-turbo": "$0.002/1K tokens"}
            }
        }
        
        # Current pricing
        current = {
            "openai": {
                "pricing": {"gpt-4": "$0.035/1K tokens", "gpt-3.5-turbo": "$0.002/1K tokens"}
            }
        }
        
        changes = detector.detect_pricing_changes(baseline, current)
        
        assert "openai" in changes
        assert "price_changes" in changes["openai"]
        assert "gpt-4" in changes["openai"]["price_changes"]
        assert changes["openai"]["price_changes"]["gpt-4"]["old_price"] == "$0.03/1K tokens"
        assert changes["openai"]["price_changes"]["gpt-4"]["new_price"] == "$0.035/1K tokens"
    
    def test_detect_endpoint_changes(self):
        """Test detecting endpoint changes."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Baseline endpoints
        baseline = {
            "openai": {
                "endpoint_status": "healthy",
                "response_time_ms": 150,
                "available_endpoints": ["https://api.openai.com/v1"]
            }
        }
        
        # Current endpoints
        current = {
            "openai": {
                "endpoint_status": "degraded",
                "response_time_ms": 5000,
                "available_endpoints": ["https://api.openai.com/v1", "https://api.openai.com/v2"]
            }
        }
        
        changes = detector.detect_endpoint_changes(baseline, current)
        
        assert "openai" in changes
        assert "status_change" in changes["openai"]
        assert "performance_change" in changes["openai"]
        assert "new_endpoints" in changes["openai"]
        assert changes["openai"]["status_change"]["old_status"] == "healthy"
        assert changes["openai"]["status_change"]["new_status"] == "degraded"
    
    @patch('provider_change_detector.ProviderChangeDetector.fetch_provider_models')
    @patch('provider_change_detector.ProviderChangeDetector.fetch_pricing_info')
    def test_run_change_detection_cycle(self, mock_pricing, mock_models):
        """Test complete change detection cycle."""
        from provider_change_detector import ProviderChangeDetector
        
        # Mock data fetching
        mock_models.return_value = {
            "status": "success",
            "models": [{"id": "gpt-4"}, {"id": "gpt-4-turbo"}],
            "response_time_ms": 200
        }
        mock_pricing.return_value = {
            "status": "success",
            "pricing": {"gpt-4": "$0.035/1K tokens"}
        }
        
        # Create baseline
        baseline = {
            "openai": {
                "models": [{"id": "gpt-4"}],
                "pricing": {"gpt-4": "$0.03/1K tokens"}
            }
        }
        
        detector = ProviderChangeDetector()
        detector.baseline_data = baseline
        
        changes = detector.run_detection_cycle()
        
        assert "openai" in changes
        assert "model_changes" in changes["openai"]
        assert "pricing_changes" in changes["openai"]
        assert len(changes["openai"]["model_changes"]["added_models"]) == 1
    
    def test_generate_change_report(self):
        """Test change report generation."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Mock detected changes
        detected_changes = {
            "openai": {
                "model_changes": {
                    "added_models": ["gpt-4-turbo"],
                    "removed_models": ["text-davinci-003"]
                },
                "pricing_changes": {
                    "gpt-4": {
                        "old_price": "$0.03/1K tokens",
                        "new_price": "$0.035/1K tokens",
                        "change_percent": 16.67
                    }
                },
                "endpoint_changes": {
                    "status_change": {
                        "old_status": "healthy",
                        "new_status": "degraded"
                    }
                }
            }
        }
        
        report = detector.generate_change_report(detected_changes)
        
        assert "summary" in report
        assert "detailed_changes" in report
        assert "impact_assessment" in report
        assert "recommendations" in report
        assert "timestamp" in report
        
        assert report["summary"]["total_changes"] == 3
        assert report["summary"]["providers_affected"] == 1
        assert len(report["detailed_changes"]["openai"]["model_changes"]["added_models"]) == 1
    
    def test_save_change_report(self):
        """Test saving change report to file."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        test_report = {
            "summary": {"total_changes": 2, "providers_affected": 1},
            "detailed_changes": {
                "openai": {"model_changes": {"added_models": ["gpt-4-turbo"]}}
            },
            "timestamp": "2026-01-10T12:00:00Z"
        }
        
        detector.save_change_report(test_report, self.report_file)
        
        assert self.report_file.exists()
        
        # Verify content
        with open(self.report_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["summary"]["total_changes"] == 2
        assert len(saved_report["detailed_changes"]["openai"]["model_changes"]["added_models"]) == 1
    
    @patch('provider_change_detector.ProviderChangeDetector.run_detection_cycle')
    @patch('provider_change_detector.ProviderChangeDetector.generate_change_report')
    @patch('provider_change_detector.ProviderChangeDetector.save_change_report')
    def test_run_scheduled_detection(self, mock_save, mock_report, mock_cycle):
        """Test scheduled change detection."""
        from provider_change_detector import ProviderChangeDetector
        
        # Mock detection cycle
        mock_cycle.return_value = {"openai": {"model_changes": {}}}
        mock_report.return_value = {"summary": {"total_changes": 1}}
        
        detector = ProviderChangeDetector()
        detector.run_scheduled_detection(output_file=str(self.report_file))
        
        mock_cycle.assert_called_once()
        mock_report.assert_called_once()
        mock_save.assert_called_once()
    
    @patch('provider_change_detector.requests.post')
    def test_send_webhook_notification(self, mock_post):
        """Test sending webhook notification."""
        from provider_change_detector import ProviderChangeDetector
        
        # Mock successful webhook response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        detector = ProviderChangeDetector()
        
        test_report = {
            "summary": {"total_changes": 1},
            "detailed_changes": {"openai": {"model_changes": {}}}
        }
        
        result = detector.send_webhook_notification(
            "https://hooks.slack.com/test",
            test_report
        )
        
        assert result["status"] == "sent"
        assert result["response_code"] == 200
        mock_post.assert_called_once()
    
    def test_check_change_significance(self):
        """Test change significance assessment."""
        from provider_change_detector import ProviderChangeDetector
        
        detector = ProviderChangeDetector()
        
        # Test significant change (model addition)
        model_change = {
            "added_models": ["gpt-4-turbo"],
            "removed_models": []
        }
        
        significance = detector.assess_change_significance("model_changes", model_change)
        
        assert significance["is_significant"] is True
        assert significance["severity"] in ["low", "medium", "high"]
        assert "reason" in significance
        
        # Test insignificant change (minor price change)
        price_change = {
            "gpt-3.5-turbo": {
                "old_price": "$0.002/1K tokens",
                "new_price": "$0.0021/1K tokens",
                "change_percent": 5.0
            }
        }
        
        significance = detector.assess_change_significance("pricing_changes", price_change)
        
        assert significance["is_significant"] is False  # Below 10% threshold


class TestChangeDetectorCLI:
    """Test change detector command line interface."""
    
    @patch('provider_change_detector.ProviderChangeDetector.run_scheduled_detection')
    def test_cli_run_detection(self, mock_detection):
        """Test CLI run detection command."""
        from provider_change_detector import main
        
        with patch('sys.argv', ['provider_change_detector.py', '--detect']):
            main()
        
        mock_detection.assert_called_once()
    
    @patch('provider_change_detector.ProviderChangeDetector.create_baseline')
    def test_cli_create_baseline(self, mock_baseline):
        """Test CLI create baseline command."""
        from provider_change_detector import main
        
        with patch('sys.argv', ['provider_change_detector.py', '--create-baseline']):
            main()
        
        mock_baseline.assert_called_once()
    
    @patch('provider_change_detector.ProviderChangeDetector.detect_model_changes')
    def test_cli_compare_with_baseline(self, mock_compare):
        """Test CLI compare with baseline command."""
        from provider_change_detector import main
        
        with patch('sys.argv', ['provider_change_detector.py', '--compare']):
            main()
        
        mock_compare.assert_called_once()
    
    def test_cli_help_output(self):
        """Test CLI help output."""
        from provider_change_detector import main
        
        with patch('sys.argv', ['provider_change_detector.py', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Help command exits with 0
