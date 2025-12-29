#!/usr/bin/env python3
"""
Daily Provider Monitoring Script
Easy to run and understand provider health monitoring.
"""

import os
import json
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from provider_health_monitor import ProviderMonitor

def daily_check():
    """Simple daily provider health check."""
    print("🌅 DAILY PROVIDER HEALTH CHECK")
    print("=" * 40)
    
    monitor = ProviderMonitor()
    results = monitor.run_health_check()
    
    # Quick summary
    healthy = sum(1 for s in results.values() if s.status == "healthy")
    total = len(results)
    
    print(f"\n📊 TODAY'S SUMMARY: {healthy}/{total} providers healthy")
    
    # Action items
    action_needed = []
    for name, status in results.items():
        if status.status == "down":
            action_needed.append(f"🚨 {name}: DOWN - {', '.join(status.issues)}")
        elif status.status == "degraded":
            action_needed.append(f"⚠️  {name}: DEGRADED - {', '.join(status.issues)}")
    
    if action_needed:
        print(f"\n🎯 ACTION NEEDED ({len(action_needed)} items):")
        for item in action_needed:
            print(f"   {item}")
    else:
        print("\n✅ All providers healthy - no action needed!")
    
    # Save simple status
    status = {
        "date": datetime.now().isoformat(),
        "healthy": healthy,
        "total": total,
        "providers": {
            name: {
                "status": status.status,
                "response_time": status.response_time,
                "issues": status.issues
            }
            for name, status in results.items()
        }
    }
    
    with open("daily_provider_status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    print(f"\n💾 Status saved to: daily_provider_status.json")
    
    # Return exit code for CI/CD
    return 0 if healthy == total else 1

if __name__ == "__main__":
    exit_code = daily_check()
    exit(exit_code)
