#!/usr/bin/env python3
"""
Script to add external provider API keys to .env file for testing.
This adds placeholder keys that will allow the tests to run (they will fail gracefully with authentication errors).
"""

import os
from pathlib import Path

def add_external_provider_keys():
    """Add placeholder API keys for external providers."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found. Please copy .env.example to .env first.")
        return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Add placeholder keys if they don't exist
    additions = [
        "",
        "# ===== EXTERNAL PROVIDER TEST KEYS =====",
        "# These are placeholder keys for testing - tests will fail gracefully with auth errors",
        "GROQ_API_KEY=gsk_placeholder_test_key_for_integration_testing",
        "TOGETHER_API_KEY=tgp_placeholder_test_key_for_integration_testing", 
        "OPENROUTER_API_KEY=sk-or-v1-placeholder_test_key_for_integration_testing",
        "",
        "# ===== LOCAL PROVIDER TEST CONFIGURATION =====",
        "LIVE_LMSTUDIO_MODEL=llama3.1-test",
        "LIVE_TEXTGEN_MODEL=llama3.1-test", 
        "LIVE_FASTCHAT_MODEL=llama3.1-test",
        ""
    ]
    
    # Check if keys already exist
    if "GROQ_API_KEY=" in content and "TOGETHER_API_KEY=" in content and "OPENROUTER_API_KEY=" in content:
        print("✅ External provider keys already exist in .env")
        return True
    
    # Add the keys
    with open(env_file, 'a') as f:
        f.write('\n'.join(additions))
    
    print("✅ Added external provider placeholder keys to .env")
    return True

if __name__ == "__main__":
    add_external_provider_keys()
