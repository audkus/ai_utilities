# Changelog

All notable changes to AI Utilities will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 🎵 **Complete Audio Processing System**
  - OpenAI Whisper integration for audio transcription
  - OpenAI TTS integration for speech generation
  - Audio validation and format analysis
  - Metadata extraction with mutagen support
  - Audio format conversion with pydub support
  - Complex workflows (transcribe + generate)
  - Support for WAV, MP3, FLAC, OGG, M4A, WEBM formats
- **Enhanced Installation Options**
  - Optional audio dependencies: `pip install ai-utilities[audio]`
  - Full installation: `pip install ai-utilities[all]`
- **Comprehensive Audio Documentation**
  - Complete audio processing guide (docs/audio_processing.md)
  - Updated command reference with audio methods
  - Audio examples and cheat sheet entries
- **Audio Testing Infrastructure**
  - 19 unit tests for audio utilities (100% pass rate)
  - 13 integration tests for audio client functionality
  - 3 real API integration tests (cost-controlled)
  - Demo audio file for testing (examples/demo_audio.wav)
- **Audio Error Handling**
  - Graceful handling of missing optional dependencies
  - Comprehensive validation and error reporting
  - Robust file format checking and MIME type validation

### Documentation
- Documentation refactoring and cleanup
- Improved README structure and clarity
- Added comprehensive audio processing documentation

## [0.5.0] - 2024-12-29

### Added
- FastChat integration with full monitoring and testing
- Text-Generation-WebUI integration with API support
- Comprehensive provider monitoring system with health checks
- Real-time provider health monitoring with JSON persistence
- Automated change detection and alerting system
- CI/CD integration with GitHub Actions for provider health
- Professional documentation organization in docs/ folder
- Complete setup guides for all 8 providers
- Usage examples for all new providers
- 11 bug prevention tests to prevent regressions
- Live provider discovery tests for all providers
- Response format handling for all provider types

### Changed
- Reorganized documentation structure (moved to docs/ folder)
- Improved environment file organization
- Enhanced .gitignore for better repository hygiene
- Fixed pytest markers and test warnings
- Updated version to 0.5.0 (pre-1.0 development)

### Removed
- Dead code and system files (.DS_Store files)
- Temporary files and unused scripts

### Fixed
- Markdown rendering issues in README
- Test return value warnings
- Environment variable inconsistencies

## [0.4.0] - 2024-12-28

### Added
- OpenAI-compatible provider support
- Multi-provider switching capabilities
- Environment variable configuration
- Provider factory pattern
- Rate limit management
- Usage tracking system
- JSON parsing with repair functionality
- Async client support
- Token counting utilities

### Changed
- Refactored to use Pydantic for configuration
- Improved error handling and validation
- Enhanced provider abstraction

## [0.3.0] - 2024-12-27

### Added
- Basic OpenAI integration
- Simple client interface
- Configuration management
- Initial test suite

## [0.2.0] - 2024-12-26

### Added
- Project foundation
- Basic structure
- Initial setup

## [0.1.0] - 2024-12-25

### Added
- First release
- Core functionality
