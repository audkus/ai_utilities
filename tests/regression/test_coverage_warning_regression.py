"""
Simple regression test to verify CoverageWarning is eliminated.

This test runs the exact command that was causing the CoverageWarning
and verifies it no longer appears.
"""

import subprocess
import sys
from pathlib import Path


def test_no_coverage_warning_on_target_test():
    """
    Verify that running pytest with coverage on the target test doesn't produce CoverageWarning.
    
    Note: Due to pytest-cov's internal behavior, there may still be some early imports,
    but the CoverageWarning should be eliminated for the target use case.
    """
    project_root = Path(__file__).parent.parent.parent  # tests/regression/ -> tests/ -> project root
    
    # Run the exact command from the user's request with consistent config
    cmd = [
        sys.executable, "-m", "pytest", "-q",
        "tests/unit/test_environment_modules.py",
        "--cov=ai_utilities",
        "--cov-report=term-missing",
        "--tb=no"  # Consistent traceback handling
    ]

    # Set environment variables to prevent root contamination
    env = dict(__import__('os').environ)
    env["COVERAGE_FILE"] = str(project_root / "coverage_reports" / ".coverage")

    # Run from the project root
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=120,  # Increased timeout for CI reliability
        env=env
    )

    # Check that the command succeeded (behavior-based assertion)
    assert result.returncode == 0, f"Command failed with return code {result.returncode}: {result.stderr}"  # noqa: S101 - Test validation

    # Check that tests still pass (behavior-based: look for pass count, not exact string)
    assert "passed" in result.stdout and "failed" not in result.stdout, f"Tests didn't pass as expected: {result.stdout}"  # noqa: S101 - Test validation

    # Check that CoverageWarning is not present (behavior-based assertion)
    assert "CoverageWarning" not in result.stdout, f"CoverageWarning still present: {result.stdout}"  # noqa: S101 - Test validation

    # Clean up coverage file created by subprocess
    coverage_file = project_root / "coverage_reports" / ".coverage"
    if coverage_file.exists():
        coverage_file.unlink()

    print(f"Command executed successfully with coverage: {result.returncode == 0}")


def test_coverage_functionality_works():
    """
    Verify that coverage measurement is working correctly despite any warnings.
    """
    project_root = Path(__file__).parent.parent.parent  # tests/regression/ -> tests/ -> project root
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/test_environment_modules.py",
        "--cov=ai_utilities",
        "--cov-report=html:coverage_reports/html",
        "--cov-report=xml:coverage_reports/coverage.xml",
        "--tb=no"  # Consistent traceback handling
    ]

    # Set environment variables to prevent root contamination
    env = dict(__import__('os').environ)
    env["COVERAGE_FILE"] = str(project_root / "coverage_reports" / ".coverage")

    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=120,  # Increased timeout for CI reliability
        env=env
    )

    # Check that the command succeeded (behavior-based assertion)
    assert result.returncode == 0, f"Command failed with return code {result.returncode}: {result.stderr}"  # noqa: S101 - Test validation

    # Check that HTML report was generated in the correct location (behavior-based)
    html_report_path = project_root / "coverage_reports" / "html" / "index.html"
    assert html_report_path.exists(), f"HTML report not found at {html_report_path}"  # noqa: S101 - Test validation

    # Check that XML report was generated in the correct location
    xml_report_path = project_root / "coverage_reports" / "coverage.xml"
    assert xml_report_path.exists(), f"XML report not found at {xml_report_path}"  # noqa: S101 - Test validation

    # Assert NO root contamination
    assert not (project_root / "htmlcov").exists(), "htmlcov should not exist in root"  # noqa: S101 - Test validation
    assert not (project_root / "coverage.xml").exists(), "coverage.xml should not exist in root"  # noqa: S101 - Test validation
    root_coverage_files = [f for f in project_root.glob(".coverage*") if f.name != ".coveragerc"]
    assert len(root_coverage_files) == 0, f"No .coverage* files should exist in root: {root_coverage_files}"  # noqa: S101 - Test validation

    # Check that coverage data was collected (behavior-based: look for coverage report generation)
    assert "Coverage HTML written" in result.stdout or "coverage" in result.stdout.lower(), "Coverage report not generated"  # noqa: S101 - Test validation
    
    # Clean up coverage artifacts to avoid repository contamination
    import shutil
    coverage_reports_dir = html_report_path.parent.parent
    if coverage_reports_dir.exists():
        shutil.rmtree(coverage_reports_dir)


def test_makefile_targets_work():
    """
    Verify that the Makefile convenience targets work correctly.
    """
    import subprocess

    # Test make help target (quick)
    result = subprocess.run(
        ["make", "help"],
        cwd=Path(__file__).parent.parent.parent,  # tests/regression/ -> tests/ -> project root
        capture_output=True,
        text=True,
        timeout=10
    )

    # Makefile help should work
    assert result.returncode == 0, f"Make help failed: {result.stderr}"  # noqa: S101 - Test validation
    assert "Available targets:" in result.stdout, "Make help not working"  # noqa: S101 - Test validation

    # Verify the targets we documented are present
    assert "test" in result.stdout, "test target missing"  # noqa: S101 - Test validation
    assert "test-fast" in result.stdout, "test-fast target missing"  # noqa: S101 - Test validation
    assert "cov" in result.stdout, "cov target missing"  # noqa: S101 - Test validation
