#!/usr/bin/env python3
"""
Minimal OpenAI Example - Quickstart
The simplest possible way to use AI Utilities with OpenAI.
"""

import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient

def main():
    print("🚀 Minimal OpenAI Example")
    print("=" * 40)
    
    # Create client (loads from .env automatically)
    client = AiClient()
    
    # Simple question
    response = client.ask("What is 2 + 2?")
    
    print(f"Response: {response}")
    print("✅ Success! Your OpenAI setup is working.")

if __name__ == "__main__":
    main()
