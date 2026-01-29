#!/usr/bin/env python3
"""
Script to create test audio files for audio integration tests.
Creates simple WAV files with test audio content using only standard library.
"""

import os
import wave
import math
from pathlib import Path

def create_test_audio_files():
    """Create test audio files for integration testing."""
    
    # Create test_audio directory
    audio_dir = Path("test_audio")
    audio_dir.mkdir(exist_ok=True)
    
    # Create a simple sine wave audio file
    def create_sine_wave(filename, duration=1.0, frequency=440.0, sample_rate=16000):
        """Create a simple sine wave WAV file."""
        # Generate samples
        num_samples = int(sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / sample_rate
            value = int(32767 * math.sin(2 * math.pi * frequency * t))
            # Convert to 16-bit signed integer (little endian)
            samples.append(value & 0xFF)
            samples.append((value >> 8) & 0xFF)
        
        # Write WAV file
        with wave.open(str(filename), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(bytes(samples))
    
    # Create test files
    files_created = []
    
    # Short test file (1 second)
    short_file = audio_dir / "test_short.wav"
    create_sine_wave(short_file, duration=1.0, frequency=440.0)
    files_created.append(short_file)
    
    # Longer test file (3 seconds)  
    long_file = audio_dir / "test_long.wav"
    create_sine_wave(long_file, duration=3.0, frequency=880.0)
    files_created.append(long_file)
    
    # Speech-like frequency range
    speech_file = audio_dir / "test_speech.wav"
    create_sine_wave(speech_file, duration=2.0, frequency=200.0)  # Lower frequency
    files_created.append(speech_file)
    
    print(f"✅ Created {len(files_created)} test audio files:")
    for file in files_created:
        size = file.stat().st_size
        print(f"   - {file.name} ({size} bytes)")
    
    return files_created

def create_mp3_placeholder():
    """Create placeholder MP3 files (since creating real MP3s requires additional libraries)."""
    audio_dir = Path("test_audio")
    
    # Create simple text files with .mp3 extension as placeholders
    # The audio tests will check for file existence but may not actually process the content
    mp3_files = [
        audio_dir / "test.mp3",
        audio_dir / "speech.mp3"
    ]
    
    for mp3_file in mp3_files:
        if not mp3_file.exists():
            mp3_file.write_text(f"Placeholder MP3 file: {mp3_file.name}")
    
    print(f"✅ Created {len(mp3_files)} placeholder MP3 files")
    return mp3_files

if __name__ == "__main__":
    print("🎵 Creating test audio files for integration tests...")
    create_test_audio_files()
    create_mp3_placeholder()
    print("✅ Audio file creation complete!")
