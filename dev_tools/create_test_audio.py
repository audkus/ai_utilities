#!/usr/bin/env python3
"""
Script to create local test audio files for development.
Creates simple WAV files using only standard library.

Note: For tests, use committed fixtures in tests/fixtures/audio/
This script is for local development only.
"""

import os
import wave
import math
from pathlib import Path

def create_test_audio_files():
    """Create local test audio files for development."""
    
    # Create gitignored directory for generated files
    audio_dir = Path("tests/.generated/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    print(f"✅ Created {len(files_created)} local test audio files:")
    for file in files_created:
        size = file.stat().st_size
        print(f"   - {file.name} ({size} bytes)")
    
    return files_created

if __name__ == "__main__":
    print("🎵 Creating local test audio files for development...")
    print("Note: For tests, committed fixtures are in tests/fixtures/audio/")
    create_test_audio_files()
    print("✅ Local audio file creation complete!")
