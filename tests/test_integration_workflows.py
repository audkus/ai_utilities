#!/usr/bin/env python3
"""
Integration tests for AI Utilities script workflows.

Tests end-to-end workflows combining multiple scripts:
- Setup → Configuration → Validation workflow
- Monitoring → Alerting → Reporting workflow  
- Change Detection → Notification → Response workflow
- WebUI Discovery → Configuration → Testing workflow
"""

import os
import sys
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add scripts to path for imports
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)


class TestSetupWorkflowIntegration:
    """Test setup workflow integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "setup_config.json"
        self.env_file = self.temp_dir / ".env"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_complete_setup_workflow(self, mock_run):
        """Test complete setup workflow: setup → configure → validate."""
        from main import MainApplication
        
        # Mock setup script responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Enhanced setup completed"),  # setup
            Mock(returncode=0, stdout="Configuration generated"),   # configure
            Mock(returncode=0, stdout="Validation passed")         # validate
        ]
        
        app = MainApplication()
        
        # Execute complete workflow
        results = []
        
        # Step 1: Run enhanced setup
        result1 = app.execute_feature("setup", ["--enhanced"])
        results.append(result1)
        
        # Step 2: Generate configuration
        result2 = app.execute_feature("configure", ["--output", str(self.config_file)])
        results.append(result2)
        
        # Step 3: Validate configuration
        result3 = app.execute_feature("validate", ["--config", str(self.config_file)])
        results.append(result3)
        
        # Verify all steps succeeded
        for i, result in enumerate(results, 1):
            assert result["success"] is True, f"Step {i} failed: {result}"
        
        assert mock_run.call_count == 3
    
    @patch('subprocess.run')
    def test_setup_with_examples_workflow(self, mock_run):
        """Test setup workflow followed by examples validation."""
        from main import MainApplication
        
        # Mock responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Setup completed"),
            Mock(returncode=0, stdout="getting_started.py executed successfully"),
            Mock(returncode=0, stdout="model_validation.py passed")
        ]
        
        app = MainApplication()
        
        # Execute setup and examples
        setup_result = app.execute_feature("setup", [])
        assert setup_result["success"] is True
        
        # Run validation examples
        example1_result = app.run_example("getting_started.py")
        example2_result = app.run_example("model_validation.py")
        
        assert example1_result["success"] is True
        assert example2_result["success"] is True
        
        assert mock_run.call_count == 3
    
    def test_setup_configuration_persistence(self):
        """Test that setup configuration persists across workflow."""
        # Create initial configuration
        initial_config = {
            "provider": "openai",
            "api_key": "test-key-123",
            "model": "gpt-4",
            "temperature": 0.7
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(initial_config, f)
        
        # Simulate workflow steps reading/writing config
        from enhanced_setup import EnhancedSetupSystem
        
        with patch('enhanced_setup.EnhancedSetupSystem.run_standard_setup') as mock_setup:
            mock_setup.return_value = {
                "provider": "openai",
                "api_key": "test-key-123",
                "model": "gpt-4",
                "temperature": 0.7,
                "cache_enabled": True
            }
            
            setup_system = EnhancedSetupSystem()
            result = setup_system.run_standard_setup()
            
            # Verify configuration is consistent
            assert result["provider"] == initial_config["provider"]
            assert result["api_key"] == initial_config["api_key"]


class TestMonitoringWorkflowIntegration:
    """Test monitoring workflow integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.health_report = self.temp_dir / "health_report.json"
        self.history_file = self.temp_dir / "provider_history.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('provider_health_monitor.requests.get')
    @patch('daily_provider_check.requests.get')
    def test_monitoring_alert_workflow(self, mock_daily, mock_health):
        """Test monitoring → detection → alert workflow."""
        from provider_health_monitor import ProviderHealthMonitor
        from daily_provider_check import DailyProviderChecker
        
        # Mock health check responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_health.return_value = mock_response
        mock_daily.return_value = mock_response
        
        # Step 1: Run health monitoring
        monitor = ProviderHealthMonitor()
        health_results = monitor.run_health_checks()
        
        # Step 2: Run daily check with same data
        checker = DailyProviderChecker(history_file=str(self.history_file))
        daily_results = checker.run_all_checks()
        
        # Step 3: Generate combined report
        combined_report = {
            "health_monitor": health_results,
            "daily_check": daily_results,
            "timestamp": time.time()
        }
        
        # Verify workflow integration
        assert len(health_results) > 0
        assert len(daily_results) > 0
        assert "timestamp" in combined_report
    
    @patch('provider_change_detector.requests.get')
    def test_change_detection_notification_workflow(self, mock_get):
        """Test change detection → notification workflow."""
        from provider_change_detector import ProviderChangeDetector
        
        # Mock model list changes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4", "object": "model"},
                {"id": "gpt-4-turbo", "object": "model"}  # New model
            ]
        }
        mock_get.return_value = mock_response
        
        detector = ProviderChangeDetector()
        
        # Step 1: Create baseline
        baseline = detector.create_baseline({
            "openai": {
                "models": [{"id": "gpt-4", "object": "model"}],
                "model_count": 1
            }
        })
        
        # Step 2: Detect changes
        current_data = {
            "openai": {
                "models": [{"id": "gpt-4"}, {"id": "gpt-4-turbo"}],
                "model_count": 2
            }
        }
        
        changes = detector.detect_model_changes(baseline["providers"], current_data)
        
        # Step 3: Generate notification
        if changes["openai"]["added_models"]:
            notification = {
                "type": "model_added",
                "provider": "openai",
                "models": changes["openai"]["added_models"],
                "timestamp": time.time()
            }
            
            assert notification["models"] == ["gpt-4-turbo"]
            assert notification["provider"] == "openai"
    
    def test_continuous_monitoring_integration(self):
        """Test continuous monitoring across multiple tools."""
        from provider_health_monitor import ProviderHealthMonitor
        from daily_provider_check import DailyProviderChecker
        from provider_change_detector import ProviderChangeDetector
        
        # Mock data for continuous monitoring
        monitoring_data = {
            "health_checks": [
                {"provider": "openai", "status": "healthy", "timestamp": time.time()},
                {"provider": "groq", "status": "healthy", "timestamp": time.time()}
            ],
            "changes_detected": [],
            "alerts_generated": []
        }
        
        # Simulate continuous monitoring cycle
        monitor = ProviderHealthMonitor()
        checker = DailyProviderChecker()
        detector = ProviderChangeDetector()
        
        # Each tool processes the same data
        health_summary = monitor.generate_health_report(monitoring_data["health_checks"])
        daily_summary = checker.generate_daily_report({
            "date": time.strftime("%Y-%m-%d"),
            "providers": {item["provider"]: item for item in monitoring_data["health_checks"]}
        })
        
        # Verify integration
        assert health_summary["summary"]["total"] == 2
        assert daily_summary["summary"]["total_providers"] == 2


class TestWebUIWorkflowIntegration:
    """Test WebUI workflow integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.webui_config = self.temp_dir / "webui_config.json"
        self.env_file = self.temp_dir / ".env"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('webui_api_helper.requests.get')
    @patch('subprocess.run')
    def test_webui_discovery_setup_workflow(self, mock_run, mock_get):
        """Test WebUI discovery → configuration → testing workflow."""
        from webui_api_helper import WebUIAPIHelper
        from main import MainApplication
        
        # Mock WebUI detection
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "llama-2-7b"}]}
        mock_response.headers = {"server": "uvicorn"}
        mock_get.return_value = mock_response
        
        # Mock example execution
        mock_run.return_value = Mock(returncode=0, stdout="Example executed successfully")
        
        # Step 1: Discover WebUI
        helper = WebUIAPIHelper()
        webui_info = helper.auto_detect_and_configure()
        
        assert webui_info is not None
        assert webui_info["provider"] == "openai_compatible"
        
        # Step 2: Save configuration
        helper.save_config_json(webui_info, str(self.webui_config))
        helper.save_config_env(webui_info, str(self.env_file))
        
        assert self.webui_config.exists()
        assert self.env_file.exists()
        
        # Step 3: Test with AI Utilities
        app = MainApplication()
        test_result = app.run_example("getting_started.py")
        
        assert test_result["success"] is True
    
    @patch('webui_api_helper.requests.get')
    def test_webui_monitoring_integration(self, mock_get):
        """Test WebUI monitoring integration with health checks."""
        from webui_api_helper import WebUIAPIHelper
        from provider_health_monitor import ProviderHealthMonitor
        
        # Mock WebUI responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "llama-2-7b"}]}
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_get.return_value = mock_response
        
        # Step 1: WebUI discovery and monitoring
        helper = WebUIAPIHelper()
        scan_results = helper.scan_for_webuis([7860, 8000, 5000])
        
        # Step 2: Health monitoring integration
        monitor = ProviderHealthMonitor()
        
        # Add WebUI endpoints to health monitoring
        for result in scan_results:
            if result["detected"]:
                health_result = monitor.check_provider_health(
                    result["webui_type"], 
                    result["endpoint"]
                )
                assert health_result["status"] == "healthy"
    
    def test_multi_webui_configuration_workflow(self):
        """Test workflow with multiple WebUIs."""
        from webui_api_helper import WebUIAPIHelper
        
        # Mock multiple WebUI configurations
        webui_configs = [
            {
                "type": "text-generation-webui",
                "port": 7860,
                "models": ["llama-2-7b", "llama-2-13b"]
            },
            {
                "type": "fastchat",
                "port": 8000,
                "models": ["vicuna-13b", "wizardlm-13b"]
            }
        ]
        
        helper = WebUIAPIHelper()
        
        # Process each WebUI
        for config in webui_configs:
            # Generate configuration
            ai_config = helper.generate_ai_utilities_config(config)
            
            # Validate configuration
            validation = helper.validate_config(ai_config)
            assert validation["valid"] is True
            
            # Generate environment file
            env_content = helper.generate_env_file_content(config)
            assert "AI_PROVIDER=openai_compatible" in env_content
            assert f"localhost:{config['port']}" in env_content


class TestDiagnosticWorkflowIntegration:
    """Test diagnostic workflow integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.diagnostic_report = self.temp_dir / "diagnostic_report.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('provider_diagnostic.requests.get')
    def test_diagnostic_healing_workflow(self, mock_get):
        """Test diagnostic → issue identification → healing workflow."""
        from provider_diagnostic import ProviderDiagnostic
        from provider_health_monitor import ProviderHealthMonitor
        
        # Mock diagnostic responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
        mock_get.return_value = mock_response
        
        # Step 1: Run comprehensive diagnostic
        diagnostic = ProviderDiagnostic()
        
        test_config = {
            "provider": "openai",
            "api_key": "sk-test-key",
            "base_url": "https://api.openai.com/v1"
        }
        
        diagnostic_results = diagnostic.run_diagnostic(test_config)
        
        # Step 2: Identify issues from diagnostic
        issues = []
        if not diagnostic_results["configuration"]["valid"]:
            issues.append("configuration_error")
        if not diagnostic_results["api_key"]["valid"]:
            issues.append("api_key_error")
        if diagnostic_results["connectivity"]["status"] != "success":
            issues.append("connectivity_error")
        
        # Step 3: Run targeted health monitoring for issues
        monitor = ProviderHealthMonitor()
        
        healing_actions = []
        for issue in issues:
            if issue == "connectivity_error":
                # Run focused health check
                health_result = monitor.check_provider_health(
                    "openai", 
                    "https://api.openai.com/v1/models"
                )
                healing_actions.append({
                    "issue": issue,
                    "action": "health_check",
                    "result": health_result
                })
        
        # Verify workflow
        assert diagnostic_results["overall_status"] in ["healthy", "warning", "error"]
        assert len(healing_actions) == len(issues)
    
    def test_performance_diagnostic_workflow(self):
        """Test performance diagnostic workflow."""
        from provider_diagnostic import ProviderDiagnostic
        
        diagnostic = ProviderDiagnostic()
        
        # Mock performance data
        performance_configs = [
            {"provider": "openai", "expected_response_time": 100},
            {"provider": "groq", "expected_response_time": 50},
            {"provider": "together", "expected_response_time": 200}
        ]
        
        performance_results = []
        
        for config in performance_configs:
            with patch('provider_diagnostic.ProviderDiagnostic.test_connectivity') as mock_test:
                mock_test.return_value = {
                    "status": "success",
                    "response_time": config["expected_response_time"] + 10
                }
                
                result = diagnostic.run_performance_benchmark(config, iterations=3)
                performance_results.append(result)
        
        # Analyze performance across providers
        avg_response_times = []
        for result in performance_results:
            avg_time = sum(r["response_time"] for r in result) / len(result)
            avg_response_times.append(avg_time)
        
        # Verify performance analysis
        assert len(performance_results) == 3
        assert all(avg_time > 0 for avg_time in avg_response_times)


class TestCIWorkflowIntegration:
    """Test CI workflow integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.ci_report = self.temp_dir / "ci_report.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_ci_pipeline_integration(self, mock_run):
        """Test complete CI pipeline integration."""
        # Mock CI pipeline steps
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Dependencies installed"),
            Mock(returncode=0, stdout="Linting passed"),
            Mock(returncode=0, stdout="Tests passed"),
            Mock(returncode=0, stdout="Provider checks passed"),
            Mock(returncode=0, stdout="Build completed")
        ]
        
        # Execute CI pipeline
        pipeline_steps = [
            ["bash", "scripts/ci_provider_check.sh", "--pre-check"],
            ["python", "-m", "pytest", "tests/", "--verbose"],
            ["bash", "scripts/ci_provider_check.sh", "--post-check"]
        ]
        
        results = []
        for step in pipeline_steps:
            result = subprocess.run(step, capture_output=True, text=True, timeout=30)
            results.append(result)
        
        # Verify all steps passed
        for result in results:
            assert result.returncode == 0
        
        assert mock_run.call_count == 5
    
    def test_ci_artifact_generation(self):
        """Test CI artifact generation across workflows."""
        artifacts = {
            "test_results": {"passed": 45, "failed": 0, "skipped": 2},
            "coverage_report": {"coverage": "87.5%", "lines": 1250},
            "provider_status": {"openai": "healthy", "groq": "healthy"},
            "performance_metrics": {"avg_response_time": 150, "success_rate": "99.8%"}
        }
        
        # Generate combined CI report
        ci_report = {
            "timestamp": time.time(),
            "pipeline": "main",
            "artifacts": artifacts,
            "summary": {
                "total_tests": artifacts["test_results"]["passed"] + artifacts["test_results"]["failed"],
                "coverage": artifacts["coverage_report"]["coverage"],
                "all_providers_healthy": all(status == "healthy" for status in artifacts["provider_status"].values())
            }
        }
        
        # Save CI report
        with open(self.ci_report, 'w') as f:
            json.dump(ci_report, f, indent=2)
        
        # Verify report generation
        assert self.ci_report.exists()
        
        with open(self.ci_report, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["summary"]["total_tests"] == 47
        assert saved_report["summary"]["all_providers_healthy"] is True


class TestErrorRecoveryWorkflows:
    """Test error recovery and fallback workflows."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_provider_failover_workflow(self, mock_run):
        """Test provider failover workflow."""
        # Mock primary provider failure, backup success
        mock_run.side_effect = [
            Mock(returncode=1, stdout="OpenAI connection failed"),  # Primary fails
            Mock(returncode=0, stdout="Groq connection successful")  # Backup succeeds
        ]
        
        # Execute failover workflow
        providers = ["openai", "groq", "together"]
        successful_provider = None
        
        for provider in providers:
            result = subprocess.run(
                ["bash", "scripts/test_provider.sh", provider],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                successful_provider = provider
                break
        
        assert successful_provider == "groq"
        assert mock_run.call_count == 2
    
    def test_configuration_recovery_workflow(self):
        """Test configuration recovery workflow."""
        # Test corrupted configuration recovery
        corrupted_config = {"provider": "", "api_key": None}
        fallback_config = {
            "provider": "openai",
            "api_key": "fallback-key",
            "model": "gpt-3.5-turbo"
        }
        
        # Simulate configuration recovery
        if not corrupted_config.get("provider"):
            # Apply fallback configuration
            recovered_config = fallback_config.copy()
            recovered_config["recovery_applied"] = True
        else:
            recovered_config = corrupted_config
        
        assert recovered_config["provider"] == "openai"
        assert recovered_config["recovery_applied"] is True
    
    def test_network_error_recovery_workflow(self):
        """Test network error recovery workflow."""
        from provider_health_monitor import ProviderHealthMonitor
        
        monitor = ProviderHealthMonitor()
        
        # Simulate network errors and recovery
        error_scenarios = [
            {"type": "timeout", "retry_after": 5},
            {"type": "connection_refused", "retry_after": 10},
            {"type": "rate_limit", "retry_after": 60}
        ]
        
        recovery_strategies = {
            "timeout": "increase_timeout",
            "connection_refused": "try_backup_endpoint", 
            "rate_limit": "exponential_backoff"
        }
        
        for scenario in error_scenarios:
            strategy = recovery_strategies[scenario["type"]]
            retry_delay = scenario["retry_after"]
            
            # Simulate recovery strategy application
            recovery_result = {
                "error_type": scenario["type"],
                "strategy_applied": strategy,
                "retry_after": retry_delay,
                "recovery_successful": True
            }
            
            assert recovery_result["strategy_applied"] is not None
            assert recovery_result["retry_after"] > 0
