#!/usr/bin/env python3
"""
Audio Transcription Demo

This demo shows how to use the AI Utilities audio processing
capabilities to transcribe audio files to text using the enhanced setup system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities.audio import (
    AudioProcessor,
    load_audio_file,
    validate_audio_file,
    get_audio_info,
)
from ai_utilities.client import AiClient


def main():
    """Demonstrate audio transcription capabilities."""
    print("🎤 AI Utilities Audio Transcription Demo")
    print("=" * 50)
    
    # Initialize client with existing configuration (no interactive setup)
    print("🔧 Initializing AI client with existing configuration...")
    client = AiClient(auto_setup=False)  # Don't trigger interactive setup for demos
    
    # Initialize the audio processor with the configured client
    processor = AudioProcessor(client=client)
    
    # Demo audio file path (you'll need to provide your own)
    audio_file_path = "demo_audio.wav"
    
    print(f"\n📁 Looking for demo audio file: {audio_file_path}")
    
    # Check if demo file exists
    if not Path(audio_file_path).exists():
        print(f"❌ Demo file not found: {audio_file_path}")
        print("\nTo run this demo:")
        print("1. Place an audio file named 'demo_audio.wav' in the current directory")
        print("2. Or modify the audio_file_path variable to point to your file")
        print("3. Supported formats: MP3, WAV, M4A, FLAC, OGG")
        return
    
    # Validate the audio file
    try:
        audio_info = get_audio_info(audio_file_path)
        print(f"✅ Audio file found and validated:")
        print(f"   📊 Size: {audio_info['size_mb']:.2f} MB")
        print(f"   🎵 Duration: {audio_info['duration_seconds']:.1f} seconds")
        print(f"   📋 Format: {audio_info['format']}")
        
        if audio_info['size_mb'] > 25:
            print("⚠️  Warning: File is larger than 25MB, may take longer to process")
            
    except Exception as e:
        print(f"❌ Error validating audio file: {e}")
        return
    
    # Transcribe the audio
    print("\n🎯 Transcribing audio...")
    print("   This may take a few moments depending on file size...")
    
    result = processor.transcribe_audio(
        audio_file_path,
        language="en",  # Optional: specify language
        temperature=0.0,  # Lower temperature for more accurate transcription
        response_format="verbose_json"  # Include timestamps
    )
    
    # Display results
    print("\n📝 Transcription Results:")
    print(f"   Model used: {result.model_used}")
    print(f"   Processing time: {result.processing_time_seconds:.2f} seconds")
    print(f"   Detected language: {result.language or 'Unknown'}")
    print(f"   Word count: {result.word_count}")
    
    if result.text:
        print(f"\n📄 Transcribed Text:")
        print(f"   {result.text}")
    else:
        print("\n⚠️  No transcription text returned")
        if hasattr(result, 'error') and result.error:
            print(f"   Error: {result.error}")
    
    # Show additional demos
    demo_supported_voices(client)
    demo_supported_models(client)


def demo_supported_voices(client):
    """Demonstrate getting supported voices for audio generation."""
    print("\n🎤 Supported Voices Demo")
    print("=" * 30)
    
    processor = AudioProcessor(client=client)
    
    try:
        voices = processor.get_supported_voices()
        print("Available voices for audio generation:")
        
        if "voices" in voices:
            for voice in voices["voices"]:
                print(f"   🎭 {voice['id']}: {voice.get('name', 'Unknown')} ({voice.get('language', 'Unknown')})")
        else:
            print("   Voice information not available")
            
    except Exception as e:
        print(f"❌ Error getting voices: {e}")


def demo_supported_models(client):
    """Demonstrate getting supported models."""
    print("\n🤖 Supported Models Demo")
    print("=" * 30)
    
    processor = AudioProcessor(client=client)
    
    try:
        models = processor.get_supported_models()
        
        print("Supported models:")
        for operation, model_list in models.items():
            print(f"   {operation.capitalize()}:")
            for model in model_list:
                print(f"     🎯 {model}")
                
    except Exception as e:
        print(f"❌ Error getting models: {e}")


if __name__ == "__main__":
    main()
    
    print("\n" + "=" * 50)
    print("🎤 Audio Transcription Demo Complete!")
    print("\nNext steps:")
    print("1. Try with your own audio files")
    print("2. Experiment with different languages")
    print("3. Try audio generation with generate_audio()")
    print("4. Check out the audio generation demo")
