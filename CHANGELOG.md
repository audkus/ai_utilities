# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For detailed release notes and process, see [RELEASE.md](docs/RELEASE.md).

## [Unreleased]

## [1.0.0] - 2025-02-13

### Added
- Documentation API contract test suite
- Engineering guarantees section in README
- Provider configuration normalization
- Multi-provider setup documentation
- PyPI prerelease staging workflow with automatic smoke testing
- Enhanced tag detection to prevent accidental matches with suffixes
- Real PyPI pre-releases instead of TestPyPI (due to name similarity restrictions)

### Changed
- Updated default model from gpt-3.5-turbo to gpt-4o-mini
- Clarified documentation boundaries and analysis file handling
- Improved provider configuration examples
- Enhanced PyPI prerelease staging workflow with improved tag detection
- Added smoke testing for prerelease releases
- Improved error handling and retry logic for PyPI publishing

### Fixed
- SSL backend compatibility warnings
- Import-time dependency handling
- Rate limit fetching tests with proper method mocking
- Provider initialization tests with improved error handling
- Environment variable contamination in test isolation

### Security
- Enhanced release workflow permissions for GitHub release creation

## [1.0.0b3] - 2025-02-13

### Added
- PyPI prerelease staging workflow with automatic smoke testing
- Enhanced tag detection to prevent accidental matches with suffixes
- Real PyPI pre-releases instead of TestPyPI (due to name similarity restrictions)

### Fixed
- Rate limit fetching tests with proper method mocking
- Provider initialization tests with improved error handling
- Environment variable contamination in test isolation

## [1.0.0] - 2024-02-10

### Added
- Unified AI provider interface supporting OpenAI, Groq, Together AI, OpenRouter, Ollama, FastChat, Text Generation WebUI, and LM Studio
- Intelligent caching with multiple backends (memory, SQLite, null)
- Rate limiting and usage tracking
- Type-safe configuration with Pydantic
- Async client support
- File operations (upload, download, list)
- Audio transcription support
- Image generation support
- Knowledge base indexing and retrieval
- JSON mode and streaming support
- Comprehensive error handling
- CLI interface
- Extensive test coverage
- Documentation and examples

### Changed
- Migrated from legacy configuration to standardized provider interface
- Improved error messages and debugging information
- Enhanced SSL compatibility checking

### Fixed
- Provider auto-selection logic
- Environment variable precedence
- Cache consistency issues
- Rate limit detection

### Breaking
- Minimum Python version increased to 3.9
- Some legacy configuration options removed (see migration guide)

## [0.x] - Previous Versions

Legacy versions with limited provider support and basic functionality. See migration guide for upgrading to 1.0.0.
