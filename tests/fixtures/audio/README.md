# Audio Fixtures

This directory contains committed binary audio fixtures for integration tests.

## Why fixtures are committed

- Avoid runtime dependencies on audio encoders (ffmpeg/lame)
- Ensure deterministic test behavior across environments
- Enable tests to run without external tools in CI
- Provide real, playable audio files for validation

## File descriptions

- `test_short.wav` - 1 second sine wave at 440Hz (16KB)
- `test_long.wav` - 3 seconds sine wave at 880Hz (48KB)
- `test_short.mp3` - 1 second sine wave, low bitrate MP3 (2KB)
- `test_speech.mp3` - 2 seconds speech-like tone, low bitrate MP3 (3KB)

## Size expectations

All fixtures are intentionally small:
- WAV files: uncompressed but short duration
- MP3 files: mono, low bitrate (32kbps), short duration
- Total repository impact: <100KB

## How to replace/regenerate

If fixtures need replacement:

1. Use audio tools (Audacity, ffmpeg, etc.) to create new files
2. Keep them short and small (same parameters as existing)
3. Replace files in this directory
4. Commit the new fixtures

Do not regenerate fixtures during tests or CI. These are static committed assets.
