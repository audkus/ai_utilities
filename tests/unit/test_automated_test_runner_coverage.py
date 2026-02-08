"""Tests for coverage artifact cleanup in automated_test_runner."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.automated_test_runner import AutomatedTestRunner


class TestCoverageCleanup:
    """Test coverage artifact cleanup functionality."""
    
    def test_finalize_coverage_removes_all_files(self):
        """Test that _finalize_coverage removes all .coverage* files."""
        # Create fake coverage files in the real repo root
        repo_root = Path(__file__).resolve().parents[2]
        test_files = []
        coverage_files = [
            ".coverage.test1.12345.abc",
            ".coverage.test2.67890.def", 
            ".coverage.localhost.99999.xyz"
        ]
        
        try:
            for file_name in coverage_files:
                test_file = repo_root / file_name
                test_file.touch()
                test_files.append(test_file)
            
            # Verify files exist
            for test_file in test_files:
                assert test_file.exists()
            
            # Create runner and run cleanup
            runner = AutomatedTestRunner()
            runner._finalize_coverage()
            
            # Files should be removed
            for test_file in test_files:
                assert not test_file.exists(), f"{test_file.name} should be removed"
                
        finally:
            # Clean up any remaining test files
            for test_file in test_files:
                if test_file.exists():
                    test_file.unlink()
    
    def test_finalize_coverage_preserves_coveragerc(self):
        """Test that .coveragerc is preserved."""
        repo_root = Path(__file__).resolve().parents[2]
        coveragerc = repo_root / ".coveragerc"
        
        # Ensure .coveragerc exists
        if not coveragerc.exists():
            coveragerc.write_text("[coverage]\n")
        
        try:
            # Create runner and run cleanup
            runner = AutomatedTestRunner()
            runner._finalize_coverage()
            
            # .coveragerc should be preserved
            assert coveragerc.exists(), ".coveragerc should be preserved"
        except Exception:
            # If test fails, ensure we don't delete the real .coveragerc
            if not coveragerc.exists():
                coveragerc.write_text("[coverage]\n")
            raise
    
    def test_finalize_coverage_creates_directories(self):
        """Test that coverage directories are created."""
        # Create runner and run cleanup
        runner = AutomatedTestRunner()
        runner._finalize_coverage()
        
        # Verify directories are created
        repo_root = Path(__file__).resolve().parents[2]
        assert (repo_root / "coverage_reports").exists()
        assert (repo_root / "coverage_reports" / "html").exists()
        assert (repo_root / "coverage_reports" / "xml").exists()
    
    def test_finalize_coverage_handles_no_files_gracefully(self):
        """Test cleanup when no coverage files exist."""
        # Create runner and run cleanup - should not fail
        runner = AutomatedTestRunner()
        runner._finalize_coverage()
        
        # Should complete without error
        assert True
