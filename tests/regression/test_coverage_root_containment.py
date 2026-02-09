"""
Regression test to ensure coverage artifacts never contaminate repository root.

This test runs a minimal subprocess with coverage and verifies that no coverage
artifacts are created in the repository root, only in coverage_reports/.
"""

import subprocess
import sys
import tempfile
from pathlib import Path


def test_coverage_subprocess_no_root_contamination():
    """
    Test that subprocess coverage runs don't create artifacts in repository root.
    
    This is a regression guard to ensure coverage artifacts always go to coverage_reports/.
    """
    project_root = Path(__file__).parent.parent.parent  # tests/regression/ -> tests/ -> project root
    
    # Create a simple test file in temp directory to avoid affecting real tests
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_test_file = Path(temp_dir) / "test_simple.py"
        temp_test_file.write_text("""
def test_simple():
    assert True

def test_math():
    assert 1 + 1 == 2
""")
        
        # Run pytest with coverage in subprocess
        cmd = [
            sys.executable, "-m", "pytest",
            str(temp_test_file),
            "--cov=ai_utilities",
            "--cov-report=html:coverage_reports/html",
            "--cov-report=xml:coverage_reports/coverage.xml",
            "-q"  # Quiet output
        ]
        
        # Set environment to prevent root contamination
        env = dict(__import__('os').environ)
        env["COVERAGE_FILE"] = str(project_root / "coverage_reports" / ".coverage")
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,  # Reasonable timeout
            env=env
        )
        
        # Should succeed (even if no coverage collected, that's fine for this test)
        assert result.returncode == 0, f"Coverage subprocess failed: {result.stderr}"
        
        # Verify NO root contamination
        assert not (project_root / "htmlcov").exists(), "htmlcov should not exist in root"
        assert not (project_root / "coverage.xml").exists(), "coverage.xml should not exist in root"
        
        # Check for any .coverage* files in root (except .coveragerc)
        root_coverage_files = [f for f in project_root.glob(".coverage*") if f.name != ".coveragerc"]
        assert len(root_coverage_files) == 0, f"Found coverage files in root: {root_coverage_files}"
        
        # Verify coverage artifacts are in correct location (if they exist)
        coverage_reports_dir = project_root / "coverage_reports"
        if coverage_reports_dir.exists():
            # Should have .coverage data file(s) if coverage was collected
            coverage_data_files = list(coverage_reports_dir.glob(".coverage*"))
            
            # Should have HTML report if coverage was collected
            html_index = coverage_reports_dir / "html" / "index.html"
            if coverage_data_files:  # Only check HTML if we actually collected coverage
                assert html_index.exists(), "Should have HTML coverage report when coverage data exists"
            
            # Should have XML report if coverage was collected
            xml_report = coverage_reports_dir / "coverage.xml"
            if coverage_data_files:  # Only check XML if we actually collected coverage
                assert xml_report.exists(), "Should have XML coverage report when coverage data exists"
        
        # Clean up coverage artifacts
        import shutil
        if coverage_reports_dir.exists():
            shutil.rmtree(coverage_reports_dir)
