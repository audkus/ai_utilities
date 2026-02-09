# Local AI Server Setup Guide

This guide provides instructions for setting up local AI servers to enable all integration tests in ai_utilities.

## Overview

ai_utilities supports several local AI providers that you can run on your own machine:

- **Ollama** - Easy-to-use local LLM runner
- **LM Studio** - GUI-based LLM server
- **Text Generation WebUI** - Web interface for running models
- **FastChat** - Open-source chatbot infrastructure

## Quick Setup Commands

### Ollama (Recommended - Easiest)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Download a model (in another terminal)
ollama pull llama3.1

# Test the model
ollama run llama3.1
```

### LM Studio

1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai/)
2. Install and launch the application
3. Search for and download a model (e.g., Llama 3 8B)
4. Start the server with default settings
5. Note the server URL (usually `http://localhost:1234/v1`)

### Text Generation WebUI

```bash
# Clone the repository
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui

# Install dependencies
pip install -r requirements.txt

# Start the web interface
python server.py --api --listen

# Access at http://localhost:5000
```

### FastChat

```bash
# Install FastChat
pip install "fschat[model_worker,webui]"

# Start the controller
python3 -m fastchat.serve.controller

# Start the model worker (in another terminal)
python3 -m fastchat.serve.model_worker --model-path lmsys/vicuna-7b-v1.5

# Start the API server (in another terminal)
python3 -m fastchat.serve.openai_api_server --host localhost --port 8000
```

## Environment Configuration

Add the following to your `.env` file:

```bash
# ===== OLLAMA =====
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1

# ===== LM STUDIO =====
LIVE_LMSTUDIO_MODEL=llama3.1

# ===== TEXT GENERATION WEBUI =====
LIVE_TEXTGEN_MODEL=llama3.1

# ===== FASTCHAT =====
LIVE_FASTCHAT_MODEL=llama3.1
```

## Testing Your Setup

Run the integration tests to verify your local servers are working:

```bash
# Test all local providers
export RUN_LIVE_AI_TESTS=1
python3 -m pytest -m "integration" --run-integration -v -k "ollama or lmstudio or textgen or fastchat"

# Test specific provider
python3 -m pytest tests/test_live_providers.py::TestLiveProviders::test_ollama_live --run-integration -v
```

## Troubleshooting

### Port Conflicts

If you get port conflicts, you can change the default ports:

```bash
# Ollama (uses 11434 by default)
# No easy port change - consider stopping other services using port 11434

# LM Studio (uses 1234 by default)
# Change in LM Studio settings

# Text Generation WebUI (uses 5000 by default)
python server.py --api --listen --port 5001

# FastChat (uses 8000 by default)
python3 -m fastchat.serve.openai_api_server --host localhost --port 8001
```

### Model Not Found

Ensure you've downloaded models:

```bash
# Ollama
ollama pull llama3.1
ollama pull codellama

# For other providers, download models through their respective interfaces
```

### Memory Issues

Local models require significant RAM:

- **7B models**: 8-16GB RAM recommended
- **13B models**: 16-32GB RAM recommended  
- **70B models**: 64GB+ RAM recommended

If you have limited RAM, stick with smaller models like Llama 3 8B.

### Server Not Responding

Check if the server is running:

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check LM Studio
curl http://localhost:1234/v1/models

# Check Text Generation WebUI
curl http://localhost:5000/v1/models

# Check FastChat
curl http://localhost:8000/v1/models
```

## Recommended Models for Testing

### Small Models (8-16GB RAM)
- `llama3.1` (8B) - Good all-around model
- `codellama` (7B) - Good for code tasks
- `mistral` (7B) - Fast and efficient

### Medium Models (16-32GB RAM)
- `llama3.1` (70B) - High quality but resource intensive
- `mixtral` (8x7B) - Good balance of quality and speed

### Large Models (64GB+ RAM)
- `llama3.1` (405B) - State of the art (if you have the hardware!)

## Integration Test Coverage

With local servers set up, you'll unlock these additional integration tests:

- **Ollama tests**: 2 additional tests
- **LM Studio tests**: 2 additional tests  
- **Text Generation WebUI tests**: 2 additional tests
- **FastChat tests**: 2 additional tests
- **Model discovery tests**: 6 additional tests

Total: **12 additional integration tests** passing!

## Security Notes

- Local servers are only accessible from your machine by default
- Be cautious with exposing local servers to the network
- Consider using a firewall if running on a shared machine
- Models downloaded from the internet should be from trusted sources

## Performance Tips

1. **Use SSD storage** for better model loading performance
2. **Allocate sufficient RAM** to avoid swapping
3. **Close other applications** when running large models
4. **Use GPU acceleration** if available (CUDA, Metal, etc.)
5. **Start with smaller models** to verify setup before trying larger ones

## Next Steps

Once your local servers are running:

1. Run the full integration test suite
2. Verify all tests are passing
3. Experiment with different models
4. Try the model discovery and validation features
5. Explore the file upload/download capabilities

Happy testing! 🚀
