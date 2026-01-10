#!/usr/bin/env python3
"""
Minimal test to fix the assertion issue
"""

import sys
sys.path.insert(0, 'src')

from ai_utilities.improved_setup import AIProviderRegistry

def test_minimal():
    print("🔧 MINIMAL TEST APPROACH")
    print("=" * 30)
    
    registry = AIProviderRegistry()
    help_text = registry.get_provider_installation_help(["openai", "groq"])
    
    print("Help text:")
    print(help_text)
    print()
    
    # Let's try to find what's actually in the string
    print("Looking for 'ai-utilities[openai]':")
    if "ai-utilities[openai]" in help_text:
        print("✅ Found!")
    else:
        print("❌ Not found")
        # Let's see what's close
        for line in help_text.split('\n'):
            if 'openai' in line:
                print(f"  Line containing openai: {repr(line)}")
                # Check if our substring is in this line
                if "ai-utilities[openai]" in line:
                    print("  ✅ Substring found in line!")
                else:
                    print("  ❌ Substring not found in line")
    
    print()
    print("Looking for 'pip install':")
    if "pip install" in help_text:
        print("✅ Found!")
    else:
        print("❌ Not found")
    
    print()
    print("Let's try a different approach - check for key components:")
    components = ["pip", "install", "ai-utilities", "openai", "groq"]
    for component in components:
        found = component in help_text
        print(f"  {component}: {'✅' if found else '❌'}")

if __name__ == "__main__":
    test_minimal()
