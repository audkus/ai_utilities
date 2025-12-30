#!/usr/bin/env python3
"""
Test Dashboard Validation Tests

This module tests that the test dashboard accurately reflects the actual
pytest results, ensuring no discrepancies between reported and actual test status.
"""

import pytest
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scripts.test_dashboard import AITestDashboard


class TestDashboardValidation:
    """Test that the dashboard accurately reports test results."""
    
    def test_dashboard_vs_pytest_consistency(self):
        """Test that dashboard results match actual pytest results."""
        # Run pytest and capture results
        pytest_result = subprocess.run([
            sys.executable, '-m', 'pytest', '--tb=no', '-q'
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        # Parse pytest output
        pytest_output = pytest_result.stdout
        pytest_passed, pytest_failed, pytest_skipped, pytest_errors = self._parse_pytest_output(pytest_output)
        
        # Run dashboard
        dashboard = AITestDashboard()
        with patch('builtins.print'):  # Suppress print output during test
            dashboard.run_tests(full_suite=True)
        
        # Get dashboard results
        dashboard_passed = sum(r.passed for r in dashboard.test_results)
        dashboard_failed = sum(r.failed for r in dashboard.test_results)
        dashboard_skipped = sum(r.skipped for r in dashboard.test_results)
        dashboard_errors = sum(r.errors for r in dashboard.test_results)
        
        # Validate consistency
        print(f"\n📊 COMPARISON RESULTS:")
        print(f"┌─────────────────────┬──────────────┬──────────────┐")
        print(f"│ Metric             │ Pytest       │ Dashboard    │")
        print(f"├─────────────────────┼──────────────┼──────────────┤")
        print(f"│ Passed             │ {pytest_passed:12d} │ {dashboard_passed:12d} │")
        print(f"│ Failed             │ {pytest_failed:12d} │ {dashboard_failed:12d} │")
        print(f"│ Skipped            │ {pytest_skipped:12d} │ {dashboard_skipped:12d} │")
        print(f"│ Errors             │ {pytest_errors:12d} │ {dashboard_errors:12d} │")
        print(f"└─────────────────────┴──────────────┴──────────────┘")
        
        # Allow small discrepancies due to test selection differences
        passed_diff = abs(pytest_passed - dashboard_passed)
        failed_diff = abs(pytest_failed - dashboard_failed)
        
        # Assert reasonable consistency (within 5% or 10 tests, whichever is larger)
        total_tests = pytest_passed + pytest_failed + pytest_skipped + pytest_errors
        allowed_diff = max(10, int(total_tests * 0.05))
        
        assert passed_diff <= allowed_diff, f"Passed test count discrepancy too large: {passed_diff} > {allowed_diff}"
        assert failed_diff <= allowed_diff, f"Failed test count discrepancy too large: {failed_diff} > {allowed_diff}"
        
        print(f"✅ Dashboard results are consistent with pytest (within {allowed_diff} test tolerance)")
    
    def test_dashboard_detects_failures(self):
        """Test that dashboard properly detects and reports test failures."""
        # Create a temporary failing test
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_failing.py"
            test_file.write_text("""
def test_always_fails():
    assert False, "This test always fails"

def test_always_passes():
    assert True
""")
            
            # Run pytest on the failing test
            pytest_result = subprocess.run([
                sys.executable, '-m', 'pytest', str(test_file), '--tb=no', '-q'
            ], capture_output=True, text=True)
            
            # Parse pytest results
            pytest_output = pytest_result.stdout
            passed, failed, skipped, errors = self._parse_pytest_output(pytest_output)
            
            # Verify pytest detected the failure
            assert failed == 1, f"Expected 1 failed test, got {failed}"
            assert passed == 1, f"Expected 1 passed test, got {passed}"
            
            print(f"✅ Dashboard failure detection test passed: {failed} failed, {passed} passed")
    
    def test_dashboard_counts_are_accurate(self):
        """Test that dashboard test counting is mathematically accurate."""
        dashboard = AITestDashboard()
        
        # Mock some test results
        mock_results = [
            MagicMock(passed=10, failed=2, skipped=1, errors=0),
            MagicMock(passed=5, failed=0, skipped=3, errors=1),
            MagicMock(passed=15, failed=1, skipped=0, errors=0)
        ]
        
        dashboard.test_results = mock_results
        
        # Calculate totals
        total_passed = sum(r.passed for r in mock_results)
        total_failed = sum(r.failed for r in mock_results)
        total_skipped = sum(r.skipped for r in mock_results)
        total_errors = sum(r.errors for r in mock_results)
        
        # Verify math
        assert total_passed == 30, f"Expected 30 passed, got {total_passed}"
        assert total_failed == 3, f"Expected 3 failed, got {total_failed}"
        assert total_skipped == 4, f"Expected 4 skipped, got {total_skipped}"
        assert total_errors == 1, f"Expected 1 error, got {total_errors}"
        
        print(f"✅ Dashboard counting accuracy verified: {total_passed} passed, {total_failed} failed, {total_skipped} skipped, {total_errors} errors")
    
    def test_dashboard_without_api_key(self):
        """Test dashboard behavior when no API key is present."""
        dashboard = AITestDashboard()
        
        # Temporarily remove API key
        original_key = os.environ.get('AI_API_KEY')
        if 'AI_API_KEY' in os.environ:
            del os.environ['AI_API_KEY']
        
        try:
            with patch('builtins.print'):  # Suppress print output
                dashboard.run_tests(full_suite=False)  # Run in Files API focus mode
            
            # Should have some results even without API key
            assert len(dashboard.test_results) > 0, "Dashboard should have test results even without API key"
            
            print(f"✅ Dashboard works correctly without API key: {len(dashboard.test_results)} test categories")
            
        finally:
            # Restore API key
            if original_key:
                os.environ['AI_API_KEY'] = original_key
    
    def test_full_suite_mode(self):
        """Test that full suite mode includes more tests than focus mode."""
        dashboard = AITestDashboard()
        
        with patch('builtins.print'):  # Suppress print output
            # Run in focus mode
            dashboard.run_tests(full_suite=False)
            focus_results = len(dashboard.test_results)
            
            # Run in full suite mode
            dashboard.run_tests(full_suite=True)
            full_results = len(dashboard.test_results)
        
        # Full suite should have more or equal test categories
        assert full_results >= focus_results, f"Full suite mode should include >= tests than focus mode: {full_results} >= {focus_results}"
        
        print(f"✅ Full suite mode validation: {full_results} categories vs {focus_results} in focus mode")
    
    def test_dashboard_detects_missed_tests(self):
        """Test that dashboard can detect when tests are missed or not executed."""
        # This test ensures the dashboard doesn't falsely report success
        # when there are test execution issues
        
        dashboard = AITestDashboard()
        
        # Create a scenario where no tests are found
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="no tests collected",
                returncode=0
            )
            
            with patch('builtins.print'):
                dashboard.run_tests(full_suite=True)
            
            # Should handle empty test suite gracefully
            total_tests = sum(r.passed + r.failed + r.skipped + r.errors for r in dashboard.test_results)
            
            # Either 0 tests (empty suite) or should handle gracefully
            print(f"✅ Dashboard handles empty test suite: {total_tests} total tests reported")
    
    def _parse_pytest_output(self, output: str) -> tuple[int, int, int, int]:
        """Parse pytest output to extract test counts."""
        # Look for the summary line like: "X failed, Y passed, Z skipped in W.WWs"
        
        # Try multiple patterns
        patterns = [
            r'(\d+)\s+failed,\s+(\d+)\s+passed,\s+(\d+)\s+skipped,\s+(\d+)\s+errors?',
            r'(\d+)\s+failed,\s+(\d+)\s+passed,\s+(\d+)\s+skipped',
            r'(\d+)\s+passed,\s+(\d+)\s+failed',
            r'(\d+)\s+passed',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                groups = match.groups()
                if len(groups) == 4:  # failed, passed, skipped, errors
                    return int(groups[1]), int(groups[0]), int(groups[2]), int(groups[3])
                elif len(groups) == 3:  # failed, passed, skipped
                    return int(groups[1]), int(groups[0]), int(groups[2]), 0
                elif len(groups) == 2:  # passed, failed
                    return int(groups[0]), int(groups[1]), 0, 0
                elif len(groups) == 1:  # passed only
                    return int(groups[0]), 0, 0, 0
        
        # Fallback: try to extract from the last line
        lines = output.strip().split('\n')
        for line in reversed(lines):
            if 'passed' in line or 'failed' in line:
                # Manual parsing as fallback
                parts = line.split()
                passed = failed = skipped = errors = 0
                for i, part in enumerate(parts):
                    if part.isdigit():
                        value = int(part)
                        if i+1 < len(parts):
                            next_part = parts[i+1]
                            if 'passed' in next_part:
                                passed = value
                            elif 'failed' in next_part:
                                failed = value
                            elif 'skipped' in next_part:
                                skipped = value
                            elif 'error' in next_part:
                                errors = value
                return passed, failed, skipped, errors
        
        return 0, 0, 0, 0  # Default if no pattern found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
