# 🎵 Audio Processing Guide

Complete guide to audio processing capabilities in AI Utilities, including transcription, generation, validation, and advanced features.

## 🎯 Overview

AI Utilities provides comprehensive audio processing capabilities with support for:
- **Audio Transcription** - Convert audio to text using OpenAI Whisper
- **Audio Generation** - Generate speech from text using OpenAI TTS
- **Audio Validation** - Validate and analyze audio files
- **Metadata Extraction** - Extract audio metadata with mutagen
- **Format Conversion** - Convert between audio formats with pydub

## 📦 Installation

### Basic Installation
```bash
pip install ai-utilities
```

### With Audio Features
```bash
pip install ai-utilities[audio]
```

### Full Installation (All Features)
```bash
pip install ai-utilities[all]
```

### Optional Dependencies
- **mutagen** - Audio metadata extraction (MP3, FLAC, OGG, M4A)
- **pydub** - Audio format conversion
- **ffmpeg** - Required for pydub (install separately)

```bash
# Install ffmpeg for audio conversion
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## 🚀 Quick Start

### Basic Audio Processing

```python
from ai_utilities import AiClient

# Initialize client
client = AiClient()

# Transcribe audio file
result = client.transcribe_audio("audio.wav")
print(f"Transcription: {result['text']}")

# Generate speech from text
audio_data = client.generate_audio("Hello world!", voice="alloy")
with open("output.mp3", "wb") as f:
    f.write(audio_data)

# Validate audio file
validation = client.validate_audio_file("audio.wav")
print(f"Valid: {validation['valid']}")
```

### Advanced Audio Processing

```python
from ai_utilities.audio import AudioProcessor
from ai_utilities.audio.audio_models import AudioFormat

# Create audio processor
processor = AudioProcessor()

# Load audio with metadata extraction
audio_file = processor.load_audio_file("music.mp3")
print(f"Duration: {audio_file.duration_seconds}s")
print(f"Metadata: {audio_file.metadata}")

# Convert audio format
processor.convert_audio_format(
    "input.wav", 
    "output.mp3", 
    AudioFormat.MP3
)

# Complex workflow: transcribe and generate with different voice
transcription, new_audio = processor.transcribe_and_generate(
    "speech.wav",
    target_voice="nova"
)
```

## 🎤 Audio Transcription

### Basic Transcription

```python
# Simple transcription
result = client.transcribe_audio("podcast.mp3")
print(result['text'])

# With language specification
result = client.transcribe_audio(
    "audio.wav",
    language="en"
)

# With custom prompt for better accuracy
result = client.transcribe_audio(
    "interview.wav",
    prompt="This is a business interview about technology trends."
)
```

### Advanced Transcription Options

```python
# Full transcription with all options
result = client.transcribe_audio(
    audio_file="meeting.wav",
    language="en",
    model="whisper-1",
    prompt="Business meeting transcript",
    temperature=0.1,
    response_format="verbose_json"
)

# Access detailed information
print(f"Text: {result['text']}")
print(f"Language: {result['language']}")
print(f"Duration: {result['duration_seconds']}")
print(f"Word count: {result['word_count']}")

# Access segments if using verbose_json
for segment in result['segments']:
    print(f"{segment['start_time']:.2f}s: {segment['text']}")
```

### Supported Audio Formats

**Input Formats:**
- WAV ✅
- MP3 ✅
- FLAC ✅
- OGG ✅
- M4A ✅
- WEBM ✅

**Response Formats:**
- `json` - Standard response
- `text` - Plain text only
- `srt` - SubRip subtitle format
- `verbose_json` - Detailed with timestamps
- `vtt` - WebVTT subtitle format

## 🔊 Audio Generation

### Basic Speech Generation

```python
# Generate speech
audio_data = client.generate_audio(
    "Hello! This is AI Utilities.",
    voice="alloy"
)

# Save to file
with open("speech.mp3", "wb") as f:
    f.write(audio_data)
```

### Voice Options

```python
# Available voices
voices = client.get_audio_voices()
for voice in voices:
    print(f"{voice['id']}: {voice['name']} ({voice['language']})")

# Generate with different voices
audio_data = client.generate_audio(
    "Welcome to our presentation!",
    voice="nova"  # alloy, echo, fable, onyx, nova, shimmer
)
```

### Advanced Generation Options

```python
# Full control over generation
audio_data = client.generate_audio(
    text="This is a professional presentation.",
    voice="alloy",
    model="tts-1",
    speed=1.0,  # 0.25 to 4.0
    response_format="mp3"  # mp3, opus, aac, flac
)

# Generate with different speeds
slow_audio = client.generate_audio(
    "Speaking slowly and clearly.",
    speed=0.8
)

fast_audio = client.generate_audio(
    "Speaking quickly and efficiently.",
    speed=1.2
)
```

### Supported Output Formats

- **MP3** - Default, good compression
- **OPUS** - Lower latency, web optimized
- **AAC** - Apple devices friendly
- **FLAC** - Lossless quality

## 🔍 Audio Validation

### File Validation

```python
# Basic validation
result = client.validate_audio_file("audio.wav")

if result['valid']:
    print("✅ Valid audio file")
    info = result['file_info']
    print(f"Format: {info['format']}")
    print(f"Size: {info['size_mb']} MB")
    print(f"Duration: {info['duration_seconds']}s")
    print(f"Sample rate: {info['sample_rate']} Hz")
    print(f"Channels: {info['channels']}")
else:
    print("❌ Invalid audio file")
    for error in result['errors']:
        print(f"Error: {error}")
```

### Advanced Validation

```python
from ai_utilities.audio.audio_utils import validate_audio_file

# Validate with detailed output
result = validate_audio_file("music.mp3")

# Check for warnings
if result['warnings']:
    for warning in result['warnings']:
        print(f"Warning: {warning}")

# Validate specific format
from ai_utilities.audio.audio_models import AudioFormat
is_wav = validate_audio_file("audio.wav", expected_format=AudioFormat.WAV)
```

## 📊 Audio Analysis

### Loading Audio Files

```python
from ai_utilities.audio.audio_utils import load_audio_file

# Load with metadata extraction
audio_file = load_audio_file("music.mp3")

print(f"File: {audio_file.file_path}")
print(f"Format: {audio_file.format}")
print(f"Size: {audio_file.file_size_bytes} bytes")
print(f"Duration: {audio_file.duration_seconds}s")
print(f"Sample rate: {audio_file.sample_rate} Hz")
print(f"Channels: {audio_file.channels}")
print(f"Bitrate: {audio_file.bitrate}")
print(f"Metadata: {audio_file.metadata}")
```

### Metadata Extraction

```python
# Extract metadata from various formats
audio_file = load_audio_file("podcast.mp3")

# Common metadata fields
metadata = audio_file.metadata
print(f"Title: {metadata.get('title', 'Unknown')}")
print(f"Artist: {metadata.get('artist', 'Unknown')}")
print(f"Album: {metadata.get('album', 'Unknown')}")
print(f"Genre: {metadata.get('genre', 'Unknown')}")
print(f"Year: {metadata.get('date', 'Unknown')}")

# Technical metadata
print(f"Codec: {metadata.get('codec', 'Unknown')}")
print(f"Bitrate: {metadata.get('bitrate', 'Unknown')}")
```

## 🔄 Format Conversion

### Basic Conversion

```python
from ai_utilities.audio.audio_utils import convert_audio_format
from ai_utilities.audio.audio_models import AudioFormat

# Convert WAV to MP3
convert_audio_format(
    input_file="speech.wav",
    output_file="speech.mp3",
    target_format=AudioFormat.MP3
)

# Convert MP3 to FLAC
convert_audio_format(
    input_file="music.mp3",
    output_file="music.flac",
    target_format=AudioFormat.FLAC
)
```

### Batch Conversion

```python
import os
from pathlib import Path

# Convert all WAV files in directory
input_dir = Path("wav_files")
output_dir = Path("mp3_files")

for wav_file in input_dir.glob("*.wav"):
    output_file = output_dir / f"{wav_file.stem}.mp3"
    convert_audio_format(str(wav_file), str(output_file), AudioFormat.MP3)
    print(f"Converted: {wav_file} -> {output_file}")
```

## 🎭 Complex Workflows

### Transcribe and Generate

```python
from ai_utilities.audio import AudioProcessor

processor = AudioProcessor()

# Transcribe audio and generate with different voice
transcription, new_audio = processor.transcribe_and_generate(
    audio_file="original_speech.wav",
    target_voice="nova",
    translation_prompt="Translate to Spanish and generate speech"
)

print(f"Original: {transcription['text']}")

# Save the new audio
with open("translated_speech.mp3", "wb") as f:
    f.write(new_audio)
```

### Voice Cloning Workflow

```python
# Extract voice characteristics
original_audio = "voice_sample.wav"
transcription = client.transcribe_audio(original_audio)

# Generate new content with same voice characteristics
new_text = "This is new content in the original voice style."
generated_audio = client.generate_audio(
    text=new_text,
    voice="alloy",  # Choose closest match
    speed=1.0
)
```

### Batch Processing

```python
import asyncio
from ai_utilities import AsyncAiClient

async def process_audio_files(file_paths):
    client = AsyncAiClient()
    
    tasks = []
    for file_path in file_paths:
        task = client.transcribe_audio(file_path)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# Process multiple files concurrently
audio_files = ["file1.wav", "file2.mp3", "file3.flac"]
transcriptions = asyncio.run(process_audio_files(audio_files))

for i, result in enumerate(transcriptions):
    print(f"File {i+1}: {result['text'][:100]}...")
```

## 🛠️ Configuration

### Environment Variables

```bash
# OpenAI API (required for audio features)
export OPENAI_API_KEY=your-openai-api-key

# Or use generic API key
export AI_API_KEY=your-openai-api-key
export AI_PROVIDER=openai
```

### Client Configuration

```python
from ai_utilities import AiSettings, AiClient

# Custom configuration
settings = AiSettings(
    api_key="your-key",
    provider="openai",
    model="whisper-1"  # Default transcription model
)

client = AiClient(settings)
```

## ⚠️ Error Handling

### Common Errors and Solutions

```python
from ai_utilities.providers.provider_exceptions import FileTransferError
from ai_utilities.audio.audio_utils import AudioProcessingError

try:
    result = client.transcribe_audio("audio.wav")
except FileTransferError as e:
    print(f"Transcription failed: {e}")
    print("Check your API key and file format")
except AudioProcessingError as e:
    print(f"Audio processing error: {e}")
    print("Check file format and integrity")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Validation Before Processing

```python
# Always validate before processing
def safe_transcribe(audio_file):
    validation = client.validate_audio_file(audio_file)
    
    if not validation['valid']:
        print("Invalid audio file:")
        for error in validation['errors']:
            print(f"  - {error}")
        return None
    
    try:
        return client.transcribe_audio(audio_file)
    except Exception as e:
        print(f"Transcription failed: {e}")
        return None

# Usage
result = safe_transcribe("audio.wav")
if result:
    print(f"Success: {result['text']}")
```

## 📈 Performance Tips

### Optimize for Speed

```python
# Use faster model for quick transcriptions
result = client.transcribe_audio(
    "audio.wav",
    model="whisper-1",  # Only option currently
    temperature=0.0  # Faster processing
)

# Use appropriate response format
result = client.transcribe_audio(
    "audio.wav",
    response_format="json"  # Faster than verbose_json
)
```

### Optimize for Quality

```python
# Use higher temperature for creative content
result = client.transcribe_audio(
    "creative_writing.wav",
    temperature=0.3,
    prompt="Creative writing piece with descriptive language"
)

# Use prompts for better accuracy
result = client.transcribe_audio(
    "technical_video.wav",
    prompt="Technical tutorial about software development"
)
```

### Batch Processing Optimization

```python
# Process files in batches to avoid rate limits
import time
from pathlib import Path

def batch_transcribe(file_paths, batch_size=5):
    results = []
    
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i+batch_size]
        
        for file_path in batch:
            try:
                result = client.transcribe_audio(file_path)
                results.append(result)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
        
        print(f"Processed batch {i//batch_size + 1}")
    
    return results
```

## 🧪 Testing

### Unit Tests

```bash
# Run audio-specific unit tests
python -m pytest tests/test_audio_utils.py -v

# Run audio integration tests (requires API key)
python -m pytest tests/test_audio_integration.py -v
```

### Integration Tests

```bash
# Run integration tests with real API calls
export OPENAI_API_KEY=your-key
python -m pytest tests/test_audio_integration.py::TestAudioProcessingRealAPI -v
```

## 📚 Examples

### Complete Audio Processing Pipeline

```python
from ai_utilities import AiClient
from ai_utilities.audio.audio_utils import load_audio_file, convert_audio_format
from pathlib import Path

def complete_audio_pipeline(input_file):
    client = AiClient()
    
    # 1. Validate input file
    validation = client.validate_audio_file(input_file)
    if not validation['valid']:
        raise ValueError(f"Invalid audio file: {validation['errors']}")
    
    # 2. Load and analyze
    audio_file = load_audio_file(input_file)
    print(f"Loaded: {audio_file.duration_seconds}s of audio")
    
    # 3. Transcribe
    transcription = client.transcribe_audio(input_file)
    print(f"Transcribed: {transcription['text'][:100]}...")
    
    # 4. Generate summary audio
    summary_text = f"Summary: {transcription['text'][:200]}..."
    summary_audio = client.generate_audio(summary_text, voice="nova")
    
    # 5. Convert format if needed
    output_file = Path(input_file).stem + "_summary.mp3"
    with open(output_file, "wb") as f:
        f.write(summary_audio)
    
    print(f"Generated summary: {output_file}")
    return transcription, output_file

# Usage
transcription, summary_file = complete_audio_pipeline("podcast.wav")
```

## 🔧 Advanced Configuration

### Custom Audio Processor

```python
from ai_utilities.audio import AudioProcessor
from ai_utilities import AiSettings

# Custom processor configuration
settings = AiSettings(
    api_key="your-key",
    provider="openai"
)

processor = AudioProcessor(
    client=AiClient(settings),
    default_transcription_model="whisper-1",
    default_tts_model="tts-1"
)

# Use custom processor
result = processor.transcribe_audio("audio.wav")
```

### Model Selection

```python
# Available models for transcription
transcription_models = processor.get_supported_models("transcription")
print("Transcription models:", transcription_models)

# Available models for generation
generation_models = processor.get_supported_models("generation")
print("Generation models:", generation_models)

# Available voices
voices = processor.get_supported_voices()
print("Available voices:", voices)
```

## 📖 Reference

### Audio Formats

```python
from ai_utilities.audio.audio_models import AudioFormat

# Supported formats
formats = [
    AudioFormat.WAV,
    AudioFormat.MP3,
    AudioFormat.FLAC,
    AudioFormat.OGG,
    AudioFormat.M4A,
    AudioFormat.WEBM
]
```

### Voice Options

```python
# Available TTS voices
voices = [
    {"id": "alloy", "name": "Alloy", "language": "en"},
    {"id": "echo", "name": "Echo", "language": "en"},
    {"id": "fable", "name": "Fable", "language": "en"},
    {"id": "onyx", "name": "Onyx", "language": "en"},
    {"id": "nova", "name": "Nova", "language": "en"},
    {"id": "shimmer", "name": "Shimmer", "language": "en"}
]
```

## 🆘 Troubleshooting

### Common Issues

**Issue: "mutagen not available"**
```bash
pip install mutagen
# or
pip install ai-utilities[audio]
```

**Issue: "pydub not available"**
```bash
pip install pydub
# Install ffmpeg for your system
brew install ffmpeg  # macOS
```

**Issue: Audio file too large**
```python
# Split large audio files
from pydub import AudioSegment

audio = AudioSegment.from_mp3("large_file.mp3")
# Split into 10-minute chunks
chunks = [audio[i:i+600000] for i in range(0, len(audio), 600000)]
```

**Issue: Poor transcription quality**
```python
# Use prompts and temperature
result = client.transcribe_audio(
    "audio.wav",
    prompt="Clear speech about technology topics",
    temperature=0.1
)
```

---

**Last Updated**: January 2026  
**Version**: 0.5.0  
**Dependencies**: OpenAI API, mutagen (optional), pydub (optional)
