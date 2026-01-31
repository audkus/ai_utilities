#!/usr/bin/env python3
"""
Audio Processing Quickstart

This is a simple quickstart example showing how to use the audio processing
features of AI Utilities.
"""

from pathlib import Path

from ai_utilities import AiClient, AiSettings
from _common import check_env_vars, get_outputs_dir, safe_write_audio


def main():
    """Quickstart demo for audio processing."""
    print("🎤 AI Utilities Audio Processing Quickstart")
    print("=" * 50)
    
    # Check for required environment variables
    missing_vars = check_env_vars(['OPENAI_API_KEY'])
    if missing_vars:
        print("❌ Cannot proceed without API key")
        return
    
    # Initialize the AI client
    print("\n🔧 Initializing AI client...")
    try:
        # Use environment-based settings
        settings = AiSettings()
        client = AiClient(settings)
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print("💡 Make sure you have a valid API key set")
        return
    
    # Example 1: Audio Transcription
    print("\n🎯 Example 1: Audio Transcription")
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
        else:
            print("   ❌ Audio file validation failed")
            for error in validation['errors']:
                print(f"      - {error}")
                
    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
    
    # Example 2: Audio Generation
    print("\n🎯 Example 2: Audio Generation")
    print("-" * 30)
    
    text_to_speak = "Hello! This is AI Utilities generating speech from text."
    print(f"📝 Generating audio for: \"{text_to_speak}\"")
    
    try:
        # Generate audio from text
        audio_data = client.generate_audio(
            text=text_to_speak,
            voice="alloy",  # Available voices: alloy, echo, fable, onyx, nova, shimmer
            model="tts-1",
            speed=1.0
        )
        
        # Save the generated audio safely
        outputs_dir = get_outputs_dir()
        output_file = outputs_dir / "generated_speech.mp3"
        safe_write_audio(output_file, audio_data)
        
        print(f"   📊 Size: {len(audio_data) / 1024:.1f} KB")
        
    except Exception as e:
        print(f"   ❌ Audio generation failed: {e}")
    
    # Example 3: Available Voices
    print("\n🎯 Example 3: Available Voices")
    print("-" * 30)
    
    try:
        voices = client.get_audio_voices()
        print(f"   🎭 Available voices ({len(voices)}):")
        
        for voice in voices:
            print(f"      - {voice['id']}: {voice.get('name', 'Unknown')} ({voice.get('language', 'Unknown')})")
            
    except Exception as e:
        print(f"   ❌ Failed to get voices: {e}")
    
    print("\n🎉 Audio Processing Quickstart Complete!")
    print("\n💡 Next Steps:")
    print("   1. Set your OPENAI_API_KEY environment variable")
    print("   2. Place an audio file named 'demo_audio.wav' in this directory")
    print("   3. Run the script again to see real results")
    print("   4. Check outputs/ directory for generated files")
    print("   5. Check out the other audio examples for more advanced features")


def show_api_info():
    """Show API information and setup instructions."""
    print("\n📚 API Setup Information")
    print("-" * 25)
    print("To use audio processing, you need:")
    print("1. An OpenAI API key with access to:")
    print("   - Whisper API (for transcription)")
    print("   - TTS API (for speech generation)")
    print("2. Set your API key as environment variable:")
    print("   export AI_API_KEY='your-openai-api-key'")
    print("3. Or include it in your code:")
    print("   settings = AiSettings(api_key='your-key')")
    print("\n🔗 Get your API key at: https://platform.openai.com/api-keys")


if __name__ == "__main__":
    main()
    show_api_info()
