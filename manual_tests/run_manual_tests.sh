#!/bin/bash

# Manual Testing Harness for AI Utilities
# Pre-release verification for v1.0.0b1

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MANUAL_VENV_DIR="$PROJECT_ROOT/.manual_venvs"
REPORTS_DIR="$PROJECT_ROOT/reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORTS_DIR/manual_report_$TIMESTAMP.md"

# Default settings
RUN_TIER2=false
RUN_FULL=false
TIER2_PROVIDER="openai"
TIMEOUT=30

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tier2)
            RUN_TIER2=true
            shift
            ;;
        --full)
            RUN_FULL=true
            shift
            ;;
        --provider)
            TIER2_PROVIDER="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--tier2] [--full] [--provider <name>] [--timeout <seconds>]"
            echo "  --tier2     Run Tier 2 tests (requires AI_API_KEY)"
            echo "  --full      Install with OpenAI extras for full provider testing"
            echo "  --provider  Override Tier 2 provider (default: openai)"
            echo "  --timeout   Set timeout in seconds (default: 30)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create directories
mkdir -p "$MANUAL_VENV_DIR"
mkdir -p "$REPORTS_DIR"

# Setup isolated environment
VENV_DIR="$MANUAL_VENV_DIR/manual_test_$TIMESTAMP"
echo "Setting up isolated environment in $VENV_DIR..."

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install package (with extras if Tier 2 or Full is enabled)
if [ "$RUN_TIER2" = true ] || [ "$RUN_FULL" = true ]; then
    echo "Installing ai-utilities with OpenAI extras..."
    pip install "$PROJECT_ROOT[openai]" > /dev/null 2>&1
else
    echo "Installing ai-utilities in minimal mode..."
    pip install "$PROJECT_ROOT" > /dev/null 2>&1
fi

# Initialize report
cat > "$REPORT_FILE" << EOF
# Manual Test Report

**Timestamp:** $(date)
**Python:** $(python --version)
**Tier 2:** $([ "$RUN_TIER2" = true ] && echo "Enabled ($TIER2_PROVIDER)" || echo "Disabled")
**Full Install:** $([ "$RUN_FULL" = true ] && echo "Enabled" || echo "Disabled")
**Timeout:** ${TIMEOUT}s

## Environment Setup
- Virtual Environment: $VENV_DIR
- Package: ai-utilities $([ "$RUN_TIER2" = true ] || [ "$RUN_FULL" = true ] && echo "(with OpenAI extras)" || echo "(minimal install)")

EOF

# Function to run tier 1 test for a provider
run_tier1_test() {
    local provider="$1"
    echo "Testing Tier 1 for provider: $provider"
    
    # Test A: Settings selection
    if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')
from ai_utilities import AiSettings
try:
    settings = AiSettings(provider='$provider')
    print('PASS: Settings created')
except Exception as e:
    print(f'FAIL: Settings creation failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
        settings_result="PASS"
        settings_reason="Settings created successfully"
    else
        settings_result="FAIL"
        settings_reason="Settings creation failed"
    fi
    
    # Test B: Provider creation path
    if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')
from ai_utilities import AiSettings, create_provider
try:
    settings = AiSettings(provider='$provider')
    provider_instance = create_provider(settings)
    print('PASS: Provider created')
except Exception as e:
    if 'optional' in str(e).lower() or 'missing' in str(e).lower():
        print(f'SKIP: Optional dependency missing: {e}')
        sys.exit(2)
    else:
        print(f'FAIL: Provider creation failed: {e}')
        sys.exit(1)
" 2>/dev/null; then
        provider_result="PASS"
        provider_reason="Provider created successfully"
    elif [ $? -eq 2 ]; then
        provider_result="SKIP"
        provider_reason="Optional dependency missing"
    else
        provider_result="FAIL"
        provider_reason="Provider creation failed"
    fi
    
    # Test C: Missing configuration behavior
    if python3 -c "
import sys
import os
sys.path.insert(0, '$PROJECT_ROOT/src')
from ai_utilities import AiSettings, create_provider
# Clear any existing API keys
for key in ['AI_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
    if key in os.environ:
        del os.environ[key]
try:
    settings = AiSettings(provider='$provider')
    provider_instance = create_provider(settings)
    # If we get here, provider doesn't require API key (local provider)
    print('PASS: No API key required')
except Exception as e:
    if 'api key' in str(e).lower() or 'required' in str(e).lower():
        print('PASS: Proper API key error')
    else:
        print(f'FAIL: Unexpected error: {e}')
        sys.exit(1)
" 2>/dev/null; then
        config_result="PASS"
        config_reason="Configuration handling correct"
    else
        config_result="FAIL"
        config_reason="Configuration error unexpected"
    fi
    
    # Determine overall result
    if [[ "$settings_result" == "FAIL" || "$provider_result" == "FAIL" || "$config_result" == "FAIL" ]]; then
        overall_result="FAIL"
    elif [[ "$settings_result" == "SKIP" || "$provider_result" == "SKIP" || "$config_result" == "SKIP" ]]; then
        overall_result="SKIP"
    else
        overall_result="PASS"
    fi
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
### $provider
| Test | Result | Reason |
|------|--------|--------|
| Settings | $settings_result | $settings_reason |
| Provider Creation | $provider_result | $provider_reason |
| Missing Config | $config_result | $config_reason |
| **Overall** | **$overall_result** | |

EOF
    
    echo "  $provider: $overall_result"
}

# Function to run tier 2 test
run_tier2_test() {
    local provider="$1"
    echo "Testing Tier 2 for provider: $provider"
    
    if [ -z "${AI_API_KEY:-}" ]; then
        cat >> "$REPORT_FILE" << EOF
### Tier 2 - $provider
**Result:** SKIP - AI_API_KEY not configured

EOF
        echo "  Tier 2 $provider: SKIP (no API key)"
        return 0
    fi
    
    # Test basic ask()
    ask_result=$(timeout "$TIMEOUT" python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')
from ai_utilities import create_client
try:
    client = create_client(provider='$provider')
    response = client.ask('What is 2+2? Answer with just the number.')
    print('PASS')
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(1)
" 2>/dev/null || echo "FAIL: Timeout")
    
    # Test ask_many()
    ask_many_result=$(timeout "$TIMEOUT" python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')
from ai_utilities import create_client
try:
    client = create_client(provider='$provider')
    responses = client.ask_many(['What is 1+1?', 'What is 2+2?'])
    if len(responses) == 2:
        print('PASS')
    else:
        print('FAIL: Wrong response count')
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(1)
" 2>/dev/null || echo "FAIL: Timeout")
    
    # Test structured output if supported (only for OpenAI)
    structured_result="N/A"
    if [ "$provider" = "openai" ]; then
        structured_result=$(timeout "$TIMEOUT" python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')
from ai_utilities import create_client
try:
    client = create_client(provider='$provider')
    response = client.ask('List 3 colors', response_format='json')
    import json
    data = json.loads(response)
    if isinstance(data, (list, dict)):
        print('PASS')
    else:
        print('FAIL: Not JSON')
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(1)
" 2>/dev/null || echo "FAIL: Timeout")
    fi
    
    # Determine overall result
    if [[ "$ask_result" == "FAIL" || "$ask_many_result" == "FAIL" || "$structured_result" == "FAIL" ]]; then
        overall_result="FAIL"
    elif [[ "$ask_result" == "PASS" && "$ask_many_result" == "PASS" && ("$structured_result" == "PASS" || "$structured_result" == "N/A") ]]; then
        overall_result="PASS"
    else
        overall_result="SKIP"
    fi
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
### Tier 2 - $provider
| Test | Result |
|------|--------|
| ask() | $ask_result |
| ask_many() | $ask_many_result |
| structured | $structured_result |
| **Overall** | **$overall_result** |

EOF
    
    echo "  Tier 2 $provider: $overall_result"
}

# Main execution
echo "Starting manual tests..."
echo "Report will be saved to: $REPORT_FILE"

# Tier 1 Tests
echo ""
echo "=== TIER 1 TESTS (All Providers, No Network) ==="

cat >> "$REPORT_FILE" << EOF
## Tier 1 Results (All Providers, No Network)

EOF

# Get list of supported providers
providers=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')
from ai_utilities.providers.provider_factory import list_supported_providers
for provider in list_supported_providers():
    print(provider)
")

tier1_pass=0
tier1_skip=0
tier1_fail=0

for provider in $providers; do
    run_tier1_test "$provider"
    
    # Count results (simple check of last overall result)
    last_result=$(tail -5 "$REPORT_FILE" | grep "Overall" | tail -1 | grep -o "\(PASS\|SKIP\|FAIL\)" || echo "FAIL")
    case "$last_result" in
        "PASS") ((tier1_pass++)) ;;
        "SKIP") ((tier1_skip++)) ;;
        "FAIL") ((tier1_fail++)) ;;
    esac
done

# Tier 2 Tests
if [ "$RUN_TIER2" = true ]; then
    echo ""
    echo "=== TIER 2 TESTS ($TIER2_PROVIDER, Real Calls) ==="
    
    # Check for API key
    if [ -z "${AI_API_KEY:-}" ]; then
        echo "⚠️  WARNING: AI_API_KEY not set - Tier 2 tests will be skipped"
        echo "   To run Tier 2 tests, set: export AI_API_KEY=your-key-here"
        echo ""
        cat >> "$REPORT_FILE" << EOF
## Tier 2 Results ($TIER2_PROVIDER, Real Calls)

⚠️ **SKIPPED**: AI_API_KEY not set
To run Tier 2 tests: \`export AI_API_KEY=your-key-here\`

EOF
    else
        echo "✅ API key found - running Tier 2 tests"
        cat >> "$REPORT_FILE" << EOF
## Tier 2 Results ($TIER2_PROVIDER, Real Calls)

EOF
        run_tier2_test "$TIER2_PROVIDER"
    fi
fi

# Summary
echo ""
echo "=== SUMMARY ==="

cat >> "$REPORT_FILE" << EOF
## Summary

**Tier 1:** $tier1_pass PASS, $tier1_skip SKIP, $tier1_fail FAIL
EOF

if [ "$RUN_TIER2" = true ]; then
    cat >> "$REPORT_FILE" << EOF
**Tier 2:** $TIER2_PROVIDER completed
EOF
fi

cat >> "$REPORT_FILE" << EOF

**Exit Code:** $([ "$tier1_fail" -gt 0 ] && echo "1" || echo "0")

---

*Generated by manual testing harness*
EOF

echo "Tier 1: $tier1_pass PASS, $tier1_skip SKIP, $tier1_fail FAIL"
if [ "$RUN_TIER2" = true ]; then
    echo "Tier 2: $TIER2_PROVIDER completed"
fi
echo "Report saved to: $REPORT_FILE"

# Cleanup
echo "Cleaning up temporary environment..."
rm -rf "$VENV_DIR"

# Exit with appropriate code
if [ "$tier1_fail" -gt 0 ]; then
    echo "Some Tier 1 tests failed"
    exit 1
else
    echo "All tests completed successfully"
    exit 0
fi
