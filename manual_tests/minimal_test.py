#!/usr/bin/env python3
"""
Minimal test for provider installation help functionality
"""

import sys
sys.path.insert(0, 'src')

from ai_utilities.improved_setup import AIProviderRegistry

def test_minimal():
    print("🔧 PROVIDER INSTALLATION HELP TEST")
    print("=" * 40)
    
    registry = AIProviderRegistry()
    help_text = registry.get_provider_installation_help(["openai", "groq"])
    
    print("Generated help text:")
    print(help_text)
    print()
    
    # Test for specific installation commands
    print("Checking for 'ai-utilities[openai]':")
    if "ai-utilities[openai]" in help_text:
        print("✅ Found!")
    else:
        print("❌ Not found")
        # Analyze lines containing openai
        for line in help_text.split('\n'):
            if 'openai' in line:
                print(f"  Line containing openai: {repr(line)}")
                # Check if substring exists in this line
                if "ai-utilities[openai]" in line:
                    print("  ✅ Substring found in line!")
                else:
                    print("  ❌ Substring not found in line")
    
    print()
    print("Checking for 'pip install':")
    if "pip install" in help_text:
        print("✅ Found!")
    else:
        print("❌ Not found")
    
    print()
    print("Check for key components:")
    components = ["pip", "install", "ai-utilities", "openai", "groq"]
    for component in components:
        found = component in help_text
        print(f"  {component}: {'✅' if found else '❌'}")

if __name__ == "__main__":
    test_minimal()
