#!/usr/bin/env python3
"""
Audio Transcription Demo

This demo shows how to use the AI Utilities audio processing
capabilities to transcribe audio files to text.
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


def main():
    """Demonstrate audio transcription capabilities."""
    print("🎤 AI Utilities Audio Transcription Demo")
    print("=" * 50)
    
    # Initialize the audio processor
    processor = AudioProcessor()
    
    # Demo audio file path (you'll need to provide your own)
    audio_file_path = "demo_audio.wav"
    
    print(f"\n📁 Looking for demo audio file: {audio_file_path}")
    
    # Check if demo file exists
    if not Path(audio_file_path).exists():
        print(f"❌ Demo file not found: {audio_file_path}")
        print("\nTo run this demo:")
        print("1. Place an audio file named 'demo_audio.wav' in this directory")
        print("2. Or modify the audio_file_path variable to point to your audio file")
        print("\nSupported formats: WAV, MP3, FLAC, OGG, M4A, WEBM")
        print("Maximum file size: 25MB")
        return
    
    try:
        # Validate the audio file
        print("\n🔍 Validating audio file...")
        if not validate_audio_file(audio_file_path):
            print("❌ Invalid audio file")
            return
        
        # Get audio information
        print("\n📊 Getting audio file information...")
        audio_info = get_audio_info(audio_file_path)
        print(f"   Format: {audio_info['format']}")
        print(f"   Size: {audio_info['file_size_mb']} MB")
        print(f"   Duration: {audio_info['duration_seconds'] or 'Unknown'} seconds")
        print(f"   Sample rate: {audio_info['sample_rate'] or 'Unknown'} Hz")
        print(f"   Channels: {audio_info['channels'] or 'Unknown'}")
        
        # Validate for transcription
        print("\n✅ Validating for transcription...")
        validation = processor.validate_audio_for_transcription(audio_file_path)
        print(f"   Valid for transcription: {validation['valid']}")
        
        if validation['warnings']:
            print("   Warnings:")
            for warning in validation['warnings']:
                print(f"     ⚠️  {warning}")
        
        if validation['errors']:
            print("   Errors:")
            for error in validation['errors']:
                print(f"     ❌ {error}")
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
        print(f"   Character count: {result.character_count}")
        
        print("\n📄 Transcribed Text:")
        print("-" * 40)
        print(result.text)
        print("-" * 40)
        
        # Show segments if available
        if result.segments:
            print(f"\n⏰ Timestamped Segments ({len(result.segments)}):")
            for i, segment in enumerate(result.segments[:5]):  # Show first 5 segments
                start_min, start_sec = divmod(int(segment.start_time), 60)
                end_min, end_sec = divmod(int(segment.end_time), 60)
                print(f"   [{i+1}] {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}")
                print(f"       {segment.text}")
            
            if len(result.segments) > 5:
                print(f"   ... and {len(result.segments) - 5} more segments")
        
        print("\n✅ Transcription completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API key is set: export AI_API_KEY='your-key'")
        print("2. Ensure the audio file is in a supported format")
        print("3. Verify the file size is under 25MB")
        print("4. Check your internet connection")


def demo_supported_voices():
    """Demonstrate getting supported voices for audio generation."""
    print("\n🎤 Supported Voices Demo")
    print("=" * 30)
    
    processor = AudioProcessor()
    
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


def demo_supported_models():
    """Demonstrate getting supported models."""
    print("\n🤖 Supported Models Demo")
    print("=" * 30)
    
    processor = AudioProcessor()
    
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
    
    # Show additional demos
    demo_supported_voices()
    demo_supported_models()
    
    print("\n" + "=" * 50)
    print("🎤 Audio Transcription Demo Complete!")
    print("\nNext steps:")
    print("1. Try with your own audio files")
    print("2. Experiment with different languages")
    print("3. Try audio generation with generate_audio()")
    print("4. Check out the audio generation demo")
