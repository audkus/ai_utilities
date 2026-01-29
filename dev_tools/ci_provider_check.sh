#!/bin/bash
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
