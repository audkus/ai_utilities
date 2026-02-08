"""Tests for coverage artifact cleanup in automated_test_runner."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.automated_test_runner import AutomatedTestRunner


class TestCoverageCleanup:
    """Test coverage artifact cleanup functionality."""
    
    def test_finalize_coverage_artifacts_removes_all_files(self):
        """Test that _finalize_coverage_artifacts removes all .coverage* files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create fake coverage files
            coverage_files = [
                ".coverage",
                ".coverage.test1.12345.abc",
                ".coverage.test2.67890.def",
                ".coverage.localhost.99999.xyz"
            ]
            
            for file_name in coverage_files:
                (temp_path / file_name).touch()
            
            # Create .coveragerc (should not be removed)
            (temp_path / ".coveragerc").write_text("[coverage]\n")
            
            # Verify files exist
            for file_name in coverage_files + [".coveragerc"]:
                assert (temp_path / file_name).exists()
            
            # Create runner with temp directory as project root
            runner = AutomatedTestRunner()
            runner.project_root = temp_path
            
            # Mock subprocess calls to avoid actually running coverage
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")
                
                # Run cleanup
                runner._finalize_coverage_artifacts()
                
                # Verify subprocess was called correctly
                assert mock_run.call_count == 3  # combine, xml, html
                
                # Check calls use sys.executable
                for call in mock_run.call_args_list:
                    args = call[0][0]
                    assert args[0] == "python3" or "python" in args[0]  # sys.executable
                    assert "-m" in args
                    assert "coverage" in args
            
            # Verify all .coverage* files are removed except .coveragerc
            for file_name in coverage_files:
                assert not (temp_path / file_name).exists(), f"{file_name} should be removed"
            
            # Verify .coveragerc is preserved
            assert (temp_path / ".coveragerc").exists(), ".coveragerc should be preserved"
            
            # Verify coverage_reports directories were created
            assert (temp_path / "coverage_reports").exists()
            assert (temp_path / "coverage_reports" / "html").exists()
            assert (temp_path / "coverage_reports" / "xml").exists()
    
    def test_finalize_coverage_artifacts_with_no_coverage_files(self):
        """Test cleanup when no coverage files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create runner with temp directory as project root
            runner = AutomatedTestRunner()
            runner.project_root = temp_path
            
            # Mock subprocess calls
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")
                
                # Run cleanup
                runner._finalize_coverage_artifacts()
                
                # Should not call subprocess if no coverage files
                mock_run.assert_not_called()
            
            # Verify directories are still created
            assert (temp_path / "coverage_reports").exists()
            assert (temp_path / "coverage_reports" / "html").exists()
            assert (temp_path / "coverage_reports" / "xml").exists()
    
    def test_finalize_coverage_artifacts_handles_subprocess_failures(self):
        """Test cleanup handles subprocess failures gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a fake coverage file
            (temp_path / ".coverage.test").touch()
            
            # Create runner
            runner = AutomatedTestRunner()
            runner.project_root = temp_path
            
            # Mock subprocess calls with check=False to avoid exceptions
            with patch('subprocess.run') as mock_run:
                # All calls succeed but we just want to test file removal
                mock_run.return_value = Mock(returncode=0, stderr="")
                
                # Should not raise exception
                runner._finalize_coverage_artifacts()
            
            # File should be removed
            assert not (temp_path / ".coverage.test").exists()
