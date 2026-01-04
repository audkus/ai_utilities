#!/usr/bin/env python3
"""
Coverage Summary Tool

Generates comprehensive test coverage reports and summaries for AI Utilities.
Provides coverage statistics, trends, and badge generation.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CoverageMetrics:
    """Coverage metrics data structure."""
    total_statements: int
    covered_statements: int
    total_lines: int
    covered_lines: int
    total_branches: int
    covered_branches: int
    percentage: float
    missing_lines: List[int]


class CoverageReporter:
    """Generate and analyze test coverage reports."""
    
    def __init__(self, coverage_file: str = ".coverage", output_dir: str = "coverage_reports"):
        self.coverage_file = Path(coverage_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def run_coverage(self, test_path: str = "tests/") -> bool:
        """Run coverage analysis on tests."""
        print("🔍 Running coverage analysis...")
        
        try:
            cmd = [
                "python", "-m", "pytest", 
                "--cov=src/ai_utilities",
                "--cov-report=json",
                "--cov-report=html",
                "--cov-report=term-missing",
                test_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Coverage analysis completed")
                print(result.stdout)
                return True
            else:
                print(f"❌ Coverage analysis failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ pytest or coverage.py not installed")
            print("Install with: pip install pytest coverage")
            return False
    
    def parse_coverage_json(self, json_file: str = "coverage.json") -> Optional[Dict[str, Any]]:
        """Parse coverage JSON report."""
        json_path = Path(json_file)
        
        if not json_path.exists():
            print(f"❌ Coverage JSON file not found: {json_file}")
            print("Run coverage analysis first with --run-coverage")
            return None
        
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error parsing coverage JSON: {e}")
            return None
    
    def extract_metrics(self, coverage_data: Dict[str, Any]) -> CoverageMetrics:
        """Extract key metrics from coverage data."""
        totals = coverage_data.get('totals', {})
        
        return CoverageMetrics(
            total_statements=totals.get('num_statements', 0),
            covered_statements=totals.get('covered_statements', 0),
            total_lines=totals.get('num_lines', 0),
            covered_lines=totals.get('covered_lines', 0),
            total_branches=totals.get('num_branches', 0),
            covered_branches=totals.get('covered_branches', 0),
            percentage=totals.get('percent_covered', 0.0),
            missing_lines=[]  # Will be populated per file
        )
    
    def generate_summary_report(self, coverage_data: Dict[str, Any]) -> str:
        """Generate a comprehensive coverage summary report."""
        metrics = self.extract_metrics(coverage_data)
        
        report = f"""
# 📊 Test Coverage Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 Overall Coverage Summary
- **Total Statements:** {metrics.total_statements}
- **Covered Statements:** {metrics.covered_statements}
- **Coverage Percentage:** {metrics.percentage:.1f}%

## 📋 File-by-File Coverage

| File | Statements | Covered | Coverage |
|------|------------|---------|----------|
"""
        
        files = coverage_data.get('files', {})
        for filename, file_data in sorted(files.items()):
            if 'src/ai_utilities' in filename:
                total = file_data.get('summary', {}).get('num_statements', 0)
                covered = file_data.get('summary', {}).get('covered_statements', 0)
                percentage = file_data.get('summary', {}).get('percent_covered', 0.0)
                
                report += f"| {filename} | {total} | {covered} | {percentage:.1f}% |\n"
        
        report += f"""

## 🎯 Coverage Quality Assessment
"""
        
        if metrics.percentage >= 90:
            report += "✅ **Excellent coverage** (≥90%) - Well tested!\n"
        elif metrics.percentage >= 80:
            report += "🟡 **Good coverage** (80-89%) - Room for improvement\n"
        elif metrics.percentage >= 70:
            report += "🟠 **Fair coverage** (70-79%) - Consider adding more tests\n"
        else:
            report += "❌ **Poor coverage** (<70%) - Significant testing needed\n"
        
        report += f"""

## 📝 Recommendations
"""
        
        if metrics.percentage < 90:
            report += "- Add unit tests for uncovered functions\n"
        
        if metrics.total_branches > 0:
            branch_coverage = (metrics.covered_branches / metrics.total_branches) * 100
            if branch_coverage < 80:
                report += "- Improve branch coverage with edge case testing\n"
        
        report += "- Run `python scripts/coverage_summary.py --run-coverage` regularly\n"
        report += "- Focus on critical paths and error handling\n"
        
        return report
    
    def generate_badge(self, percentage: float) -> str:
        """Generate coverage badge SVG."""
        color = "#4c1" if percentage >= 90 else "#dfb317" if percentage >= 80 else "#e05d44"
        
        badge = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="106" height="20" xmlns="http://www.w3.org/2000/svg">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="106" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h55v20H0z"/>
    <path fill="{color}" d="M55 0h51v20H55z"/>
    <path fill="url(#b)" d="M0 0h106v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="27.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="27.5" y="14">coverage</text>
    <text x="80.5" y="15" fill="#010101" fill-opacity=".3">{percentage:.0f}%</text>
    <text x="80.5" y="14">{percentage:.0f}%</text>
  </g>
</svg>'''
        
        return badge
    
    def save_reports(self, coverage_data: Dict[str, Any]) -> None:
        """Save all coverage reports to files."""
        metrics = self.extract_metrics(coverage_data)
        
        # Save markdown report
        report = self.generate_summary_report(coverage_data)
        report_file = self.output_dir / "coverage_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📝 Coverage report saved: {report_file}")
        
        # Save badge
        badge = self.generate_badge(metrics.percentage)
        badge_file = self.output_dir / "coverage_badge.svg"
        with open(badge_file, 'w') as f:
            f.write(badge)
        print(f"🎨 Coverage badge saved: {badge_file}")
        
        # Save JSON summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "percentage": metrics.percentage,
            "total_statements": metrics.total_statements,
            "covered_statements": metrics.covered_statements,
            "quality": "excellent" if metrics.percentage >= 90 else "good" if metrics.percentage >= 80 else "fair" if metrics.percentage >= 70 else "poor"
        }
        
        summary_file = self.output_dir / "coverage_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"📊 Coverage summary saved: {summary_file}")
    
    def print_summary(self, coverage_data: Dict[str, Any]) -> None:
        """Print a concise coverage summary to console."""
        metrics = self.extract_metrics(coverage_data)
        
        print(f"\n🎯 Coverage Summary:")
        print(f"   Total Statements: {metrics.total_statements}")
        print(f"   Covered Statements: {metrics.covered_statements}")
        print(f"   Coverage: {metrics.percentage:.1f}%")
        
        if metrics.percentage >= 90:
            print("   ✅ Excellent coverage!")
        elif metrics.percentage >= 80:
            print("   🟡 Good coverage")
        elif metrics.percentage >= 70:
            print("   🟠 Fair coverage")
        else:
            print("   ❌ Poor coverage - needs improvement")


def main():
    """Main entry point for coverage summary tool."""
    parser = argparse.ArgumentParser(description="Generate test coverage reports")
    parser.add_argument("--run-coverage", action="store_true", 
                       help="Run coverage analysis before generating report")
    parser.add_argument("--test-path", default="tests/",
                       help="Path to tests (default: tests/)")
    parser.add_argument("--output-dir", default="coverage_reports",
                       help="Output directory for reports (default: coverage_reports)")
    parser.add_argument("--json-file", default="coverage.json",
                       help="Coverage JSON file (default: coverage.json)")
    
    args = parser.parse_args()
    
    reporter = CoverageReporter(output_dir=args.output_dir)
    
    # Run coverage if requested
    if args.run_coverage:
        if not reporter.run_coverage(args.test_path):
            sys.exit(1)
    
    # Parse existing coverage data
    coverage_data = reporter.parse_coverage_json(args.json_file)
    if not coverage_data:
        sys.exit(1)
    
    # Generate and save reports
    reporter.save_reports(coverage_data)
    reporter.print_summary(coverage_data)


if __name__ == "__main__":
    main()