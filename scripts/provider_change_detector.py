#!/usr/bin/env python3
"""
Automated Provider Change Detection System
Integrates with CI/CD to automatically detect and report provider changes.
"""

import os
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from provider_health_monitor import ProviderMonitor, ProviderStatus

class ProviderChangeDetector:
    """Detect and report provider changes automatically."""
    
    def __init__(self):
        self.monitor = ProviderMonitor()
        self.alert_threshold = {
            'response_time': 10.0,  # Alert if slower than 10s
            'downtime_hours': 1,     # Alert if down for more than 1 hour
            'error_rate': 0.1        # Alert if error rate > 10%
        }
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run comprehensive provider check with change detection."""
        print("🔍 COMPREHENSIVE PROVIDER CHANGE DETECTION")
        print("=" * 60)
        
        # Run health check
        results = self.monitor.run_health_check()
        
        # Analyze changes
        analysis = self._analyze_changes(results)
        
        # Generate report
        report = self._generate_report(results, analysis)
        
        return {
            'results': results,
            'analysis': analysis,
            'report': report,
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_changes(self, results: Dict[str, ProviderStatus]) -> Dict[str, Any]:
        """Analyze changes and detect issues."""
        analysis = {
            'critical_issues': [],
            'warnings': [],
            'performance_issues': [],
            'model_changes': [],
            'api_changes': []
        }
        
        for name, status in results.items():
            # Critical issues
            if status.status == "down":
                analysis['critical_issues'].append(f"{name}: Provider is down")
            
            # Performance issues
            if status.response_time > self.alert_threshold['response_time']:
                analysis['performance_issues'].append(
                    f"{name}: Slow response ({status.response_time:.1f}s)"
                )
            
            # Model changes
            if "model" in str(status.issues).lower():
                analysis['model_changes'].append(f"{name}: Model availability changed")
            
            # API changes
            if any(code in str(status.issues) for code in ['401', '403', '404']):
                analysis['api_changes'].append(f"{name}: API access changed")
            
            # Warnings
            if status.status == "degraded":
                analysis['warnings'].append(f"{name}: {', '.join(status.issues)}")
        
        return analysis
    
    def _generate_report(self, results: Dict[str, ProviderStatus], analysis: Dict[str, Any]) -> str:
        """Generate detailed report."""
        report = []
        report.append("# AI PROVIDER HEALTH REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive summary
        healthy = sum(1 for s in results.values() if s.status == "healthy")
        total = len(results)
        report.append(f"## EXECUTIVE SUMMARY")
        report.append(f"- **Overall Health**: {healthy}/{total} providers healthy ({healthy/total*100:.1f}%)")
        report.append(f"- **Critical Issues**: {len(analysis['critical_issues'])}")
        report.append(f"- **Warnings**: {len(analysis['warnings'])}")
        report.append(f"- **Performance Issues**: {len(analysis['performance_issues'])}")
        report.append("")
        
        # Detailed status
        report.append("## DETAILED STATUS")
        for name, status in results.items():
            status_icon = {"healthy": "✅", "degraded": "⚠️", "down": "❌"}[status.status]
            report.append(f"### {status_icon} {name}")
            report.append(f"- **Status**: {status.status.upper()}")
            report.append(f"- **Response Time**: {status.response_time:.2f}s")
            report.append(f"- **Test Model**: {status.test_model}")
            report.append(f"- **Endpoint**: {status.endpoint}")
            
            if status.issues:
                report.append("- **Issues**:")
                for issue in status.issues:
                    report.append(f"  - {issue}")
            report.append("")
        
        # Issues summary
        if analysis['critical_issues']:
            report.append("## 🚨 CRITICAL ISSUES")
            for issue in analysis['critical_issues']:
                report.append(f"- {issue}")
            report.append("")
        
        if analysis['warnings']:
            report.append("## ⚠️ WARNINGS")
            for warning in analysis['warnings']:
                report.append(f"- {warning}")
            report.append("")
        
        if analysis['performance_issues']:
            report.append("## 🐌 PERFORMANCE ISSUES")
            for perf in analysis['performance_issues']:
                report.append(f"- {perf}")
            report.append("")
        
        # Recommendations
        report.append("## 💡 RECOMMENDATIONS")
        report.append("- Review critical issues immediately")
        report.append("- Consider implementing fallback providers for degraded services")
        report.append("- Monitor performance trends over time")
        report.append("- Update test models if availability changes")
        report.append("- Check provider documentation for API changes")
        report.append("")
        
        return "\n".join(report)
    
    def save_report(self, report: str, filename: str = None):
        """Save report to file."""
        from pathlib import Path
        
        # Create reports directory
        reports_dir = Path("reports") / "provider_health"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            filename = f"provider_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        filepath = reports_dir / filename
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(f"📄 Report saved: {filename}")
        return filename
    
    def run_tests_with_monitoring(self):
        """Run test suite with provider monitoring."""
        print("🧪 RUNNING TESTS WITH PROVIDER MONITORING")
        print("=" * 50)
        
        # Run health check first
        health_results = self.monitor.run_health_check()
        
        # Check if any providers are down
        failed_providers = [name for name, status in health_results.items() 
                           if status.status == "down"]
        
        if failed_providers:
            print(f"⚠️  Skipping tests for failed providers: {', '.join(failed_providers)}")
        
        # Run pytest with appropriate markers
        try:
            # Run tests for healthy providers only
            cmd = ["pytest", "--tb=short", "-v"]
            
            # Add provider-specific markers for healthy providers
            provider_markers = {
                "OpenAI": "openai",
                "Groq": "groq", 
                "Together AI": "together",
                "OpenRouter": "openrouter",
                "Ollama": "ollama",
                "LM Studio": "lmstudio"
            }
            
            for name, status in health_results.items():
                if status.status == "healthy" and name in provider_markers:
                    cmd.extend(["-m", provider_markers[name]])
            
            # Skip if no healthy providers
            if len(cmd) == 4:  # Only base pytest command
                print("❌ No healthy providers to test")
                return False
            
            print(f"🚀 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            print("📊 TEST RESULTS:")
            print(result.stdout)
            if result.stderr:
                print("⚠️  ERRORS:")
                print(result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False

def create_ci_script():
    """Create CI/CD script for automated monitoring."""
    script = """#!/bin/bash
# CI/CD Provider Health Check Script

set -e

echo "🚀 Starting CI/CD Provider Health Check"

# Activate virtual environment
source .venv/bin/activate

# Run comprehensive provider check
python provider_change_detector.py

# Run tests with monitoring
python provider_change_detector.py --run-tests

# Generate report
python provider_change_detector.py --generate-report

echo "✅ CI/CD Provider Health Check Complete"
"""
    
    with open("ci_provider_check.sh", "w") as f:
        f.write(script)
    
    os.chmod("ci_provider_check.sh", 0o755)
    print("📄 Created CI/CD script: ci_provider_check.sh")

def main():
    """Main execution."""
    import sys
    
    detector = ProviderChangeDetector()
    
    if "--run-tests" in sys.argv:
        detector.run_tests_with_monitoring()
    elif "--generate-report" in sys.argv:
        results = detector.run_comprehensive_check()
        detector.save_report(results['report'])
    else:
        results = detector.run_comprehensive_check()
        detector.save_report(results['report'])
        
        # Create CI script
        create_ci_script()

if __name__ == "__main__":
    main()
