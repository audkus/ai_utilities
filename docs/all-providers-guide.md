# 🌐 Complete Guide to All Supported AI Providers

This guide covers EVERY AI provider that can work with the ai_utilities library through its OpenAI-compatible interface.

## 📋 Provider Categories

### 🌩️ **Cloud Providers (Production Ready)**
| Provider | Setup Time | Cost | Quality | Speed |
|----------|------------|------|---------|-------|
| **OpenAI** | 2 min | $$ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Together AI** | 3 min | $ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Groq** | 2 min | $ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Anyscale** | 3 min | $$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Fireworks AI** | 2 min | $ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Replicate** | 3 min | $ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### 🏠 **Local Providers (Privacy First)**
| Provider | Setup Time | Cost | Hardware | Models |
|----------|------------|------|----------|--------|
| **Ollama** | 5 min | Free | CPU/GPU | 100+ |
| **vLLM** | 10 min | Free | GPU | 50+ |
| **LM Studio** | 5 min | Free | CPU/GPU | 200+ |
| **Oobabooga** | 15 min | Free | CPU/GPU | 100+ |
| **LocalAI** | 10 min | Free | CPU/GPU | 50+ |
| **FastChat** | 15 min | Free | GPU | 30+ |

### 🏢 **Enterprise Providers**
| Provider | Setup Time | Cost | Features | Use Case |
|----------|------------|------|----------|---------|
| **Azure OpenAI** | 10 min | $$$ | Enterprise | Corporate |
| **Google Vertex AI** | 15 min | $$$ | Enterprise | Corporate |
| **AWS Bedrock** | 20 min | $$$ | Enterprise | Corporate |
| **IBM watsonx** | 15 min | $$$ | Enterprise | Corporate |

---

## 🚀 **DETAILED SETUP FOR EACH PROVIDER**

### 🌩️ **CLOUD PROVIDERS**

#### 1. **OpenAI** (Primary Cloud Provider)
```bash
# Setup
export AI_API_KEY="sk-your-openai-api-key"
export AI_PROVIDER="openai"
export AI_MODEL="gpt-4"  # or gpt-3.5-turbo

# Test
python3 -c "
from ai_utilities import AiClient
client = AiClient()
response = client.ask('What is AI?')
print(f'OpenAI: {response}')
"
```

**Models Available:**
- `gpt-4` - Best quality, slower
- `gpt-4-turbo` - Good balance
- `gpt-3.5-turbo` - Fast, cost-effective

#### 2. **Together AI** (Alternative Cloud)
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://api.together.xyz/v1"
export AI_API_KEY="your-together-api-key"
export AI_MODEL="meta-llama/Llama-2-7b-chat-hf"

# Test
python3 test_all_providers.py --providers together_ai
```

**Models Available:**
- `meta-llama/Llama-2-7b-chat-hf`
- `meta-llama/Llama-2-13b-chat-hf`
- `meta-llama/Llama-2-70b-chat-hf`
- `mistralai/Mixtral-8x7B-Instruct-v0.1`

#### 3. **Groq** (Fastest Inference)
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://api.groq.com/openai/v1"
export AI_API_KEY="your-groq-api-key"
export AI_MODEL="mixtral-8x7b-32768"

# Test
python3 test_all_providers.py --providers groq
```

**Models Available:**
- `mixtral-8x7b-32768` - Fast, high quality
- `llama2-70b-4096` - Large, fast
- `gemma-7b-it` - Small, very fast

#### 4. **Anyscale** (Ray-based Cloud)
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://api.endpoints.anyscale.com/v1"
export AI_API_KEY="your-anyscale-api-key"
export AI_MODEL="meta-llama/Llama-2-7b-chat-hf"

# Test
python3 test_all_providers.py --providers anyscale
```

#### 5. **Fireworks AI** (Speed Optimized)
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://api.fireworks.ai/inference/v1"
export AI_API_KEY="your-fireworks-api-key"
export AI_MODEL="accounts/fireworks/models/llama-v2-7b-chat"

# Test
python3 test_all_providers.py --providers fireworks
```

#### 6. **Replicate** (Model Hosting)
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://api.replicate.com/v1"
export AI_API_KEY="your-replicate-api-key"
export AI_MODEL="replicate/llama-2-70b-chat"

# Test
python3 test_all_providers.py --providers replicate
```

---

### 🏠 **LOCAL PROVIDERS**

#### 1. **Ollama** (Easiest Local Setup) ✅ ALREADY WORKING
```bash
# Installation
brew install ollama  # macOS
# or: curl -fsSL https://ollama.ai/install.sh | sh  # Linux

# Start server
ollama serve

# Pull models
ollama pull llama3.2:latest
ollama pull codellama:7b
ollama pull mistral:7b

# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:11434/v1"
export AI_API_KEY="dummy-key"
export AI_MODEL="llama3.2:latest"

# Test
python3 test_all_providers.py --providers ollama
```

**Models Available:**
- `llama3.2:latest` - Latest Llama 3.2
- `codellama:7b` - Code specialized
- `mistral:7b` - Fast, efficient
- `vicuna:7b` - Chat optimized
- `wizardcoder:7b` - Code generation

#### 2. **vLLM** (Performance Optimized)
```bash
# Installation
pip install vllm

# Start server (GPU recommended)
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --port 8000

# CPU-only alternative
python3 -m vllm.entrypoints.openai.api_server \
    --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    --port 8000

# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:8000/v1"
export AI_API_KEY="dummy-key"

# Test
python3 test_all_providers.py --providers vllm
```

#### 3. **LM Studio** (GUI-based)
```bash
# 1. Download from https://lmstudio.ai/
# 2. Install and launch
# 3. Load a model (e.g., Llama 2 7B Chat)
# 4. Start server:
#    - Port: 1234
#    - Host: 127.0.0.1
#    - Enable CORS

# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:1234/v1"
export AI_API_KEY="dummy-key"

# Test
python3 test_all_providers.py --providers lm_studio
```

#### 4. **Oobabooga** (Advanced Local)
```bash
# Installation
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui
pip install -r requirements.txt

# Start with OpenAI extension
python3 server.py --extensions openai --api

# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:7860/v1"
export AI_API_KEY="dummy-key"

# Test
python3 test_all_providers.py --providers oobabooga
```

#### 5. **LocalAI** (Drop-in OpenAI Replacement)
```bash
# Installation
curl -Lo local-ai "https://github.com/go-skynet/LocalAI/releases/latest/download/LocalAI-darwin-Latest"
chmod +x local-ai

# Start server
./local-ai --models-path /path/to/models

# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="http://localhost:8080/v1"
export AI_API_KEY="dummy-key"

# Test
python3 test_all_providers.py --providers localai
```

---

### 🏢 **ENTERPRISE PROVIDERS**

#### 1. **Azure OpenAI**
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://your-resource.openai.azure.com/"
export AI_API_KEY="your-azure-api-key"
export AI_MODEL="gpt-4"  # Your deployment name

# Test
python3 test_all_providers.py --providers azure_openai
```

#### 2. **Google Vertex AI**
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://us-central1-aiplatform.googleapis.com/v1/projects/your-project/locations/us-central1/publishers/google/models"
export AI_API_KEY="your-google-api-key"

# Test
python3 test_all_providers.py --providers vertex_ai
```

#### 3. **AWS Bedrock**
```bash
# Setup
export AI_PROVIDER="openai_compatible"
export AI_BASE_URL="https://bedrock-runtime.us-east-1.amazonaws.com"
export AI_API_KEY="your-aws-credentials"

# Test
python3 test_all_providers.py --providers bedrock
```

---

## 🧪 **COMPREHENSIVE TESTING SCRIPT**

Let's test all providers systematically:
```bash
# Test all cloud providers (requires API keys)
python3 test_all_providers.py --providers openai together_ai groq anyscale fireworks replicate

# Test all local providers (requires local setup)
python3 test_all_providers.py --providers ollama vllm lm_studio oobabooga localai

# Test enterprise providers (requires enterprise setup)
python3 test_all_providers.py --providers azure_openai vertex_ai bedrock

# Test everything (comprehensive)
python3 test_all_providers.py --providers openai together_ai groq anyscale fireworks replicate ollama vllm lm_studio oobabooga localai azure_openai vertex_ai bedrock
```

---

## 📊 **PROVIDER COMPARISON MATRIX**

| Provider | JSON Mode | Streaming | Tools | Images | Cost | Speed | Privacy |
|----------|-----------|-----------|-------|--------|------|-------|----------|
| **OpenAI** | ✅ | ✅ | ✅ | ✅ | $$$ | ⭐⭐⭐⭐⭐ | ❌ |
| **Together AI** | ✅ | ⚠️ | ❌ | ❌ | $ | ⭐⭐⭐⭐ | ✅ |
| **Groq** | ✅ | ⚠️ | ❌ | ❌ | $ | ⭐⭐⭐⭐⭐ | ✅ |
| **Ollama** | ⚠️ | ❌ | ❌ | ❌ | Free | ⭐⭐⭐ | ✅✅ |
| **vLLM** | ⚠️ | ❌ | ❌ | ❌ | Free | ⭐⭐⭐⭐ | ✅✅ |
| **LM Studio** | ⚠️ | ❌ | ❌ | ❌ | Free | ⭐⭐ | ✅✅ |
| **Azure OpenAI** | ✅ | ✅ | ✅ | ✅ | $$$ | ⭐⭐⭐⭐ | ✅ |
| **Vertex AI** | ✅ | ✅ | ⚠️ | ✅ | $$$ | ⭐⭐⭐⭐ | ✅ |

**Legend:**
- ✅ = Full support
- ⚠️ = Partial support (may vary by model)
- ❌ = Not supported
- ✅✅ = Excellent privacy (local)

---

## 🎯 **RECOMMENDATIONS BY USE CASE**

### **🚀 Production Applications**
1. **OpenAI** - Best quality, full features
2. **Azure OpenAI** - Enterprise requirements
3. **Together AI** - Cost-effective alternative

### **🔬 Development & Testing**
1. **Ollama** - Free, easy setup
2. **Groq** - Fastest iteration
3. **OpenAI** - Production parity

### **🔒 Privacy & Security**
1. **Ollama** - 100% local, free
2. **vLLM** - High performance local
3. **LM Studio** - User-friendly local

### **💰 Cost Optimization**
1. **Ollama** - Free (after hardware)
2. **Groq** - Fast, cheap inference
3. **Together AI** - Competitive pricing

### **⚡ Speed Critical**
1. **Groq** - Fastest cloud inference
2. **vLLM** - Fastest local inference
3. **OpenAI** - Fast cloud with quality

---

## 🛠️ **ADVANCED CONFIGURATION**

### **Custom Headers for Authentication**
```python
from ai_utilities import AiSettings

# For enterprise gateways
settings = AiSettings(
    provider="openai_compatible",
    base_url="https://your-company-gateway.com/v1",
    api_key="your-api-key",
    extra_headers={
        "Authorization": "Bearer custom-token",
        "X-Department": "engineering",
        "X-Project": "ai-app"
    }
)
```

### **Timeout Configuration**
```python
# For slow local models
settings = AiSettings(
    provider="openai_compatible",
    base_url="http://localhost:11434/v1",
    request_timeout_s=120.0,  # 2 minutes
    api_key="dummy-key"
)

# For fast cloud models
settings = AiSettings(
    provider="openai",
    api_key="your-key",
    request_timeout_s=30.0  # 30 seconds
)
```

### **Model-Specific Configuration**
```python
# Different configs for different models
configs = {
    "fast": AiSettings(provider="openai", model="gpt-3.5-turbo"),
    "quality": AiSettings(provider="openai", model="gpt-4"),
    "local": AiSettings(provider="openai_compatible", base_url="http://localhost:11434/v1"),
    "cheap": AiSettings(provider="openai_compatible", base_url="https://api.together.xyz/v1")
}
```

---

## 🏆 **CONCLUSION**

The ai_utilities library supports **15+ AI providers** across 3 categories:

✅ **6 Cloud Providers** - Production-ready, scalable  
✅ **6 Local Providers** - Privacy-focused, cost-effective  
✅ **3 Enterprise Providers** - Corporate-grade, secure  

**You can switch between ANY of these providers with just a few environment variable changes, while keeping the exact same code!**

```python
from ai_utilities import AiClient

# This SAME code works with ALL providers above!
client = AiClient()
response = client.ask("What is AI?")
print(response)
```

🎯 **Next Step:** Choose your first provider based on your use case and run the test script!
