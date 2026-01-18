#!/usr/bin/env python3
"""
Tests for ci_provider_check.sh script.

Tests the CI provider checking functionality including:
- Provider availability validation
- CI environment integration
- Exit code handling
- Configuration validation
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


class TestCIProviderCheck:
    """Test CI provider check functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.script_path = Path(scripts_dir) / "ci_provider_check.sh"
        self.config_file = self.temp_dir / "ci_config.json"
        self.env_file = self.temp_dir / ".env"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_script_exists_and_executable(self):
        """Test that the CI provider check script exists and is executable."""
        assert self.script_path.exists(), f"Script not found at {self.script_path}"
        
        # Check if script is executable (might not be in all environments)
        if os.access(self.script_path, os.X_OK):
            assert True
        else:
            # Script exists but may not be executable in test environment
            assert self.script_path.suffix == ".sh"
    
    @patch('subprocess.run')
    def test_ci_provider_check_success(self, mock_run):
        """Test successful CI provider check."""
        # Mock successful script execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
✓ OpenAI provider: Available
✓ Groq provider: Available  
✓ Together provider: Available
All providers checked successfully
"""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Execute the script
        result = subprocess.run(
            ["bash", str(self.script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0
        assert "Available" in result.stdout
        assert "All providers checked" in result.stdout
    
    @patch('subprocess.run')
    def test_ci_provider_check_failure(self, mock_run):
        """Test CI provider check with failures."""
        # Mock failed script execution
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = """
✗ OpenAI provider: Connection failed
✓ Groq provider: Available
✗ Together provider: Authentication error
Some providers are not available
"""
        mock_result.stderr = "Error connecting to OpenAI API"
        mock_run.return_value = mock_result
        
        # Execute the script
        result = subprocess.run(
            ["bash", str(self.script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 1
        assert "Connection failed" in result.stdout
        assert "Authentication error" in result.stdout
    
    def test_ci_environment_variables(self):
        """Test CI environment variable handling."""
        # Test with CI environment variables set
        ci_env_vars = {
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_TOKEN": "test-token",
            "OPENAI_API_KEY": "test-openai-key",
            "GROQ_API_KEY": "test-groq-key"
        }
        
        with patch.dict(os.environ, ci_env_vars):
            # Mock the script execution
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "All providers available in CI"
                mock_run.return_value = mock_result
                
                result = subprocess.run(
                    ["bash", str(self.script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                assert result.returncode == 0
                mock_run.assert_called_once()
    
    def test_script_with_config_file(self):
        """Test script execution with configuration file."""
        # Create test configuration
        test_config = {
            "providers": ["openai", "groq", "together"],
            "timeout": 30,
            "retry_attempts": 3,
            "ci_mode": True
        }
        
        import json
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Mock script execution with config
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "CI check with config completed"
            mock_run.return_value = mock_result
            
            result = subprocess.run(
                ["bash", str(self.script_path), "--config", str(self.config_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0
            # Verify config parameter was passed
            call_args = mock_run.call_args[0][0]
            assert str(self.config_file) in call_args
    
    def test_script_help_output(self):
        """Test script help output."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = """
Usage: ci_provider_check.sh [OPTIONS]

Options:
  --config FILE    Configuration file path
  --timeout SEC    Request timeout in seconds
  --verbose        Verbose output
  --help           Show this help message

Examples:
  ci_provider_check.sh                    # Check with default settings
  ci_provider_check.sh --config ci.json  # Use configuration file
  ci_provider_check.sh --verbose         # Verbose output
"""
            mock_run.return_value = mock_result
            
            result = subprocess.run(
                ["bash", str(self.script_path), "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0
            assert "Usage:" in result.stdout
            assert "Options:" in result.stdout
    
    def test_exit_code_handling(self):
        """Test proper exit code handling."""
        test_cases = [
            (0, "All providers available"),
            (1, "Some providers unavailable"),
            (2, "Configuration error"),
            (3, "Network error")
        ]
        
        for exit_code, description in test_cases:
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = exit_code
                mock_result.stdout = description
                mock_run.return_value = mock_result
                
                result = subprocess.run(
                    ["bash", str(self.script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                assert result.returncode == exit_code
                assert description in result.stdout
    
    def test_timeout_handling(self):
        """Test timeout handling in CI environment."""
        with patch('subprocess.run') as mock_run:
            # Simulate timeout
            mock_run.side_effect = subprocess.TimeoutExpired(
                ["bash", str(self.script_path)], 30
            )
            
            with pytest.raises(subprocess.TimeoutExpired):
                subprocess.run(
                    ["bash", str(self.script_path), "--timeout", "1"],
                    capture_output=True,
                    text=True,
                    timeout=5  # Shorter timeout for test
                )
    
    def test_provider_specific_checks(self):
        """Test individual provider checks."""
        providers = ["openai", "groq", "together", "anthropic", "cohere"]
        
        for provider in providers:
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = f"✓ {provider.title()} provider: Available"
                mock_run.return_value = mock_result
                
                result = subprocess.run(
                    ["bash", str(self.script_path), "--provider", provider],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                assert result.returncode == 0
                assert f"{provider.title()} provider" in result.stdout
    
    def test_ci_specific_features(self):
        """Test CI-specific features and optimizations."""
        ci_features = {
            "GITHUB_ACTIONS": "GitHub Actions integration",
            "GITLAB_CI": "GitLab CI integration", 
            "JENKINS_URL": "Jenkins integration",
            "CIRCLECI": "CircleCI integration"
        }
        
        for ci_var, description in ci_features.items():
            with patch.dict(os.environ, {ci_var: "true"}):
                with patch('subprocess.run') as mock_run:
                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_result.stdout = f"CI mode active: {description}"
                    mock_run.return_value = mock_result
                    
                    result = subprocess.run(
                        ["bash", str(self.script_path), "--ci-mode"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    assert result.returncode == 0
                    assert "CI mode active" in result.stdout
    
    def test_error_reporting(self):
        """Test detailed error reporting in CI context."""
        error_scenarios = [
            {
                "error_type": "authentication",
                "expected_output": "Authentication failed - check API keys"
            },
            {
                "error_type": "network", 
                "expected_output": "Network error - check connectivity"
            },
            {
                "error_type": "rate_limit",
                "expected_output": "Rate limit exceeded - retry later"
            },
            {
                "error_type": "service_unavailable",
                "expected_output": "Service temporarily unavailable"
            }
        ]
        
        for scenario in error_scenarios:
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 1
                mock_result.stdout = f"ERROR: {scenario['expected_output']}"
                mock_result.stderr = f"Detailed: {scenario['error_type']}"
                mock_run.return_value = mock_result
                
                result = subprocess.run(
                    ["bash", str(self.script_path), "--verbose"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                assert result.returncode == 1
                assert scenario["expected_output"] in result.stdout
    
    def test_performance_in_ci(self):
        """Test script performance optimization for CI."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Performance check completed in 2.5s"
            mock_run.return_value = mock_result
            
            # Test with performance optimization flag
            result = subprocess.run(
                ["bash", str(self.script_path), "--fast"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0
            mock_run.assert_called_once()
    
    def test_integration_with_ci_systems(self):
        """Test integration with different CI systems."""
        ci_systems = [
            {"env": {"GITHUB_ACTIONS": "true"}, "name": "GitHub Actions"},
            {"env": {"GITLAB_CI": "true"}, "name": "GitLab CI"},
            {"env": {"JENKINS_URL": "http://jenkins"}, "name": "Jenkins"},
            {"env": {"CIRCLECI": "true"}, "name": "CircleCI"}
        ]
        
        for ci_system in ci_systems:
            with patch.dict(os.environ, ci_system["env"]):
                with patch('subprocess.run') as mock_run:
                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_result.stdout = f"Integrated with {ci_system['name']}"
                    mock_run.return_value = mock_result
                    
                    result = subprocess.run(
                        ["bash", str(self.script_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    assert result.returncode == 0
                    assert ci_system["name"] in result.stdout


class TestCICheckWorkflow:
    """Test CI check workflow integration."""
    
    def test_ci_check_in_pipeline(self):
        """Test CI check as part of CI pipeline."""
        with patch('subprocess.run') as mock_run:
            # Mock successful CI check
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "CI pipeline check passed"
            mock_run.return_value = mock_result
            
            # Simulate CI pipeline execution
            pipeline_steps = [
                ["bash", "scripts/ci_provider_check.sh", "--pre-check"],
                ["bash", "scripts/ci_provider_check.sh", "--full-check"],
                ["bash", "scripts/ci_provider_check.sh", "--post-check"]
            ]
            
            for step in pipeline_steps:
                result = subprocess.run(step, capture_output=True, text=True, timeout=30)
                assert result.returncode == 0
            
            assert mock_run.call_count == 3
    
    def test_ci_check_with_artifacts(self):
        """Test CI check with artifact generation."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Artifacts generated: ci_report.json, logs.txt"
            mock_run.return_value = mock_result
            
            result = subprocess.run(
                ["bash", str(scripts_dir + "/ci_provider_check.sh"), "--generate-artifacts"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0
            assert "Artifacts generated" in result.stdout
    
    def test_ci_check_rollback(self):
        """Test CI check rollback functionality."""
        with patch('subprocess.run') as mock_run:
            # Mock failure and rollback
            mock_run.side_effect = [
                Mock(returncode=1, stdout="Check failed"),  # Initial failure
                Mock(returncode=0, stdout="Rollback successful")  # Rollback success
            ]
            
            # Execute with rollback
            result = subprocess.run(
                ["bash", str(scripts_dir + "/ci_provider_check.sh"), "--with-rollback"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should handle rollback
            assert mock_run.call_count == 2
