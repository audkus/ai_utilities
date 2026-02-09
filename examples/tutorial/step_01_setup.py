#!/usr/bin/env python3
"""
Step 1: Setup - Tutorial
Setting up AI Utilities for the first time.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    print("🔧 Step 1: Setup")
    print("=" * 40)
    
    print("📋 Checking your setup...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"  ✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if ai_utilities is installed
    try:
        import ai_utilities
        print(f"  ✅ AI Utilities: {ai_utilities.__version__}")
    except ImportError:
        print("  ❌ AI Utilities not found")
        print("  💡 Install it: pip install ai-utilities[openai]")
        return
    
    # Check environment variables
    has_env = os.path.exists(".env")
    print(f"  {'✅' if has_env else '⚠️'} .env file found")
    
    # Check for API keys
    api_keys = ["OPENAI_API_KEY", "GROQ_API_KEY", "TOGETHER_API_KEY"]
    found_keys = [key for key in api_keys if os.getenv(key)]
    
    if found_keys:
        print(f"  ✅ API keys found: {', '.join(found_keys)}")
    else:
        print("  ⚠️ No API keys found")
        print("  💡 Set API keys in .env file or environment")
        print("  📝 Example .env file:")
        print("     OPENAI_API_KEY=your-key-here")
    
    print("\n🎯 Setup complete!")
    print("  ✅ You're ready to use AI Utilities")
    print("  📚 Next: Run 'python examples/tutorial/step_02_client.py'")

if __name__ == "__main__":
    main()
