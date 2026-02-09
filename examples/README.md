# AI Utilities Examples

Welcome to the AI Utilities examples! This directory contains practical examples that demonstrate how to use the library effectively.

## 🚀 Quick Start (Beginner Friendly)

**Perfect for getting started immediately:**

```bash
# Minimal examples - 5 lines of code, instant success
python examples/quickstarts/minimal_openai.py
python examples/quickstarts/minimal_ollama.py
python examples/quickstarts/minimal_groq.py
python examples/quickstarts/minimal_audio.py
```

## 📚 Real-World Recipes

**Practical examples for common use cases:**

```bash
# Audio transcription with automatic saving
python examples/recipes/audio_transcription.py

# Knowledge base creation and searching
python examples/recipes/knowledge_indexing.py

# Image generation with cost tracking
python examples/recipes/image_generation.py

# File upload and management
python examples/recipes/file_operations.py
```

## 📚 Step-by-Step Tutorial

**Learn AI Utilities progressively:**

```bash
# Step 1: Setup and configuration
python examples/tutorial/step_01_setup.py

# Step 2: Client creation and providers
python examples/tutorial/step_02_client.py

# Step 3: Intelligent caching
python examples/tutorial/step_03_caching.py

# Step 4: Advanced features
python examples/tutorial/step_04_advanced.py
```

## 🔧 Advanced Examples

**For experienced users and complex scenarios:**

```bash
# Document processing pipeline
python examples/advanced/document_step_01_extract.py
python examples/advanced/document_step_02_summarize.py
python examples/advanced/document_step_03_transform.py

# Multiple image generation
python examples/advanced/image_generate_multiple.py

# Advanced monitoring
python examples/advanced/metrics_monitoring_advanced.py

# File operations with uploads
python examples/advanced/files_operations.py
```

## 📁 Assets Directory

Sample files used by examples:

- `examples/assets/sample_audio.mp3` - Sample audio for transcription examples
- `examples/assets/sample_document.pdf` - Sample document for processing examples

## 🔧 Configuration

Most examples use environment variables for configuration:

```bash
# Create a .env file:
echo "OPENAI_API_KEY=your-key-here" > .env

# Or set environment variables:
export OPENAI_API_KEY=your-key-here
export GROQ_API_KEY=your-key-here
```

## 🚀 Testing Examples

All examples are designed to work immediately:

```bash
# Quickstarts work without any setup
python examples/quickstarts/minimal_openai.py

# Recipes work with proper configuration
python examples/recipes/audio_transcription.py

# Tutorials work step-by-step
python examples/tutorial/step_01_setup.py
```

## 📚 Documentation

For detailed documentation:

- [Getting Started Guide](docs/user/getting-started.md) - Complete setup and examples
- [Configuration Guide](docs/user/configuration.md) - All environment variables
- [Provider Setup](docs/user/providers.md) - Provider-specific configuration
- [Smart Caching](docs/user/caching.md) - Reduce API costs with caching
- [Audio Processing](docs/user/audio.md) - Complete audio processing guide
- [Metrics and Monitoring](docs/user/metrics.md) - Track performance and usage
- [Troubleshooting Guide](docs/user/troubleshooting.md) - Common issues and solutions

## 🎯 Learning Path

**Recommended progression for new developers:**

1. **Start with quickstarts** - Get immediate success
2. **Try recipes** - Solve real problems
3. **Follow tutorials** - Learn advanced concepts
4. **Explore advanced** - Master the library

## 🔧 Customization

All examples are designed to be easily customizable:

- **Change providers**: Modify the `AiClient()` call
- **Adjust settings**: Use `AiSettings()` for configuration
- **Add logging**: Add print statements for debugging
- **Extend functionality**: Build on the examples

## 🚀 Production Ready

All examples include:

- **Error handling** for missing configuration
- **Output management** with predictable directories
- **Cost tracking** where applicable
- **Graceful degradation** when services are unavailable

## 🎉 Start Exploring!

Choose your starting point and begin your AI Utilities journey:

```bash
# For immediate success
python examples/quickstarts/minimal_openai.py

# For real-world problems
python examples/recipes/audio_transcription.py

# For learning step-by-step
python examples/tutorial/step_01_setup.py
```

Happy coding! 🚀
