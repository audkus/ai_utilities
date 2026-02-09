#!/usr/bin/env python3
"""
Minimal Audio Example - Quickstart
The simplest possible way to use AI Utilities for audio processing.
"""

import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient

def main():
    print("🎵 Minimal Audio Example")
    print("=" * 40)
    
    # Create client
    client = AiClient()
    
    # Simple transcription
    audio_path = "examples/assets/sample_audio.mp3"
    if os.path.exists(audio_path):
        response = client.transcribe(audio_path)
        print(f"Transcription: {response.text}")
        print("✅ Success! Audio transcription is working.")
    else:
        print("⚠️  Sample audio not found at:", audio_path)
        print("💡 Add an audio file to test transcription.")

if __name__ == "__main__":
    main()
