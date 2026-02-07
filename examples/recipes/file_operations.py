#!/usr/bin/env python3
"""
File Operations Recipe
Complete example of uploading and managing files with AI Utilities.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, UploadedFile
from ai_utilities.audio import AudioProcessor

def main():
    print("📁 File Operations Recipe")
    print("=" * 50)
    
    # Create client
    client = AiClient()
    
    # Upload a text file
    print("📤 Uploading text file...")
    text_content = "This is a sample document for testing file operations."
    text_file = Path(__file__).parent / "_output" / Path(__file__).stem / "sample.txt"
    text_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(text_file, "w") as f:
        f.write(text_content)
    
    uploaded = client.upload_file(str(text_file))
    print(f"✅ Uploaded: {uploaded.name}")
    print(f"   Size: {uploaded.size} bytes")
    
    # Upload an audio file
    audio_path = "examples/assets/sample_audio.mp3"
    if os.path.exists(audio_path):
        print("🎵 Uploading audio file...")
        uploaded_audio = client.upload_file(audio_path)
        print(f"✅ Uploaded: {uploaded_audio.name}")
        print(f"   Size: {uploaded_audio.size} bytes")
    else:
        print("⚠️  Audio file not found for upload example")
    
    # List uploaded files
    print("\n📋 Listing uploaded files:")
    uploaded_files = client.list_uploaded_files()
    for file in uploaded_files:
        print(f"  📄 {file.name} ({file.size} bytes)")
    
    print("✅ File operations complete!")

if __name__ == "__main__":
    main()
