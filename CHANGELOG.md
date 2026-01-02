# Changelog

All notable changes to AI Utilities will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Upcoming

### Added
- **Minimal Install Support** - Core library works without provider SDKs
- **Provider Extras** - Optional dependencies: `pip install ai-utilities[openai]`
- **Lazy Provider Imports** - Providers loaded only when needed
- **Clear Error Messages** - Actionable errors for missing dependencies
- **API Stability Contract** - Explicit v1.x stability guarantees
- **Golden Path Example** - Simple getting started guide
- **Progressive Examples** - Structured learning path from basic to advanced
- **Type Safety Improvements** - Mypy configuration for core modules (52→0 errors)
- **Test Infrastructure** - Fixed all test infrastructure issues
- **Comprehensive CI/CD** - Multi-version, cross-platform testing pipeline
- **Automated Releases** - Tag-based PyPI and GitHub releases
- **Security Monitoring** - Vulnerability scanning and dependency updates
- **Dead Code Cleanup** - Removed 28 unused imports and variables
- **README Clarity** - Added value proposition and competitive analysis
- **Error Handling Guide** - Public exception taxonomy documentation
- **Cache Stability Guarantee** - v1.x cache format and key stability promises
- **Demo Simplification** - Replaced 1100+ line complex demo with focused examples
- **Model Validation Example** - Simple setup testing utility

### Changed
- **Provider Imports** - Now lazy to support minimal installs
- **Installation Options** - Clear separation of core vs optional features
- **Error Handling** - Better messages for missing optional dependencies
- **Test Organization** - All tests now pass with lazy imports
- **Documentation Structure** - Clear progressive learning path
- **Code Quality** - Zero mypy errors and zero dead code issues
- **Import Performance** - Faster imports with minimal dependencies

### Breaking
- None

### Deprecated
- None

### Security
- Added automated vulnerability scanning with safety and bandit
- Implemented dependency freshness monitoring
- Added security scanning to CI pipeline

---

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
- 🧠 **Smart Caching System** - Complete caching infrastructure with multiple backends
- **SQLite Cache Backend** - Persistent caching with namespace isolation and LRU eviction
- **Memory Cache Backend** - Fast in-memory caching with TTL support
- **Namespace Support** - Automatic and custom namespace isolation for multi-project environments
- **Cache Configuration** - Comprehensive cache settings in AiSettings with sensible defaults
- **TTL Expiration** - Automatic cleanup of expired cache entries
- **LRU Eviction** - Memory-efficient cache size management
- **Thread Safety** - Concurrent access support for all cache backends
- **Vector Search System** - Knowledge base with semantic search capabilities
- **Enhanced Installation Options**
  - Optional audio dependencies: `pip install ai-utilities[audio]`
  - Vector search dependencies: `pip install ai-utilities[vector]`
  - Full installation: `pip install ai-utilities[all]`
- **Comprehensive Documentation**
  - Complete audio processing guide (docs/audio_processing.md)
  - Smart caching guide (docs/caching.md)
  - Updated command reference with audio methods
  - Audio examples and cheat sheet entries
- **Testing Infrastructure**
  - 19 unit tests for audio utilities (100% pass rate)
  - 13 integration tests for audio client functionality
  - 19 new tests covering all caching functionality
  - 3 real API integration tests (cost-controlled)
  - Demo audio file for testing (examples/demo_audio.wav)
- **Demo Script** - Interactive demonstration of namespace isolation and sharing
- **Audio Error Handling**
  - Graceful handling of missing optional dependencies
  - Comprehensive validation and error reporting
  - Robust file format checking and MIME type validation

### Changed
- **Test Organization** - Dashboard tests now deselected by default for faster regular test runs
- **Documentation Structure** - Added caching and audio documentation, updated testing guide
- **pytest Configuration** - Updated markers and test selection for better CI/CD experience
- **Pytest Isolation** - SQLite cache disabled by default in tests unless explicit path provided

### Technical Details
- **Cache Backends**: Null (default), Memory, SQLite
- **Database Schema**: Primary key (namespace, key) for guaranteed isolation
- **Performance**: 10-1000x speed improvement for cached responses
- **Memory Usage**: ~100-200 bytes per cached response including metadata
- **API Cost Reduction**: 60-90% fewer API calls in typical usage patterns

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
