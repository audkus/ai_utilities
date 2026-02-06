#!/usr/bin/env python3
"""
Audio Processing Quickstart

This is a simple quickstart example showing how to use the audio processing
features of AI Utilities.
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

from examples._common import print_header, output_dir, require_env, safe_write_audio
# === END BOOTSTRAP ===

from ai_utilities import AiClient, AiSettings


def main() -> int:
    """Quickstart demo for audio processing."""
    
    print_header("🎤 Audio TTS Quickstart")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # Initialize AI client
    print("\n🔧 Initializing AI client...")
    try:
        client = AiClient()
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # Generate speech from text
    print("\n🗣️ Generating speech from text...")
    try:
        text_to_speak = "Hello! This is a test of the AI Utilities text-to-speech functionality. I hope you enjoy this demonstration!"
        
        print(f"   Text: \"{text_to_speak}\"")
        
        # Generate speech
        response = client.generate_speech(
            text=text_to_speak,
            voice="alloy",  # Available voices: alloy, echo, fable, onyx, nova, shimmer
            response_format="mp3"
        )
        
        print("✅ Speech generated successfully!")
        
        # Save to output directory
        script_output_dir = output_dir(Path(__file__))
        audio_file = script_output_dir / "generated_speech.mp3"
        
        safe_write_audio(audio_file, response.content)
        print(f"✅ Audio saved to: {audio_file}")
        
        # Show audio info
        print(f"\n📊 Audio Information:")
        print(f"   Format: MP3")
        print(f"   Voice: alloy")
        print(f"   Text length: {len(text_to_speak)} characters")
        print(f"   File size: {len(response.content)} bytes")
        
    except Exception as e:
        print(f"❌ Speech generation failed: {e}")
        return 1
    
    print(f"\n🎉 Audio TTS demonstration complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
