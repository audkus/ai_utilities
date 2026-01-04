#!/usr/bin/env python3
"""
Tests for coverage_summary.py script.

Tests the coverage reporting functionality including report generation,
badge creation, and CLI interface.
"""

import os
import sys
import json
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


class TestCoverageSummary:
    """Test coverage summary script functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.coverage_file = self.temp_dir / ".coverage"
        self.json_file = self.temp_dir / "coverage.json"
        self.output_dir = self.temp_dir / "coverage_reports"
        
        # Mock coverage data
        self.mock_coverage_data = {
            "totals": {
                "num_statements": 1000,
                "covered_statements": 850,
                "num_lines": 950,
                "covered_lines": 820,
                "num_branches": 200,
                "covered_branches": 160,
                "percent_covered": 85.0
            },
            "files": {
                "src/ai_utilities/client.py": {
                    "summary": {
                        "num_statements": 100,
                        "covered_statements": 95,
                        "percent_covered": 95.0
                    }
                },
                "src/ai_utilities/providers/base_provider.py": {
                    "summary": {
                        "num_statements": 50,
                        "covered_statements": 40,
                        "percent_covered": 80.0
                    }
                }
            }
        }
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_coverage_metrics_dataclass(self):
        """Test CoverageMetrics dataclass."""
        from coverage_summary import CoverageMetrics
        
        metrics = CoverageMetrics(
            total_statements=1000,
            covered_statements=850,
            total_lines=950,
            covered_lines=820,
            total_branches=200,
            covered_branches=160,
            percentage=85.0,
            missing_lines=[1, 2, 3]
        )
        
        assert metrics.total_statements == 1000
        assert metrics.covered_statements == 850
        assert metrics.percentage == 85.0
        assert metrics.missing_lines == [1, 2, 3]
    
    def test_coverage_reporter_initialization(self):
        """Test CoverageReporter initialization."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(
            coverage_file=str(self.coverage_file),
            output_dir=str(self.output_dir)
        )
        
        assert reporter.coverage_file == self.coverage_file
        assert reporter.output_dir == self.output_dir
        assert self.output_dir.exists()
    
    @patch('subprocess.run')
    def test_run_coverage_success(self, mock_run):
        """Test successful coverage run."""
        from coverage_summary import CoverageReporter
        
        # Mock successful subprocess call
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Coverage report generated"
        )
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        result = reporter.run_coverage("tests/")
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check the command was called correctly
        call_args = mock_run.call_args[0][0]
        assert "pytest" in call_args
        assert "--cov=src/ai_utilities" in call_args
        assert "--cov-report=json" in call_args
    
    @patch('subprocess.run')
    def test_run_coverage_failure(self, mock_run):
        """Test failed coverage run."""
        from coverage_summary import CoverageReporter
        
        # Mock failed subprocess call
        mock_run.return_value = Mock(
            returncode=1,
            stderr="Coverage failed"
        )
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        result = reporter.run_coverage("tests/")
        
        assert result is False
    
    @patch('subprocess.run')
    def test_run_coverage_not_installed(self, mock_run):
        """Test coverage when pytest not installed."""
        from coverage_summary import CoverageReporter
        
        # Mock FileNotFoundError
        mock_run.side_effect = FileNotFoundError()
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        result = reporter.run_coverage("tests/")
        
        assert result is False
    
    def test_parse_coverage_json_success(self):
        """Test successful JSON parsing."""
        from coverage_summary import CoverageReporter
        
        # Create mock coverage.json file
        with open(self.json_file, 'w') as f:
            json.dump(self.mock_coverage_data, f)
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        result = reporter.parse_coverage_json(str(self.json_file))
        
        assert result is not None
        assert result["totals"]["percent_covered"] == 85.0
    
    def test_parse_coverage_json_file_not_found(self):
        """Test JSON parsing when file doesn't exist."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        result = reporter.parse_coverage_json("nonexistent.json")
        
        assert result is None
    
    def test_extract_metrics(self):
        """Test metrics extraction from coverage data."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        metrics = reporter.extract_metrics(self.mock_coverage_data)
        
        assert metrics.total_statements == 1000
        assert metrics.covered_statements == 850
        assert metrics.percentage == 85.0
    
    def test_generate_summary_report(self):
        """Test summary report generation."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        report = reporter.generate_summary_report(self.mock_coverage_data)
        
        assert "📊 Test Coverage Report" in report
        assert "85.0%" in report
        assert "src/ai_utilities/client.py" in report
        assert "Good coverage" in report
    
    def test_generate_badge_excellent(self):
        """Test badge generation for excellent coverage."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        badge = reporter.generate_badge(95.0)
        
        assert "#4c1" in badge  # Green color for excellent
        assert "95%" in badge
        assert "<svg" in badge
    
    def test_generate_badge_good(self):
        """Test badge generation for good coverage."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        badge = reporter.generate_badge(85.0)
        
        assert "#dfb317" in badge  # Yellow color for good
        assert "85%" in badge
    
    def test_generate_badge_poor(self):
        """Test badge generation for poor coverage."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        badge = reporter.generate_badge(65.0)
        
        assert "#e05d44" in badge  # Red color for poor
        assert "65%" in badge
    
    def test_save_reports(self):
        """Test saving all reports."""
        from coverage_summary import CoverageReporter
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        reporter.save_reports(self.mock_coverage_data)
        
        # Check files were created
        assert (self.output_dir / "coverage_report.md").exists()
        assert (self.output_dir / "coverage_badge.svg").exists()
        assert (self.output_dir / "coverage_summary.json").exists()
        
        # Check content
        with open(self.output_dir / "coverage_summary.json") as f:
            summary = json.load(f)
        
        assert summary["percentage"] == 85.0
        assert summary["quality"] == "good"
    
    def test_print_summary(self):
        """Test console summary printing."""
        from coverage_summary import CoverageReporter
        from io import StringIO
        import sys
        
        reporter = CoverageReporter(output_dir=str(self.output_dir))
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        reporter.print_summary(self.mock_coverage_data)
        
        sys.stdout = sys.__stdout__  # Restore stdout
        
        output = captured_output.getvalue()
        assert "Coverage: 85.0%" in output
        assert "Good coverage" in output
    
    @patch('coverage_summary.CoverageReporter.run_coverage')
    @patch('coverage_summary.CoverageReporter.parse_coverage_json')
    @patch('coverage_summary.CoverageReporter.save_reports')
    def test_main_function(self, mock_save, mock_parse, mock_run):
        """Test main function with mocked dependencies."""
        from coverage_summary import main
        
        # Mock successful operations
        mock_run.return_value = True
        mock_parse.return_value = self.mock_coverage_data
        
        # Mock sys.argv
        with patch('sys.argv', ['coverage_summary.py', '--run-coverage']):
            main()
        
        # Verify functions were called
        mock_run.assert_called_once()
        mock_parse.assert_called_once()
        mock_save.assert_called_once()
    
    def test_cli_help(self):
        """Test CLI help functionality."""
        result = subprocess.run(
            [sys.executable, 'scripts/coverage_summary.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert result.returncode == 0
        assert "Generate test coverage reports" in result.stdout
        assert "--run-coverage" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
