#!/usr/bin/env python3
"""
Minimal Ollama Example - Quickstart
The simplest possible way to use AI Utilities with Ollama (local AI).
"""

import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient

def main():
    print("🦙 Minimal Ollama Example")
    print("=" * 40)
    
    # Create client for local Ollama
    client = AiClient(provider="ollama")
    
    # Simple question
    response = client.ask("What is 2 + 2?")
    
    print(f"Response: {response}")
    print("✅ Success! Your Ollama setup is working.")
    print("💡 Make sure Ollama is running: ollama serve")

if __name__ == "__main__":
    main()
