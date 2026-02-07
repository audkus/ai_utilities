#!/usr/bin/env python3
"""
AI Utilities Provider Monitoring Tools

Consolidated provider health monitoring, diagnostics, and change detection
for development and CI/CD operations.

This module provides:
- Provider health monitoring
- Change detection and alerting
- Diagnostic tools
- CI/CD integration utilities

Usage:
    python scripts/provider_tools.py --health-check
    python scripts/provider_tools.py --diagnose
    python scripts/provider_tools.py --detect-changes
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from ai_utilities import create_client
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure ai_utilities is installed or PYTHONPATH includes src/")
    sys.exit(1)


@dataclass
class ProviderStatus:
    """Track provider health status."""
    name: str
    endpoint: str
    api_key_env: str
    test_model: str
    last_check: datetime
    status: str  # "healthy", "degraded", "down"
    issues: List[str]
    response_time: float
    changed_since: Optional[datetime] = None


class ProviderMonitor:
    """Monitor AI provider health and detect changes."""
    
    def __init__(self):
        load_dotenv()
        self.providers = self._setup_providers()
        self.status_file = "provider_health.json"
        self.alert_thresholds = {
            "response_time": 10.0,  # Alert if slower than 10s
            "downtime_hours": 1,  # Alert if down for more than 1 hour
            "error_rate": 0.1,  # Alert if error rate > 10%
        }
    
    def _setup_providers(self) -> List[Dict]:
        """Configure providers to monitor."""
        return [
            {
                "name": "OpenAI",
                "endpoint": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
                "test_model": "gpt-3.5-turbo",
                "models_endpoint": "https://api.openai.com/v1/models"
            },
            {
                "name": "Groq",
                "endpoint": "https://api.groq.com/openai/v1",
                "api_key_env": "GROQ_API_KEY", 
                "test_model": "llama3-8b-8192",
                "models_endpoint": "https://api.groq.com/openai/v1/models"
            }
        ]
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on all providers."""
        print("🔍 PROVIDER HEALTH CHECK")
        print("=" * 50)
        
        results = {}
        previous_status = self._load_previous_status()
        
        for provider_config in self.providers:
            provider_name = provider_config["name"]
            print(f"\n📡 Checking {provider_name}...")
            
            try:
                status = self._check_provider(provider_config, previous_status.get(provider_name))
                results[provider_name] = status
                
                # Display results
                status_icon = "✅" if status.status == "healthy" else "⚠️" if status.status == "degraded" else "❌"
                print(f"   {status_icon} {status.status} ({status.response_time:.2f}s)")
                
                if status.issues:
                    for issue in status.issues:
                        print(f"      • {issue}")
                        
                if status.changed_since:
                    print(f"      🔄 Changed since: {status.changed_since}")
                    
            except Exception as e:
                print(f"   ❌ Failed to check {provider_name}: {e}")
                results[provider_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Save current status
        self._save_status(results)
        
        return {
            "providers": results,
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(results)
        }
    
    def _check_provider(self, config: Dict, previous_status: Optional[Dict]) -> ProviderStatus:
        """Check individual provider health."""
        name = config["name"]
        api_key = os.getenv(config["api_key_env"])
        
        if not api_key:
            return ProviderStatus(
                name=name,
                endpoint=config["endpoint"],
                api_key_env=config["api_key_env"],
                test_model=config["test_model"],
                last_check=datetime.now(),
                status="down",
                issues=[f"Missing API key: {config['api_key_env']}"],
                response_time=0.0
            )
        
        try:
            # Create client and test
            client = create_client(provider=name.lower())
            start_time = datetime.now()
            
            # Simple test request
            response = client.ask("Hello", max_tokens=5)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Analyze response
            issues = []
            status = "healthy"
            
            if response_time > self.alert_thresholds["response_time"]:
                issues.append(f"Slow response time: {response_time:.2f}s")
                status = "degraded"
            
            # Check for changes
            changed_since = None
            if previous_status and previous_status.get("status") != status:
                changed_since = datetime.now()
            
            return ProviderStatus(
                name=name,
                endpoint=config["endpoint"],
                api_key_env=config["api_key_env"],
                test_model=config["test_model"],
                last_check=datetime.now(),
                status=status,
                issues=issues,
                response_time=response_time,
                changed_since=changed_since
            )
            
        except Exception as e:
            return ProviderStatus(
                name=name,
                endpoint=config["endpoint"],
                api_key_env=config["api_key_env"],
                test_model=config["test_model"],
                last_check=datetime.now(),
                status="down",
                issues=[f"Connection failed: {str(e)}"],
                response_time=0.0
            )
    
    def _load_previous_status(self) -> Dict:
        """Load previous provider status."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_status(self, results: Dict) -> None:
        """Save current provider status."""
        try:
            # Convert datetime objects to strings for JSON serialization
            serializable_results = {}
            for provider, data in results.items():
                if isinstance(data, ProviderStatus):
                    serializable_results[provider] = asdict(data)
                    if serializable_results[provider]["changed_since"]:
                        serializable_results[provider]["changed_since"] = data.changed_since.isoformat()
                    serializable_results[provider]["last_check"] = data.last_check.isoformat()
                else:
                    serializable_results[provider] = data
            
            with open(self.status_file, 'w') as f:
                json.dump(serializable_results, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save status: {e}")
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of health check results."""
        summary = {
            "total_providers": len(results),
            "healthy": 0,
            "degraded": 0,
            "down": 0,
            "error": 0
        }
        
        for provider, data in results.items():
            if isinstance(data, ProviderStatus):
                summary[data.status] += 1
            elif data.get("status") == "error":
                summary["error"] += 1
            else:
                summary[data.get("status", "unknown")] = summary.get(data.get("status", "unknown"), 0) + 1
        
        return summary


class ProviderDiagnostics:
    """Diagnostic tools for provider issues."""
    
    def __init__(self):
        self.monitor = ProviderMonitor()
    
    def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive provider diagnostics."""
        print("🔧 PROVIDER DIAGNOSTICS")
        print("=" * 50)
        
        diagnostics = {
            "environment": self._check_environment(),
            "connectivity": self._check_connectivity(),
            "configuration": self._check_configuration(),
            "dependencies": self._check_dependencies(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Display results
        self._display_diagnostics(diagnostics)
        
        return diagnostics
    
    def _check_environment(self) -> Dict[str, Any]:
        """Check environment setup."""
        print("\n🌍 Environment Check:")
        
        env_status = {"python_version": sys.version, "missing_vars": [], "present_vars": []}
        
        for provider_config in self.monitor.providers:
            api_key_env = provider_config["api_key_env"]
            api_key = os.getenv(api_key_env)
            
            if api_key:
                env_status["present_vars"].append(api_key_env)
                print(f"   ✅ {api_key_env}: Set")
            else:
                env_status["missing_vars"].append(api_key_env)
                print(f"   ❌ {api_key_env}: Missing")
        
        return env_status
    
    def _check_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        print("\n🌐 Connectivity Check:")
        
        connectivity = {}
        
        for provider_config in self.monitor.providers:
            name = provider_config["name"]
            endpoint = provider_config["endpoint"]
            
            try:
                import requests
                response = requests.get(endpoint, timeout=5)
                connectivity[name] = {
                    "status_code": response.status_code,
                    "reachable": response.status_code < 500,
                    "endpoint": endpoint
                }
                
                status_icon = "✅" if response.status_code < 500 else "❌"
                print(f"   {status_icon} {name}: {response.status_code}")
                
            except Exception as e:
                connectivity[name] = {
                    "reachable": False,
                    "error": str(e),
                    "endpoint": endpoint
                }
                print(f"   ❌ {name}: {str(e)}")
        
        return connectivity
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration files."""
        print("\n⚙️ Configuration Check:")
        
        config_status = {
            "dotenv_exists": os.path.exists(".env"),
            "config_files": [],
            "issues": []
        }
        
        # Check for .env file
        if os.path.exists(".env"):
            print("   ✅ .env file exists")
            config_status["config_files"].append(".env")
        else:
            print("   ⚠️ .env file not found")
            config_status["issues"].append("Consider creating .env file for API keys")
        
        # Check for other config files
        for config_file in ["config.json", "settings.yaml", "ai_utilities_config.json"]:
            if os.path.exists(config_file):
                print(f"   ✅ {config_file} exists")
                config_status["config_files"].append(config_file)
        
        return config_status
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check required dependencies."""
        print("\n📦 Dependencies Check:")
        
        dependencies = {}
        
        required_packages = ["requests", "pydantic", "python-dotenv"]
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                dependencies[package] = {"installed": True}
                print(f"   ✅ {package}: Installed")
            except ImportError:
                dependencies[package] = {"installed": False}
                print(f"   ❌ {package}: Missing")
        
        return dependencies
    
    def _display_diagnostics(self, diagnostics: Dict[str, Any]) -> None:
        """Display diagnostic results with recommendations."""
        print(f"\n📋 Diagnostic Summary:")
        print("=" * 30)
        
        # Environment recommendations
        env = diagnostics["environment"]
        if env["missing_vars"]:
            print(f"\n🔑 Missing API Keys ({len(env['missing_vars'])}):")
            for var in env["missing_vars"]:
                print(f"   • Set {var} in your environment or .env file")
        
        # Connectivity recommendations
        conn = diagnostics["connectivity"]
        unreachable = [name for name, data in conn.items() if not data.get("reachable", True)]
        if unreachable:
            print(f"\n🌐 Connectivity Issues ({len(unreachable)}):")
            for name in unreachable:
                data = conn[name]
                if "error" in data:
                    print(f"   • {name}: {data['error']}")
        
        # Configuration recommendations
        config = diagnostics["configuration"]
        if config["issues"]:
            print(f"\n⚙️ Configuration Issues:")
            for issue in config["issues"]:
                print(f"   • {issue}")
        
        # Dependency recommendations
        deps = diagnostics["dependencies"]
        missing_deps = [pkg for pkg, data in deps.items() if not data["installed"]]
        if missing_deps:
            print(f"\n📦 Missing Dependencies:")
            for pkg in missing_deps:
                print(f"   • Install {pkg}: pip install {pkg}")


class ChangeDetector:
    """Detect and report provider changes."""
    
    def __init__(self):
        self.monitor = ProviderMonitor()
    
    def detect_changes(self) -> Dict[str, Any]:
        """Detect provider changes since last check."""
        print("🔄 CHANGE DETECTION")
        print("=" * 50)
        
        # Run health check
        results = self.monitor.run_health_check()
        
        # Analyze changes
        changes = self._analyze_changes(results["providers"])
        
        # Generate alerts
        alerts = self._generate_alerts(changes)
        
        return {
            "results": results,
            "changes": changes,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_changes(self, results: Dict) -> Dict[str, Any]:
        """Analyze provider changes."""
        changes = {
            "status_changes": [],
            "new_issues": [],
            "performance_changes": [],
            "new_providers": [],
            "removed_providers": []
        }
        
        previous_status = self.monitor._load_previous_status()
        
        for provider_name, current_data in results.items():
            if not isinstance(current_data, ProviderStatus):
                continue
                
            previous_data = previous_status.get(provider_name)
            
            # Status changes
            if previous_data and previous_data.get("status") != current_data.status:
                changes["status_changes"].append({
                    "provider": provider_name,
                    "from": previous_data.get("status"),
                    "to": current_data.status,
                    "timestamp": current_data.last_check.isoformat()
                })
            
            # New issues
            if current_data.issues:
                prev_issues = previous_data.get("issues", []) if previous_data else []
                new_issues = [issue for issue in current_data.issues if issue not in prev_issues]
                if new_issues:
                    changes["new_issues"].append({
                        "provider": provider_name,
                        "issues": new_issues,
                        "timestamp": current_data.last_check.isoformat()
                    })
            
            # Performance changes
            if previous_data and "response_time" in previous_data:
                prev_time = previous_data["response_time"]
                curr_time = current_data.response_time
                change_pct = ((curr_time - prev_time) / prev_time) * 100 if prev_time > 0 else 0
                
                if abs(change_pct) > 20:  # 20% change threshold
                    changes["performance_changes"].append({
                        "provider": provider_name,
                        "from": prev_time,
                        "to": curr_time,
                        "change_percent": change_pct,
                        "timestamp": current_data.last_check.isoformat()
                    })
        
        return changes
    
    def _generate_alerts(self, changes: Dict) -> List[Dict]:
        """Generate alerts for significant changes."""
        alerts = []
        
        # Status change alerts
        for change in changes["status_changes"]:
            if change["to"] in ["down", "degraded"]:
                alerts.append({
                    "severity": "high" if change["to"] == "down" else "medium",
                    "type": "status_change",
                    "message": f"{change['provider']} status changed from {change['from']} to {change['to']}",
                    "timestamp": change["timestamp"]
                })
        
        # Performance alerts
        for change in changes["performance_changes"]:
            if change["change_percent"] > 50:
                alerts.append({
                    "severity": "medium",
                    "type": "performance",
                    "message": f"{change['provider']} response time changed by {change['change_percent']:.1f}%",
                    "timestamp": change["timestamp"]
                })
        
        return alerts


def main():
    """Main entry point for provider tools."""
    parser = argparse.ArgumentParser(description="AI Utilities Provider Tools")
    parser.add_argument("--health-check", action="store_true", help="Run provider health check")
    parser.add_argument("--diagnose", action="store_true", help="Run provider diagnostics")
    parser.add_argument("--detect-changes", action="store_true", help="Detect provider changes")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    
    args = parser.parse_args()
    
    if not any([args.health_check, args.diagnose, args.detect_changes, args.all]):
        parser.print_help()
        return
    
    print("🚀 AI Utilities Provider Tools")
    print("=" * 50)
    
    try:
        if args.all or args.health_check:
            monitor = ProviderMonitor()
            health_results = monitor.run_health_check()
            
            # Save results
            with open("provider_health_report.json", "w") as f:
                json.dump(health_results, f, indent=2, default=str)
            print(f"\n📁 Health report saved to: provider_health_report.json")
        
        if args.all or args.diagnose:
            diagnostics = ProviderDiagnostics()
            diag_results = diagnostics.run_diagnostics()
            
            # Save results
            with open("provider_diagnostic_report.json", "w") as f:
                json.dump(diag_results, f, indent=2, default=str)
            print(f"\n📁 Diagnostic report saved to: provider_diagnostic_report.json")
        
        if args.all or args.detect_changes:
            detector = ChangeDetector()
            change_results = detector.detect_changes()
            
            # Save results
            with open("provider_change_report.json", "w") as f:
                json.dump(change_results, f, indent=2, default=str)
            print(f"\n📁 Change report saved to: provider_change_report.json")
        
        print(f"\n✅ Provider tools completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
