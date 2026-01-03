# AI Utilities Documentation

Welcome to the AI Utilities documentation! This folder contains detailed guides and documentation for the project.

## 🚦 Public API

The stable public API includes these main imports:

```python
from ai_utilities import (
    AiClient,           # Main synchronous AI client
    AsyncAiClient,      # Asynchronous AI client  
    AiSettings,         # Configuration settings
    create_client,      # Client factory function
    AskResult,          # Response result type
    UploadedFile,       # File upload model
    # Audio processing
    AudioProcessor,     # Audio transcription/generation
    # Usage tracking
    UsageTracker,       # Request usage tracking
    # Utilities
    TokenCounter,       # Token counting utility
)
```

All other objects are considered internal and may change between versions.

## 📚 Available Documentation

### 🏗️ **[Reliability & Maintenance Guide](reliability_guide.md)**
Production deployment, monitoring, and maintenance best practices
- High availability setup with circuit breakers
- Performance monitoring and metrics collection
- Cache management and optimization
- Security considerations and audit logging

### 🔄 **[Migration Guide](../MIGRATION.md)**
Step-by-step migration to AI Utilities v1.0
- Breaking changes and compatibility notes
- Import updates and configuration changes
- Testing checklist and common issues
- Performance improvements in v1.0

### 🎵 [Audio Processing Guide](audio_processing.md)
- Complete audio processing capabilities
- Audio transcription with OpenAI Whisper
- Audio generation with OpenAI TTS
- Audio validation and metadata extraction
- Format conversion and advanced workflows
- Installation and configuration guide

### 🧠 [Smart Caching Guide](caching.md)
- Complete caching system documentation
- Multiple cache backends (null, memory, sqlite)
- Namespace isolation and configuration
- Performance optimization and best practices
- TTL expiration and LRU eviction

### 🔍 [Vector Search Guide](vector_extensions.md)
- Knowledge base and semantic search
- Document indexing and retrieval
- Embedding-based search capabilities
- Integration with AI models

### 🚀 [Testing Setup Guide](testing-setup.md)
- Complete testing setup and configuration
- Provider-specific testing instructions
- Troubleshooting and best practices
- Code examples and usage patterns

### 🧪 [Testing Guide](testing_guide.md)
- Comprehensive testing documentation
- Test categories and selection strategies
- Understanding test output and deselected tests
- Writing tests with cache backends

### 🤖 [All Providers Guide](all-providers-guide.md)
- Comprehensive guide for all 8 AI providers
- Setup instructions for each provider
- Configuration examples and environment variables
- Provider-specific capabilities and limitations

### 🦙 [Ollama Capabilities](ollama-capabilities.md)
- Detailed Ollama integration guide
- Model management and setup
- Performance optimization tips
- Advanced configuration options

## 🏗️ Project Structure

```
ai_utilities/
├── README.md              # Main project documentation
├── docs/                  # This folder - additional documentation
├── src/                   # Source code
├── tests/                 # Test suite
├── examples/              # Usage examples
└── scripts/               # Utility scripts
```

## 🎯 Quick Links

- **Main Project**: [README.md](../README.md)
- **Source Code**: [`src/`](../src/)
- **Examples**: [`examples/`](../examples/)
- **Tests**: [`tests/`](../tests/)

## 📖 Getting Started

1. Read the [main README](../README.md) for project overview
<<<<<<< HEAD
2. Check the [Audio Processing Guide](audio_processing.md) for audio features
3. Follow the [Testing Setup Guide](testing-setup.md) for configuration
4. Check the [All Providers Guide](all-providers-guide.md) for provider setup
5. Explore the [examples](../examples/) for usage patterns
=======
2. Check the [Smart Caching Guide](caching.md) for performance optimization
3. Follow the [Testing Setup Guide](testing-setup.md) for configuration
4. Review the [Testing Guide](testing_guide.md) for test categories
5. Check the [All Providers Guide](all-providers-guide.md) for provider setup
6. Explore the [examples](../examples/) for usage patterns
>>>>>>> feature/smart-caching

## 🤝 Contributing

When adding new documentation:
1. Use clear, descriptive filenames
2. Update this index file
3. Add cross-references where appropriate
4. Follow the existing markdown formatting

---

**Last Updated**: December 2025  
**Project Version**: 1.0.0
