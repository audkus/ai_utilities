#!/usr/bin/env python3
"""
Audio Transcription Quickstart

Basic example showing how to transcribe audio files using AI Utilities.
"""

from pathlib import Path
import sys

# === BOOTSTRAP: Ensure ai_utilities is importable from any location ===
script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent.parent

# Add src directory to sys.path if not already there
src_dir = repo_root / "src"
src_dir_str = str(src_dir)
if src_dir_str not in sys.path:
    sys.path.insert(0, src_dir_str)

# Add repo root to sys.path for examples import
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from examples._common import print_header, output_dir, require_env, assets_dir, safe_write_audio
# === END BOOTSTRAP ===

from ai_utilities import AiClient, AiSettings


def main():
    """Quickstart demo for audio transcription."""
    
    print_header("🎤 AI Utilities Audio Transcription Quickstart")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # Initialize the AI client
    print("\n🔧 Initializing AI client...")
    try:
        settings = AiSettings()
        client = AiClient(settings)
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # Transcribe audio file
    print("\n🎯 Example: Audio Transcription")
    print("-" * 30)
    
    # Use asset from examples/assets directory
    audio_file = assets_dir() / "demo_audio.wav"
    print(f"📁 Transcribing audio file: {audio_file}")
    
    # Check if audio file exists
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        print("💡 Make sure demo_audio.wav exists in examples/assets/")
        return 1
    
    try:
        # Validate the audio file first
        validation = client.validate_audio_file(str(audio_file))
        print(f"   Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        
        if validation['valid']:
            # Transcribe the audio
            result = client.transcribe_audio(
                str(audio_file),
                language="en",  # Optional: specify language
                model="whisper-1"
            )
            
            print(f"   ✅ Transcription complete!")
            print(f"   📝 Text: {result['text']}")
            print(f"   🎛️  Model: {result['model_used']}")
            print(f"   ⏱️  Time: {result['processing_time_seconds']:.2f}s")
            print(f"   📊 Words: {result['word_count']}")
            
            # Save transcription to outputs
            script_output_dir = output_dir(Path(__file__))
            output_file = script_output_dir / "transcription_result.txt"
            output_file.write_text(result['text'], encoding='utf-8')
            print(f"   📁 Transcription saved to: {output_file}")
            
        else:
            print("   ❌ Audio file validation failed")
            for error in validation['errors']:
                print(f"      - {error}")
            return 1
                
    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
        return 1
    
    print("\n🎉 Audio Transcription Quickstart Complete!")
    print("\n💡 Next Steps:")
    print("   1. Set your OPENAI_API_KEY environment variable")
    print("   2. Place an audio file in examples/assets/")
    print("   3. Run the script again to see real results")
    print("   4. Check examples/_output/ directory for transcription results")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
