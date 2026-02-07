#!/usr/bin/env python3
"""
Minimal Groq Example - Quickstart
The simplest possible way to use AI Utilities with Groq (fast inference).
"""

import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient

def main():
    print("⚡ Minimal Groq Example")
    print("=" * 40)
    
    # Create client for Groq (fast inference)
    client = AiClient(provider="groq")
    
    # Simple question
    response = client.ask("What is 2 + 2?")
    
    print(f"Response: {response}")
    print("✅ Success! Your Groq setup is working.")
    print("💡 Get free API key: https://console.groq.com/")

if __name__ == "__main__":
    main()
