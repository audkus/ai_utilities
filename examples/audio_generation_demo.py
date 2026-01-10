#!/usr/bin/env python3
"""
Audio Generation Demo

This demo shows how to use the AI Utilities audio processing
capabilities to generate speech from text using the enhanced setup system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities.audio import AudioProcessor, AudioFormat
from ai_utilities.client import AiClient


def main():
    """Demonstrate audio generation capabilities."""
    print("🎤 AI Utilities Audio Generation Demo")
    print("=" * 50)
    
    # Initialize client with enhanced setup system
    print("🔧 Initializing AI client with enhanced setup...")
    client = AiClient()
    
    # Initialize the audio processor with the configured client
    processor = AudioProcessor(client=client)
    
    # Demo texts to generate
    demo_texts = [
        {
            "text": "Hello, this is a demonstration of AI-powered text-to-speech synthesis.",
            "voice": "alloy",
            "description": "Standard greeting with alloy voice"
        },
        {
            "text": "Welcome to the future of audio processing with artificial intelligence.",
            "voice": "nova", 
            "description": "Welcome message with nova voice"
        },
        {
            "text": "The quick brown fox jumps over the lazy dog. This pangram tests all letters of the alphabet.",
            "voice": "echo",
            "description": "Pangram with echo voice"
        }
    ]
    
    print(f"📝 Generating {len(demo_texts)} audio samples...")
    
    for i, demo in enumerate(demo_texts, 1):
        print(f"\n🎯 Sample {i}: {demo['description']}")
        print(f"   Voice: {demo['voice']}")
        print(f"   Text: \"{demo['text']}\"")
        
        try:
            # Generate audio
            print("   🔄 Generating audio...")
            result = processor.generate_audio(
                text=demo['text'],
                voice=demo['voice'],
                speed=1.0,
                response_format=AudioFormat.MP3
            )
            
            # Save the generated audio
            output_filename = f"generated_audio_{i}_{demo['voice']}.mp3"
            output_path = Path(output_filename)
            
            result.save_to_file(output_path)
            
            # Display results
            print(f"   ✅ Generated successfully!")
            print(f"   📁 Saved to: {output_path}")
            print(f"   📊 File size: {result.file_size_mb:.2f} MB")
            print(f"   ⏱️  Processing time: {result.processing_time_seconds:.2f} seconds")
            print(f"   🎛️  Model used: {result.model_used}")
            
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
    
    print(f"\n🎉 Audio generation demo completed!")
    print(f"📁 Check the generated audio files in the current directory.")

    # Run additional demos
    demo_voice_variations(client)
    demo_speed_variations(client)
    demo_format_variations(client)
    demo_long_text(client)


def demo_voice_variations(client):
    """Demonstrate different voices with the same text."""
    print("\n🎭 Voice Variations Demo")
    print("=" * 30)
    
    processor = AudioProcessor(client=client)
    
    # Get supported voices
    try:
        voices_info = processor.get_supported_voices()
        if "voices" in voices_info:
            voices = [v["id"] for v in voices_info["voices"]]
        else:
            voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    except:
        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    test_text = "This is a test of different voice synthesizers. Each voice has its own unique characteristics."
    
    print(f"🎤 Testing {len(voices)} different voices...")
    print(f"📝 Text: \"{test_text}\"")
    
    for voice in voices:
        try:
            print(f"\n🎭 Generating with {voice} voice...")
            
            result = processor.generate_audio(
                text=test_text,
                voice=voice,
                speed=1.0,
                response_format=AudioFormat.MP3
            )
            
            output_path = Path(f"voice_comparison_{voice}.mp3")
            result.save_to_file(output_path)
            
            print(f"   ✅ Saved to: {output_path}")
            print(f"   📊 Size: {result.file_size_mb:.2f} MB")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")


def demo_speed_variations(client):
    """Demonstrate different speech speeds."""
    print("\n⚡ Speed Variations Demo")
    print("=" * 30)
    
    processor = AudioProcessor(client=client)
    
    test_text = "This demonstrates how speech speed affects audio generation. Speed ranges from very slow to very fast."
    speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    
    print(f"📝 Text: \"{test_text}\"")
    print(f"🎤 Voice: alloy")
    
    for speed in speeds:
        try:
            print(f"\n⚡ Generating with {speed}x speed...")
            
            result = processor.generate_audio(
                text=test_text,
                voice="alloy",
                speed=speed,
                response_format=AudioFormat.MP3
            )
            
            output_path = Path(f"speed_test_{speed}x.mp3")
            result.save_to_file(output_path)
            
            print(f"   ✅ Saved to: {output_path}")
            print(f"   📊 Size: {result.file_size_mb:.2f} MB")
            print(f"   ⏱️  Time: {result.processing_time_seconds:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")


def demo_format_variations(client):
    """Demonstrate different audio formats."""
    print("\n📁 Format Variations Demo")
    print("=" * 30)
    
    processor = AudioProcessor(client=client)
    
    test_text = "This demo shows different audio formats for speech synthesis."
    formats = [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.FLAC, AudioFormat.OGG]
    
    print(f"📝 Text: \"{test_text}\"")
    print(f"🎤 Voice: alloy")
    
    for format in formats:
        try:
            print(f"\n📁 Generating in {format.value.upper()} format...")
            
            result = processor.generate_audio(
                text=test_text,
                voice="alloy",
                speed=1.0,
                response_format=format
            )
            
            output_path = Path(f"format_test_{format.value}.{format.value}")
            result.save_to_file(output_path)
            
            print(f"   ✅ Saved to: {output_path}")
            print(f"   📊 Size: {result.file_size_mb:.2f} MB")
            print(f"   ⏱️  Time: {result.processing_time_seconds:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")


def demo_long_text(client):
    """Demonstrate generating longer text."""
    print("\n📖 Long Text Demo")
    print("=" * 20)
    
    processor = AudioProcessor(client=client)
    
    long_text = """
    Artificial intelligence has revolutionized the way we interact with technology. 
    From natural language processing to computer vision, AI systems are becoming 
    increasingly sophisticated. Text-to-speech technology, in particular, has made 
    tremendous strides in recent years, enabling more natural and expressive 
    vocal synthesis. This demo showcases the ability to generate longer passages 
    of speech from text, opening up possibilities for audiobooks, podcasts, 
    accessibility features, and much more. The quality and naturalness of 
    synthesized speech continues to improve, making it difficult to distinguish 
    from human speech in many cases.
    """.strip()
    
    print(f"📝 Generating {len(long_text)} characters of text...")
    
    try:
        result = processor.generate_audio(
            text=long_text,
            voice="nova",
            speed=1.0,
            response_format=AudioFormat.MP3
        )
        
        output_path = Path("long_text_demo.mp3")
        result.save_to_file(output_path)
        
        print(f"   ✅ Generated successfully!")
        print(f"   📁 Saved to: {output_path}")
        print(f"   📊 Size: {result.file_size_mb:.2f} MB")
        print(f"   ⏱️  Time: {result.processing_time_seconds:.2f}s")
        print(f"   📝 Characters: {len(long_text)}")
        print(f"   📝 Words: {len(long_text.split())}")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")


if __name__ == "__main__":
    main()
    
    print("\n" + "=" * 50)
    print("🎤 Audio Generation Demo Complete!")
    print("\nGenerated files:")
    print("📁 Various audio samples demonstrating different voices, speeds, and formats")
    print("\nTips:")
    print("1. Listen to the generated files to compare voice characteristics")
    print("2. Try different text content and languages")
    print("3. Experiment with speed settings for different effects")
    print("4. Use different formats based on your needs (MP3 for size, WAV for quality)")
