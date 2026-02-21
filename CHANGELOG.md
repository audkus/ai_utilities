# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For detailed release notes and process, see [RELEASE.md](docs/RELEASE.md).

## [Unreleased]

### Added
- Interactive CLI setup command (`ai-utilities setup`) for cross-platform provider configuration
- Support for creating and patching .env files with provider selections
- Multi-provider mode with `AI_PROVIDER=auto` and `AI_AUTO_SELECT_ORDER`
- Optional dependency detection and install command guidance
- Cross-platform environment variable setup instructions

### Changed
- **BREAKING**: Auto provider selection now respects `AI_AUTO_SELECT_ORDER` and prefers local providers by default
- **BREAKING**: No silent default to OpenAI when no provider is configured - raises `ProviderConfigurationError` instead
- Updated default provider order to prefer local providers: ollama,lmstudio,groq,openrouter,together,deepseek,openai
- Improved provider resolution with explicit configuration requirements

### Fixed
- Environment variable contamination in provider auto-selection
- Missing provider configuration error messages with clear setup guidance

## [1.0.1] - 2025-02-20

### Added
- Interactive CLI setup workflow for provider configuration
- Cross-platform .env file creation and patching
- Multi-provider auto-selection with configurable order
- Optional dependency detection and install guidance

### Changed
- Auto provider selection respects AI_AUTO_SELECT_ORDER (defaults to local-first)
- Removed silent OpenAI fallback when no provider configured
- Enhanced error messages for missing provider configuration

### Fixed
- Provider configuration precedence and resolution logic
- Environment variable handling in multi-provider setups

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
