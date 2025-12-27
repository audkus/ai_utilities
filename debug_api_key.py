#!/usr/bin/env python3
"""
Debug script to check AI_API_KEY configuration
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_api_key():
    print("🔍 AI_API_KEY Configuration Debug")
    print("=" * 50)
    
    # Check 1: Direct environment variable
    print("\n1. Direct Environment Variable Check:")
    api_key = os.getenv("AI_API_KEY")
    if api_key:
        print(f"   ✅ AI_API_KEY is set: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
    else:
        print("   ❌ AI_API_KEY is not set in current environment")
    
    # Check 2: All environment variables with AI_
    print("\n2. All AI_ Environment Variables:")
    ai_vars = {k: v for k, v in os.environ.items() if k.startswith("AI_")}
    if ai_vars:
        for key, value in ai_vars.items():
            if "API_KEY" in key:
                masked_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                print(f"   {key}: {masked_value}")
            else:
                print(f"   {key}: {value}")
    else:
        print("   ❌ No AI_ environment variables found")
    
    # Check 3: Try to load AiSettings
    print("\n3. AiSettings Loading Test:")
    try:
        from ai_utilities.client import AiSettings
        
        settings = AiSettings()
        print(f"   ✅ AiSettings loaded successfully")
        print(f"   Provider: {settings.provider}")
        print(f"   Model: {settings.model}")
        if settings.api_key:
            masked_key = f"{settings.api_key[:10]}...{settings.api_key[-4:]}" if len(settings.api_key) > 14 else "***"
            print(f"   API Key: {masked_key}")
        else:
            print(f"   ❌ API Key: None")
    except Exception as e:
        print(f"   ❌ Error loading AiSettings: {e}")
    
    # Check 4: Try to create client
    print("\n4. Client Creation Test:")
    try:
        from ai_utilities import create_client
        
        client = create_client()
        print("   ✅ Client created successfully")
    except Exception as e:
        print(f"   ❌ Error creating client: {e}")
    
    # Check 5: Common setup commands
    print("\n5. Setup Commands:")
    print("   To set AI_API_KEY for current session:")
    print("   Linux/Mac: export AI_API_KEY='your-openai-key-here'")
    print("   Windows PowerShell: $env:AI_API_KEY='your-openai-key-here'")
    print("   Windows CMD: set AI_API_KEY=your-openai-key-here")
    
    print("\n   To make it permanent:")
    print("   Add to ~/.bashrc or ~/.zshrc (Linux/Mac):")
    print("   export AI_API_KEY='your-openai-key-here'")
    print("   ")
    print("   Add to PowerShell profile (Windows):")
    print("   $env:AI_API_KEY='your-openai-key-here'")
    
    # Check 6: Test with explicit key
    print("\n6. Test with Explicit Key:")
    print("   If you have your key, you can test it directly:")
    print("   python3 -c \"")
    print("   from ai_utilities import create_client")
    print("   client = create_client(api_key='your-key-here')")
    print("   response = client.ask('What is 2+2?')")
    print("   print(response)\"")

if __name__ == "__main__":
    debug_api_key()
