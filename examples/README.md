# 📚 AI Utilities Examples

> **Note**: Examples are tutorial scripts; lint rules may be relaxed for this folder to improve readability and educational value.

## 🚀 Prerequisites

### Installation
```bash
# Install the package with development dependencies
pip install -e ".[dev]"

# Or install with specific providers
pip install ai-utilities[openai]
```

### Required Environment Variables
Most examples require at least one of these:
```bash
# OpenAI (most common)
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Specify provider
export AI_PROVIDER="openai"

# For local providers
export OLLAMA_BASE_URL="http://localhost:11434"
export TEXT_GENERATION_WEBUI_BASE_URL="http://localhost:5000"
```

## 📁 Folder Structure

```
examples/
├── quickstarts/          # Basic examples for getting started
├── advanced/            # Advanced workflows and multi-step processes  
├── providers/           # Provider-specific examples
├── assets/              # Sample files (PDFs, audio, etc.)
├── outputs/             # Generated files (auto-ignored by git)
├── _common.py           # Shared utilities for all examples
└── README.md            # This file
```

## 🎯 Quickstart Examples

### Text Generation
```bash
python quickstarts/text_generate_basic.py
```
Basic Q&A with AI models.

### Image Generation  
```bash
python quickstarts/image_generate_basic.py
```
Generate images from text prompts.

### Audio TTS (Text-to-Speech)
```bash
python quickstarts/audio_tts_basic.py
```
Convert text to speech audio.

### Audio Transcription
```bash
python quickstarts/audio_transcribe_basic.py
```
Transcribe audio files to text.

### File Operations
```bash
python quickstarts/files_upload_basic.py
```
Upload and process files.

### Document Processing
```bash
python quickstarts/document_basic.py
```
Extract and process PDF documents.

### Usage Tracking
```bash
python quickstarts/usage_tracking_basic.py
```
Monitor API usage and tokens.

## 🔧 Advanced Examples

### Audio Voice Variations
```bash
python advanced/audio_tts_voices.py
```
Generate speech with different voices.

### Image Generation (Multiple)
```bash
python advanced/image_generate_multiple.py
```
Generate multiple images with different settings.

### File Operations (Advanced)
```bash
python advanced/files_operations.py
```
Advanced file processing workflows.

### Document Workflow (Multi-step)
```bash
# Step 1: Extract text from PDF
python advanced/document_step_01_extract.py

# Step 2: Summarize the text  
python advanced/document_step_02_summarize.py

# Step 3: Transform to different formats
python advanced/document_step_03_transform.py
```

## 🤖 Provider Examples

### FastChat
```bash
python providers/fastchat_basic.py
```
Use AI Utilities with FastChat local models.

### Text-Generation-WebUI
```bash
python providers/text_generation_webui_basic.py
```
Use AI Utilities with text-generation-webui.

## 📂 Output Files

All generated files are saved to `examples/outputs/`:
- Audio files: MP3, WAV
- Images: PNG, JPEG  
- Text: TXT, JSON
- Documents: Various formats

The `outputs/` directory is automatically ignored by git to prevent committing generated artifacts.

## 🛡️ Error Prevention

The examples include built-in protections:
- **Audio validation**: Prevents saving JSON errors as audio files
- **Format checking**: Validates file headers before saving
- **Safe writing**: Atomic file writes to prevent corruption
- **Clear error messages**: Actionable error reporting

## 💡 Tips for Running Examples

1. **Set environment variables first** - Most examples need API keys
2. **Check outputs/ directory** - Results are saved there, not in the examples folder
3. **Start with quickstarts** - Begin with basic examples before advanced ones
4. **Use sample assets** - Sample files are in `examples/assets/`
5. **Read the comments** - Each example has detailed explanations

## � Troubleshooting

### Common Issues

**"API key required"**
```bash
export OPENAI_API_KEY="your-key-here"
```

**"Cannot import ai_utilities"**
```bash
pip install -e ".[dev]"
```

**"Audio file not found"**
```bash
# Check examples/assets/ for sample files
ls examples/assets/
```

**"Provider not configured"**
```bash
export AI_PROVIDER="openai"
# Or specify your local provider
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Provider Compatibility

| Feature | OpenAI | Local Models | Notes |
|---------|---------|--------------|-------|
| Text Generation | ✅ | ✅ | All providers support |
| Image Generation | ✅ | ❌ | OpenAI only |
| Audio TTS | ✅ | ❌ | OpenAI only |
| Audio Transcription | ✅ | ❌ | OpenAI only |
| File Operations | ✅ | ✅ | All providers support |

## 📖 Need More Help?

- Check individual example files for detailed comments
- Look at `examples/_common.py` for shared utilities
- Review the main project README for full documentation
- Check the project documentation site for comprehensive guides

## 🧪 Testing Examples

### Syntax Validation
```bash
# Compile all examples to check for syntax errors
python -m compileall examples

# Or run the dedicated test suite
pytest -q tests/examples/test_examples_compile.py
```

### Smoke Tests
```bash
# Run smoke tests to ensure examples fail gracefully without API keys
pytest -q tests/examples/test_examples_smoke.py
```

### All Example Tests
```bash
# Run all example-related tests
pytest -q tests/examples/
```

The tests ensure:
- All examples compile without syntax errors
- Examples fail gracefully when environment variables are missing
- No files are modified outside `examples/outputs/` during execution
- Examples follow the expected exit code conventions (0 for success, 2 for missing config)
