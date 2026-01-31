#!/usr/bin/env python3
"""
Audio Transcription Quickstart

Basic example showing how to transcribe audio files using AI Utilities.
"""

from pathlib import Path

from ai_utilities import AiClient, AiSettings
from _common import check_env_vars, get_outputs_dir


def main():
    """Quickstart demo for audio transcription."""
    print("🎤 AI Utilities Audio Transcription Quickstart")
    print("=" * 50)
    
    # Check for required environment variables
    missing_vars = check_env_vars(['OPENAI_API_KEY'])
    if missing_vars:
        print("❌ Cannot proceed without API key")
        return
    
    # Initialize the AI client
    print("\n🔧 Initializing AI client...")
    try:
        settings = AiSettings()
        client = AiClient(settings)
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Transcribe audio file
    print("\n🎯 Example: Audio Transcription")
    print("-" * 30)
    
    audio_file = "demo_audio.wav"  # Replace with your audio file
    print(f"📁 Transcribing audio file: {audio_file}")
    
    try:
        # Validate the audio file first
        validation = client.validate_audio_file(audio_file)
        print(f"   Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        
        if validation['valid']:
            # Transcribe the audio
            result = client.transcribe_audio(
                audio_file,
                language="en",  # Optional: specify language
                model="whisper-1"
            )
            
            print(f"   ✅ Transcription complete!")
            print(f"   📝 Text: {result['text']}")
            print(f"   🎛️  Model: {result['model_used']}")
            print(f"   ⏱️  Time: {result['processing_time_seconds']:.2f}s")
            print(f"   📊 Words: {result['word_count']}")
            
            # Save transcription to outputs
            outputs_dir = get_outputs_dir()
            output_file = outputs_dir / "transcription_result.txt"
            output_file.write_text(result['text'], encoding='utf-8')
            print(f"   📁 Transcription saved to: {output_file}")
            
        else:
            print("   ❌ Audio file validation failed")
            for error in validation['errors']:
                print(f"      - {error}")
                
    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
    
    print("\n🎉 Audio Transcription Quickstart Complete!")
    print("\n💡 Next Steps:")
    print("   1. Set your OPENAI_API_KEY environment variable")
    print("   2. Place an audio file named 'demo_audio.wav' in this directory")
    print("   3. Run the script again to see real results")
    print("   4. Check outputs/ directory for transcription results")


if __name__ == "__main__":
    main()
