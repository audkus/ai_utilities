#!/usr/bin/env python3
"""
Coverage test runner with proper directory structure management.
This script runs tests with coverage and ensures reports are organized correctly.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_coverage_directories(project_root):
    """Ensure coverage directories exist with proper structure."""
    coverage_dir = project_root / "coverage_reports"
    html_dir = coverage_dir / "html"
    xml_dir = coverage_dir / "xml"
    
    # Create directories
    coverage_dir.mkdir(exist_ok=True)
    html_dir.mkdir(exist_ok=True)
    xml_dir.mkdir(exist_ok=True)
    
    return coverage_dir, html_dir, xml_dir

def clean_old_coverage_reports(html_dir, xml_dir):
    """Clean old coverage reports."""
    # Clean HTML reports
    if html_dir.exists():
        for item in html_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    
    # Clean XML reports
    if xml_dir.exists():
        for item in xml_dir.iterdir():
            if item.is_file():
                item.unlink()

def run_coverage_tests(project_root, html_dir, xml_dir, include_integration=False):
    """Run tests with coverage."""
    print("🧪 Running tests with coverage...")
    
    # Build pytest command
    cmd = [
        "python3", "-m", "pytest",
        "--cov=src/ai_utilities",
        f"--cov-report=html:{html_dir}",
        f"--cov-report=xml:{xml_dir}/coverage.xml",
        "--cov-report=term-missing",
        "--tb=short",
        "--timeout=120"
    ]
    
    # Add integration tests if requested
    if include_integration:
        cmd.extend(["-m", "integration", "--run-integration"])
        env = os.environ.copy()
        env["RUN_LIVE_AI_TESTS"] = "1"
    else:
        cmd.extend(["-m", "not integration"])
        env = os.environ.copy()
    
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run tests
    result = subprocess.run(cmd, cwd=project_root, env=env)
    
    return result.returncode == 0

def show_coverage_summary(project_root, xml_dir):
    """Show coverage summary from XML report."""
    coverage_xml = xml_dir / "coverage.xml"
    
    if coverage_xml.exists():
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_xml)
            root = tree.getroot()
            
            # Find coverage element
            coverage = root.find(".//coverage")
            if coverage is not None:
                line_rate = coverage.get("line-rate", "0")
                percentage = float(line_rate) * 100
                
                print(f"\n📊 Coverage Summary: {percentage:.1f}%")
                
                # Show module breakdown
                packages = root.findall(".//package")
                if packages:
                    print("\n📋 Module Coverage:")
                    for package in packages[:10]:  # Show top 10
                        name = package.get("name", "").replace("src/", "")
                        line_rate = float(package.get("line-rate", "0")) * 100
                        print(f"  {name}: {line_rate:.1f}%")
                    
                    if len(packages) > 10:
                        print(f"  ... and {len(packages) - 10} more modules")
                
        except Exception as e:
            print(f"⚠️  Could not parse coverage XML: {e}")
    else:
        print("⚠️  Coverage XML report not found")

def main():
    """Main coverage runner."""
    project_root = Path(__file__).parent.parent
    
    print("🧪 AI Utilities - Coverage Test Runner")
    print("=" * 60)
    
    # Setup directories
    coverage_dir, html_dir, xml_dir = setup_coverage_directories(project_root)
    
    # Clean old reports
    clean_old_coverage_reports(html_dir, xml_dir)
    print(f"📁 Coverage reports will be saved to: {coverage_dir}")
    
    # Check if integration tests should be included
    include_integration = "--integration" in sys.argv or "-i" in sys.argv
    
    if include_integration:
        print("🌐 Including integration tests (requires RUN_LIVE_AI_TESTS=1)")
    else:
        print("🔬 Running unit tests only (faster)")
    
    # Run tests
    success = run_coverage_tests(project_root, html_dir, xml_dir, include_integration)
    
    # Show summary
    show_coverage_summary(project_root, xml_dir)
    
    # Report results
    if success:
        print(f"\n🎉 Coverage tests completed successfully!")
        print(f"📄 HTML report: {html_dir}/index.html")
        print(f"📄 XML report: {xml_dir}/coverage.xml")
    else:
        print(f"\n❌ Some tests failed - check output above")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
