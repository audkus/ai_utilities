#!/usr/bin/env python3
"""
Step 2: Client - Tutorial
Creating and using AI clients for different providers.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, AiSettings

def main():
    print("🤖 Step 2: Client")
    print("=" * 40)
    
    print("📋 Creating AI clients...")
    
    # Method 1: Auto-detect client (recommended)
    print("  🔄 Auto-detecting provider...")
    client = AiClient()
    print(f"  ✅ Using provider: {client.provider}")
    
    # Method 2: Explicit provider selection
    print("\n  🔧 Explicit provider selection:")
    
    # OpenAI
    print("  📝 Creating OpenAI client...")
    openai_client = AiClient(provider="openai")
    print(f"  ✅ OpenAI client ready")
    
    # Groq (fast inference)
    print("  ⚡ Creating Groq client...")
    groq_client = AiClient(provider="groq")
    print(f"  ✅ Groq client ready")
    
    # Local Ollama
    print("  🦙 Creating Ollama client...")
    try:
        ollama_client = AiClient(provider="ollama")
        print(f"  ✅ Ollama client ready")
    except Exception as e:
        print(f"  ⚠️ Ollama client failed: {e}")
        print("  💡 Make sure Ollama is running: ollama serve")
    
    # Custom settings
    print("\n  ⚙️ Custom settings:")
    settings = AiSettings(
        provider="openai",
        model="gpt-4",
        max_tokens=100,
        temperature=0.7
    )
    custom_client = AiClient(settings=settings)
    print(f"  ✅ Custom client ready: {settings.model}")
    
    # Test the auto-detected client
    print("\n  🧪 Testing auto-detected client:")
    try:
        response = client.ask("What is 2 + 2?")
        print(f"  ✅ Response: {response}")
        print("  🎉 Client is working correctly!")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("  💡 Check your API key configuration")
    
    print("\n🎯 Client setup complete!")
    print("  📚 Next: Run 'python examples/tutorial/step_03_caching.py'")

if __name__ == "__main__":
    main()
