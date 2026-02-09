#!/usr/bin/env python3
"""
Test a simple free API that works without any setup.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import create_client

def probe_simple_free_api():
    """Probe a simple free API that works without registration."""
    print("🌐 Testing Simple Free API (No Setup Required)")
    print("=" * 55)
    
    # Using a public demo API
    print("🧪 Testing Ollama Public Demo...")
    
    try:
        # This is a public Ollama demo server
        client = create_client(
            provider='openai_compatible',
            base_url='https://demo.ollama.ai/v1'
        )
        
        response = client.ask("What is 2+2? Give a brief answer.", model="llama3.2:latest")
        print(f"✅ Success! Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n🎯 RECOMMENDATION:")
    print("• For immediate testing: Use local Ollama (you already have it)")
    print("• For cloud testing: Set up free API keys (Groq recommended)")
    print("• Groq gives you the fastest free inference with Llama 3")

if __name__ == "__main__":
    probe_simple_free_api()
