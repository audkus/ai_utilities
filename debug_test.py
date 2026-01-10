#!/usr/bin/env python3
"""
Debug script to fix the test assertion issue
"""

import sys
sys.path.insert(0, 'src')

from ai_utilities.improved_setup import AIProviderRegistry

def debug_test_issue():
    print("🔍 DEBUGGING TEST ASSERTION ISSUE")
    print("=" * 50)
    
    registry = AIProviderRegistry()
    help_text = registry.get_provider_installation_help(["openai", "groq"])
    
    print("Help text content:")
    print(repr(help_text))
    print()
    
    # Check each assertion separately
    assertions = [
        'pip install "ai-utilities[openai]"',
        'pip install "ai-utilities[groq]"',
        'Providers will be available immediately'
    ]
    
    for assertion in assertions:
        print(f"Testing: {repr(assertion)}")
        result = assertion in help_text
        print(f"Result: {result}")
        
        if not result:
            # Find similar strings
            lines = help_text.split('\n')
            for i, line in enumerate(lines):
                if any(word in line.lower() for word in ['openai', 'groq', 'install']):
                    print(f"  Similar line {i}: {repr(line)}")
        print()
    
    # Try alternative assertions
    print("Trying alternative assertions:")
    alt_assertions = [
        'pip install "ai-utilities[openai]"',
        'ai-utilities[openai]',
        'openai'
    ]
    
    for assertion in alt_assertions:
        result = assertion in help_text
        print(f"  {repr(assertion)}: {result}")

if __name__ == "__main__":
    debug_test_issue()
