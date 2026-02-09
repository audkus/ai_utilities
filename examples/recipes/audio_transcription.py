#!/usr/bin/env python3
"""
Audio Transcription Recipe
Complete example of transcribing audio files with AI Utilities.
"""

import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, safe_write_bytes
from ai_utilities.audio import AudioProcessor

def main():
    print("🎵 Audio Transcription Recipe")
    print("=" * 50)
    
    # Create client
    client = AiClient()
    
    # Audio file to transcribe
    audio_path = "examples/assets/sample_audio.mp3"
    
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        print("💡 Add an audio file to test transcription.")
        return
    
    print(f"📁 Transcribing: {audio_path}")
    
    # Transcribe the audio
    response = client.transcribe(audio_path)
    
    # Display results
    print(f"📝 Transcription: {response.text}")
    print(f"⏱️  Duration: {response.duration}s")
    print(f"💰 Cost: ${response.cost:.4f}")
    
    # Save transcription
    output_dir = Path(__file__).parent / "_output" / Path(__file__).stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    transcript_file = output_dir / "transcription.txt"
    with open(transcript_file, "w") as f:
        f.write(response.text)
    
    print(f"💾 Saved to: {transcript_file}")
    print("✅ Audio transcription complete!")

if __name__ == "__main__":
    main()
