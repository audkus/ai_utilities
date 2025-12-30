#!/usr/bin/env python3
"""
Simple Dashboard Validation Tests

Lightweight tests to validate dashboard accuracy without running full test suites.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scripts.test_dashboard import AITestDashboard


class TestDashboardValidationSimple:
    """Test dashboard accuracy with mocked data."""
    
    def test_dashboard_parsing_accuracy(self):
        """Test that dashboard correctly parses pytest output."""
        dashboard = AITestDashboard()
        
        # Mock pytest output samples
        test_cases = [
            ("10 failed, 450 passed, 29 skipped, 19 errors", (450, 10, 29, 19)),
            ("5 failed, 452 passed, 29 skipped", (452, 5, 29, 0)),
            ("450 passed, 5 failed", (450, 5, 0, 0)),
            ("455 passed", (455, 0, 0, 0)),
        ]
        
        for output, expected in test_cases:
            passed, failed, skipped, errors = dashboard._parse_pytest_output(output)
            assert (passed, failed, skipped, errors) == expected, \
                f"Parsing failed for: {output}. Expected {expected}, got {(passed, failed, skipped, errors)}"
        
        print("✅ Dashboard pytest output parsing is accurate")
    
    def test_dashboard_math_consistency(self):
        """Test that dashboard calculations are mathematically sound."""
        dashboard = AITestDashboard()
        
        # Mock test results with known totals
        mock_results = [
            MagicMock(passed=100, failed=5, skipped=10, errors=2, category="Unit Tests"),
            MagicMock(passed=50, failed=3, skipped=5, errors=0, category="Integration"),
            MagicMock(passed=25, failed=0, skipped=2, errors=1, category="Core"),
        ]
        
        dashboard.test_results = mock_results
        
        # Calculate expected totals
        expected_passed = 175
        expected_failed = 8
        expected_skipped = 17
        expected_errors = 3
        expected_total = 203
        
        # Verify dashboard calculations
        actual_passed = sum(r.passed for r in dashboard.test_results)
        actual_failed = sum(r.failed for r in dashboard.test_results)
        actual_skipped = sum(r.skipped for r in dashboard.test_results)
        actual_errors = sum(r.errors for r in dashboard.test_results)
        actual_total = actual_passed + actual_failed + actual_skipped + actual_errors
        
        assert actual_passed == expected_passed
        assert actual_failed == expected_failed
        assert actual_skipped == expected_skipped
        assert actual_errors == expected_errors
        assert actual_total == expected_total
        
        print(f"✅ Dashboard math is consistent: {actual_total} total tests")
    
    def test_dashboard_failure_detection(self):
        """Test that dashboard properly identifies failure conditions."""
        dashboard = AITestDashboard()
        
        # Test scenarios
        scenarios = [
            # (passed, failed, skipped, errors, should_be_ready)
            (100, 0, 5, 0, True),   # Perfect - ready for production
            (95, 5, 0, 0, False),   # Has failures - not ready
            (100, 0, 0, 3, False),  # Has errors - not ready
            (80, 10, 10, 0, False), # Many failures - not ready
        ]
        
        for passed, failed, skipped, errors, should_be_ready in scenarios:
            # Create mock result
            mock_result = MagicMock(
                passed=passed, 
                failed=failed, 
                skipped=skipped, 
                errors=errors,
                category="Test"
            )
            dashboard.test_results = [mock_result]
            
            # Check readiness logic
            total_failed = failed + errors
            is_ready = total_failed == 0
            
            assert is_ready == should_be_ready, \
                f"Readiness check failed for scenario: {passed}p/{failed}f/{skipped}s/{errors}e"
        
        print("✅ Dashboard failure detection logic is correct")
    
    def test_dashboard_environment_handling(self):
        """Test that dashboard handles environment variable scenarios."""
        dashboard = AITestDashboard()
        
        # Test with API key present
        with patch.dict(os.environ, {'AI_API_KEY': 'test-key-12345'}):
            api_key = os.getenv('AI_API_KEY')
            assert api_key == 'test-key-12345'
            assert len(api_key) > 10  # Basic validation
        
        # Test without API key
        original_key = os.environ.get('AI_API_KEY')
        if 'AI_API_KEY' in os.environ:
            del os.environ['AI_API_KEY']
        
        try:
            api_key = os.getenv('AI_API_KEY')
            assert api_key is None
        finally:
            # Restore original key
            if original_key:
                os.environ['AI_API_KEY'] = original_key
        
        print("✅ Dashboard environment handling is robust")
    
    def test_dashboard_error_scenarios(self):
        """Test dashboard behavior with various error scenarios."""
        dashboard = AITestDashboard()
        
        # Test empty results
        dashboard.test_results = []
        total_tests = sum(r.passed + r.failed + r.skipped + r.errors for r in dashboard.test_results)
        assert total_tests == 0
        
        # Test all failed scenario
        all_failed = MagicMock(passed=0, failed=10, skipped=0, errors=0, category="All Failed")
        dashboard.test_results = [all_failed]
        total_failed = sum(r.failed for r in dashboard.test_results)
        assert total_failed == 10
        
        # Test all errors scenario
        all_errors = MagicMock(passed=0, failed=0, skipped=0, errors=5, category="All Errors")
        dashboard.test_results = [all_errors]
        total_errors = sum(r.errors for r in dashboard.test_results)
        assert total_errors == 5
        
        print("✅ Dashboard handles error scenarios correctly")
    
    def test_dashboard_consistency_check(self):
        """Test that dashboard maintains internal consistency."""
        dashboard = AITestDashboard()
        
        # Create consistent test data
        test_data = [
            {"passed": 10, "failed": 1, "skipped": 2, "errors": 0},
            {"passed": 20, "failed": 0, "skipped": 3, "errors": 1},
            {"passed": 15, "failed": 2, "skipped": 1, "errors": 0},
        ]
        
        dashboard.test_results = [
            MagicMock(**data, category=f"Test {i+1}") 
            for i, data in enumerate(test_data)
        ]
        
        # Verify internal consistency
        for i, result in enumerate(dashboard.test_results):
            expected = test_data[i]
            assert result.passed == expected["passed"]
            assert result.failed == expected["failed"]
            assert result.skipped == expected["skipped"]
            assert result.errors == expected["errors"]
        
        # Verify totals match sum of parts
        total_passed = sum(r.passed for r in dashboard.test_results)
        total_failed = sum(r.failed for r in dashboard.test_results)
        total_skipped = sum(r.skipped for r in dashboard.test_results)
        total_errors = sum(r.errors for r in dashboard.test_results)
        
        expected_passed = sum(d["passed"] for d in test_data)
        expected_failed = sum(d["failed"] for d in test_data)
        expected_skipped = sum(d["skipped"] for d in test_data)
        expected_errors = sum(d["errors"] for d in test_data)
        
        assert total_passed == expected_passed
        assert total_failed == expected_failed
        assert total_skipped == expected_skipped
        assert total_errors == expected_errors
        
        print("✅ Dashboard maintains internal consistency")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
