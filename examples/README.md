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
├── _output/             # Generated files (auto-ignored by git)
├── _common.py           # Shared utilities for all examples
└── README.md            # This file
```

## 🎯 Running Examples

### ✨ Universal Execution

All examples can be run from **any location**:

```bash
# From repository root
python examples/quickstarts/text_generate_basic.py

# From examples directory  
cd examples && python quickstarts/text_generate_basic.py

# From script's own folder
cd examples/quickstarts && python text_generate_basic.py

# Using absolute path
python /full/path/to/ai_utilities/examples/quickstarts/text_generate_basic.py
```

### 📂 Output Management

Each example creates its own output directory:
```
examples/_output/<script_name>/
```

- **Automatic**: Scripts create output directories automatically
- **Isolated**: Each script has its own output folder
- **Predictable**: Always know where to find generated files
- **Overrideable**: Set `AI_UTILITIES_EXAMPLES_OUTPUT_DIR` to redirect

### 🔄 Example Categories

#### 🟢 OFFLINE_SAFE Examples
Run without API keys, perfect for learning:
```bash
python examples/quickstarts/metrics_monitoring_basic.py
python examples/quickstarts/usage_tracking_basic.py
```

#### 🔴 REQUIRES_AI_PROVIDER Examples  
Need API keys, fail gracefully without them:
```bash
python examples/quickstarts/text_generate_basic.py
python examples/quickstarts/audio_transcribe_basic.py
python examples/quickstarts/document_basic.py
```

#### 🟡 OPTIONAL_ASSET_REQUIRED Examples
Need additional setup (local servers, etc.):
```bash
python examples/providers/fastchat_basic.py
python examples/providers/text_generation_webui_basic.py
```

## 🎯 Quickstart Examples

### Text Generation
```bash
python examples/quickstarts/text_generate_basic.py
```
Basic Q&A with AI models.
**Requires**: `OPENAI_API_KEY`

### Audio Transcription
```bash
python examples/quickstarts/audio_transcribe_basic.py
```
Transcribe audio files using Whisper.
**Requires**: `OPENAI_API_KEY` + audio file in `examples/assets/`

### Metrics Collection
```bash
python examples/quickstarts/metrics_monitoring_basic.py
```
**OFFLINE_SAFE** - Learn metrics collection without API calls.

### Document Processing
```bash
python examples/quickstarts/document_basic.py
```
Upload and analyze PDF documents.
**Requires**: `OPENAI_API_KEY`

## 🔧 Advanced Examples

### Document Workflow Pipeline
```bash
python examples/advanced/document_step_01_extract.py  # Extract text
python examples/advanced/document_step_02_summarize.py  # Summarize
python examples/advanced/document_step_03_transform.py  # Transform
```

### Multi-Model Image Generation
```bash
python examples/advanced/image_generate_multiple.py
```

### Advanced Metrics with AI Integration
```bash
python examples/advanced/metrics_monitoring_advanced.py
```

## 🌐 Provider Examples

### FastChat Integration
```bash
python examples/providers/fastchat_basic.py
```
Connect to local FastChat server.
**Requires**: FastChat server running locally

### Text Generation WebUI
```bash
python examples/providers/text_generation_webui_basic.py
```
Connect to Text Generation WebUI.
**Requires**: WebUI server running locally

## 🧪 Testing Examples

Run the example test suite:
```bash
pytest tests/examples/ -v
```

Tests validate:
- ✅ Scripts run from any location
- ✅ Proper exit codes (0 for success, 1 for config required)
- ✅ Graceful failure without API keys
- ✅ Output directory creation
- ✅ No network calls in offline mode

## 📝 Asset Management

### Provided Assets
Located in `examples/assets/`:
- `demo_audio.wav` - Sample audio for transcription
- `sample_document.pdf` - Sample PDF for document processing
- `sample_report.pdf` - Another PDF sample

### Using Custom Assets
Replace asset references in scripts:
```python
# Instead of:
audio_file = assets_dir() / "demo_audio.wav"

# Use your own:
audio_file = Path("/path/to/your/audio.wav")
```

## 🔍 Debugging Examples

### Common Issues

1. **Import Errors**: Scripts use bootstrap system - should work from anywhere
2. **Missing API Keys**: Scripts fail gracefully with clear messages
3. **Asset Not Found**: Check `examples/assets/` directory
4. **Permission Issues**: Scripts write to `examples/_output/`

### Environment Override for Testing
```bash
# Redirect outputs to temp directory for testing
export AI_UTILITIES_EXAMPLES_OUTPUT_DIR=/tmp/examples_output
python examples/quickstarts/text_generate_basic.py
```

### Verbose Mode
Scripts show detailed output including:
- ✅ Success indicators
- 📁 Output file locations  
- ❌ Error messages with hints
- ⚠️  Warnings about missing configuration

## 🛠️ Development

### Adding New Examples

1. **Use Bootstrap Template**:
```python
# === BOOTSTRAP: Ensure ai_utilities is importable from any location ===
from pathlib import Path
import sys

script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent.parent
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from examples._common import print_header, output_dir, require_env
# === END BOOTSTRAP ===
```

2. **Follow Output Pattern**:
```python
script_output_dir = output_dir(Path(__file__))
output_file = script_output_dir / "result.txt"
print(f"📁 Output saved to: {output_file}")
```

3. **Handle Configuration Gracefully**:
```python
if not require_env(['OPENAI_API_KEY']):
    print("❌ CONFIGURATION REQUIRED")
    return 1
```

4. **Add Tests**: Update `tests/examples/test_examples_executability.py`

### Lint Configuration
Examples folder has relaxed lint rules for educational value:
- ✅ Print statements allowed
- ✅ Longer lines for readability  
- ✅ sys.path manipulation (bootstrap system)
- 🚫 Production code in `src/` remains strict

## 📚 Further Learning

1. **Start with OFFLINE_SAFE examples** to understand patterns
2. **Configure API keys** for provider examples
3. **Check outputs** in `examples/_output/` after running
4. **Read the code** - examples are well-documented
5. **Run tests** to understand contract validation

## 🤝 Contributing

When adding examples:
- 🟢 Classify as OFFLINE_SAFE if possible
- 🔴 Use graceful failure for REQUIRES_AI_PROVIDER
- 📁 Use `assets_dir()` for required files
- 📝 Write to `output_dir()` for results
- 🧪 Add corresponding tests
- 📖 Update this README

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
