# 📚 AI Utilities Examples

## 🌟 Start Here: Getting Started

**File**: `getting_started.py`  
**This is the recommended starting point for all new users.**

Shows the simplest workflow:
- Install and import
- Create a client
- Ask a question with caching
- Handle the response

```python
from ai_utilities import AiClient

client = AiClient()
result = client.ask(
    "Explain dependency injection in one paragraph",
    cache_namespace="docs"
)
print(result.text)
```

## 📈 Progressive Learning Path

### Level 1: Basics
- `getting_started.py` - **Start here** - Simple Q&A
- `model_validation.py` - **Test your setup** - Validate AI configuration
- `simple_image_generation.py` - Basic image generation
- `files_quickstart.py` - File upload/download

### Level 2: Common Patterns  
- `ask_parameters_demo.py` - Different response formats
- `environment_isolation_example.py` - Environment configuration
- `usage_tracking_example.py` - Monitor token usage

### Level 3: Advanced Features
- `knowledge_example.py` - Knowledge base integration
- `document_ai_demo.py` - Document processing
- `parallel_usage_tracking_example.py` - Concurrent operations

### Level 4: Specialized
- `audio_*.py` - Audio processing (transcription, generation)
- `image_generation_demo.py` - Advanced image workflows
- `complete_content_workflow.py` - Full production pipeline

## 🎯 Quick Reference

| Need | Example | Description |
|------|---------|-------------|
| **First steps** | `getting_started.py` | Simple Q&A with caching |
| **Setup testing** | `model_validation.py` | Validate AI configuration |
| **Images** | `simple_image_generation.py` | Generate images from text |
| **Files** | `files_quickstart.py` | Upload/download files |
| **Audio** | `audio_quickstart.py` | Transcribe/generate audio |
| **Documents** | `simple_document_ai.py` | Process PDFs/Docs |
| **Configuration** | `environment_isolation_example.py` | Environment setup |
| **Monitoring** | `usage_tracking_example.py` | Track token usage |

## 💡 Tips

1. **Always use `cache_namespace`** for examples and documentation
2. **Check `result.usage`** to monitor token consumption  
3. **Use `AiSettings`** for explicit configuration
4. **Handle exceptions** - see error handling examples
5. **Start simple** - don't jump to advanced examples immediately

## 🔧 Environment Setup

Most examples require:
```bash
# Basic install
pip install ai-utilities

# With providers (recommended for examples)
pip install ai-utilities[openai]

# Set your API key
export OPENAI_API_KEY="your-api-key"
```

## 📖 Need More?

- Check the main README for detailed documentation
- Look at individual examples for specific features
- Each example file has detailed comments and explanations
