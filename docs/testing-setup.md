# 🧪 Multi-Provider AI Testing Setup Guide

This guide helps you set up local AI servers and cloud AI services for comprehensive testing of the ai_utilities library.

## 📋 Testing Matrix

| Provider | Setup Type | Purpose | Test Commands |
|----------|------------|---------|---------------|
| **OpenAI** | Cloud API | Production validation | `AI_PROVIDER=openai AI_API_KEY=...` |
| **Ollama** | Local Server | Local AI testing | `AI_PROVIDER=openai_compatible AI_BASE_URL=http://localhost:11434/v1` |
| **vLLM** | Local Server | Performance testing | `AI_PROVIDER=openai_compatible AI_BASE_URL=http://localhost:8000/v1` |
| **LM Studio** | Local Server | GUI-based testing | `AI_PROVIDER=openai_compatible AI_BASE_URL=http://localhost:1234/v1` |
| **Together AI** | Cloud API | Alternative cloud | `AI_PROVIDER=openai_compatible AI_BASE_URL=https://api.together.xyz/v1` |

---

## 🌩️ 1. OpenAI Cloud Setup (Production)

### Installation
```bash
# Already installed with pip install ai-utilities
pip install openai
```

### Configuration
```bash
export AI_API_KEY="sk-your-openai-api-key"
export AI_PROVIDER="openai"
export AI_MODEL="gpt-4"  # or gpt-3.5-turbo for cost savings
```

### Test
```bash
python3 -c "
from ai_utilities import AiClient
client = AiClient()
response = client.ask('What is 2+2?')
print(f'OpenAI Response: {response}')
"
```

---

## 🦙 2. Ollama Local Setup (Recommended for Local Testing)

### Installation
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai/download
```

### Start Ollama
```bash
ollama serve
# Runs on http://localhost:11434
```

### Pull Models
```bash
# Small model for testing
ollama pull llama2:7b

# Medium model
ollama pull codellama:7b

# Large model (if you have RAM)
ollama pull llama2:13b
```

### Configuration
```bash
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:11434/v1"
export AI_API_KEY="dummy-key"  # Not required for Ollama
export AI_MODEL="llama2"
```

### Test
```bash
python3 -c "
from ai_utilities import AiClient
client = AiClient()
response = client.ask('What is 2+2?')
print(f'Ollama Response: {response}')
"
```

---

## ⚡ 3. vLLM Local Setup (Performance Testing)

### Installation
```bash
pip install vllm
```

### Start vLLM Server
```bash
# Basic server
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --port 8000

# With GPU (if available)
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.8 \
    --port 8000
```

### Configuration
```bash
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:8000/v1"
export AI_API_KEY="dummy-key"
export AI_MODEL="meta-llama/Llama-2-7b-chat-hf"
```

### Test
```bash
python3 -c "
from ai_utilities import AiClient
client = AiClient()
response = client.ask('What is 2+2?')
print(f'vLLM Response: {response}')
"
```

---

## 🖥️ 4. LM Studio Setup (GUI-based Local AI)

### Installation
1. Download from https://lmstudio.ai/
2. Install and launch LM Studio
3. Load a model (e.g., Llama 2 7B Chat)
4. Start server with:
   - Port: 1234
   - Host: 127.0.0.1
   - CORS: Enabled

### Configuration
```bash
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:1234/v1"
export AI_API_KEY="dummy-key"
export AI_MODEL="local-model"  # Use whatever model you loaded
```

### Test
```bash
python3 -c "
from ai_utilities import AiClient
client = AiClient()
response = client.ask('What is 2+2?')
print(f'LM Studio Response: {response}')
"
```

---

## 🔗 5. Together AI Cloud Setup (Alternative Cloud)

### Installation
```bash
pip install openai  # Uses OpenAI SDK with different base URL
```

### Get API Key
1. Sign up at https://together.ai/
2. Get API key from dashboard

### Configuration
```bash
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://api.together.xyz/v1"
export AI_API_KEY="your-together-api-key"
export AI_MODEL="meta-llama/Llama-2-7b-chat-hf"
```

### Test
```bash
python3 -c "
from ai_utilities import AiClient
client = AiClient()
response = client.ask('What is 2+2?')
print(f'Together AI Response: {response}')
"
```

---

## 🧪 Comprehensive Testing Commands

### Test All Providers
```bash
# 1. OpenAI (Cloud)
echo "Testing OpenAI..."
export AI_PROVIDER="openai"
export AI_API_KEY="sk-your-openai-key"
python3 -m pytest tests/test_real_api_integration.py::test_openai_real_api_call -v -s

# 2. Ollama (Local)
echo "Testing Ollama..."
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:11434/v1"
export AI_API_KEY="dummy-key"
python3 -m pytest tests/test_real_api_integration.py::test_openai_compatible_real_api -v -s

# 3. vLLM (Local)
echo "Testing vLLM..."
export AI_BASE_URL="http://localhost:8000/v1"
python3 -m pytest tests/test_real_api_integration.py::test_openai_compatible_real_api -v -s

# 4. LM Studio (Local)
echo "Testing LM Studio..."
export AI_BASE_URL="http://localhost:1234/v1"
python3 -m pytest tests/test_real_api_integration.py::test_openai_compatible_real_api -v -s

# 5. Together AI (Cloud)
echo "Testing Together AI..."
export AI_BASE_URL="https://api.together.xyz/v1"
export AI_API_KEY="your-together-key"
python3 -m pytest tests/test_real_api_integration.py::test_openai_compatible_real_api -v -s
```

### Performance Comparison
```bash
# Test response times across providers
python3 -c "
import time
from ai_utilities import AiClient, AiSettings

providers = [
    ('OpenAI', {'provider': 'openai', 'api_key': 'sk-your-key', 'model': 'gpt-3.5-turbo'}),
    ('Ollama', {'provider': 'openai_compatible', 'base_url': 'http://localhost:11434/v1', 'api_key': 'dummy-key', 'model': 'llama2'}),
    ('vLLM', {'provider': 'openai_compatible', 'base_url': 'http://localhost:8000/v1', 'api_key': 'dummy-key', 'model': 'llama2'}),
]

for name, config in providers:
    try:
        client = AiClient(AiSettings(**config))
        start = time.time()
        response = client.ask('What is the capital of France?')
        duration = time.time() - start
        print(f'{name}: {duration:.2f}s - {response[:50]}...')
    except Exception as e:
        print(f'{name}: ERROR - {e}')
"
```

---

## 🔧 Troubleshooting

### Common Issues

**Ollama connection refused:**
```bash
# Make sure Ollama is running
ollama serve
# Check if port is accessible
curl http://localhost:11434/api/tags
```

**vLLM model not found:**
```bash
# Download model first
pip install huggingface_hub
python3 -c \"from huggingface_hub import snapshot_download; snapshot_download('meta-llama/Llama-2-7b-chat-hf')\"
```

**CORS errors with LM Studio:**
1. Open LM Studio
2. Go to Server tab
3. Enable "Allow Cross-Origin Requests"
4. Restart server

**Memory issues with large models:**
```bash
# Use smaller models
export AI_MODEL="llama2:7b"  # Instead of 13b or 70b
# Or use quantized models
export AI_MODEL="llama2:7b-chat-q4_K_M"
```

---

## 📊 Testing Checklist

- [ ] **OpenAI Cloud**: API key works, basic requests succeed
- [ ] **Ollama Local**: Server running, models downloaded, requests work
- [ ] **vLLM Local**: Server starts, model loads, performance is good
- [ ] **LM Studio**: GUI running, server enabled, requests work
- [ ] **Together AI**: API key works, alternative cloud provider functional
- [ ] **Provider Switching**: Can switch between providers without code changes
- [ ] **Error Handling**: Proper errors for missing config, invalid URLs
- [ ] **Performance**: Response times acceptable for each provider
- [ ] **JSON Mode**: Works where supported, graceful degradation where not
- [ ] **Custom Headers**: Can add authentication headers for gateways

---

## 🚀 Next Steps

1. **Start with Ollama** (easiest local setup)
2. **Test OpenAI** (production validation)
3. **Add vLLM** (performance testing)
4. **Try Together AI** (alternative cloud)
5. **Performance comparison** across all providers

This comprehensive setup ensures your multi-provider AI library works reliably across all major AI platforms! 🎯
