# Provider Troubleshooting Guide

## "!Model provider unreachable" - What it means and how to fix it

### What this error means

The "!Model provider unreachable" message indicates that the AI Utilities library cannot connect to the AI provider's server. This typically happens with:

1. **Local AI servers** (Ollama, LM Studio, FastChat, text-generation-webui)
2. **Self-hosted or custom endpoints**
3. **Network connectivity issues**

The library performs a health check by trying to connect to the provider's `/v1/models` endpoint. If this fails, it marks the provider as "unreachable".

### Common causes and solutions

#### 1. Local AI Server Not Running

**Symptoms:**
- You're using Ollama, LM Studio, or other local AI servers
- The server hasn't been started yet

**Solutions:**

**For Ollama:**
```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/v1/models
```

**For LM Studio:**
1. Open LM Studio
2. Go to the "Server" tab  
3. Click "Start Server"
4. Verify with: `curl http://localhost:1234/v1/models`

**For text-generation-webui:**
```bash
# Start with API enabled
python server.py --api

# Verify with: 
curl http://localhost:5000/v1/models
```

**For FastChat:**
```bash
# Start controller
python3 -m fastchat.serve.controller

# Verify with:
curl http://localhost:8000/v1/models
```

#### 2. Wrong URL or Port

**Symptoms:**
- Server is running but on a different port
- URL configuration is incorrect

**Solutions:**

1. **Check your server's actual URL:**
```bash
# Find what port your server is using
netstat -tulpn | grep :11434  # For Ollama
netstat -tulpn | grep :1234  # For LM Studio
```

2. **Update your configuration:**
```python
# In your code or .env file
AI_BASE_URL=http://localhost:11434/v1  # Adjust port as needed
```

3. **Test the URL manually:**
```bash
curl http://localhost:11434/v1/models
# Should return model list or 401 (server is up)
```

#### 3. Firewall or Network Issues

**Symptoms:**
- Server is running locally but can't be reached
- Remote servers are inaccessible

**Solutions:**

**Local firewall:**
```bash
# Check if port is blocked (macOS/Linux)
sudo lsof -i :11434

# Allow traffic through firewall
# macOS: System Preferences → Security & Privacy → Firewall
# Linux: sudo ufw allow 11434
```

**Network connectivity:**
```bash
# Test basic connectivity
ping localhost
curl -I http://localhost:11434

# For remote servers
ping api.openai.com
curl -I https://api.openai.com/v1/models
```

#### 4. Server Starting Up

**Symptoms:**
- Server was just started and isn't ready yet
- Getting intermittent connection errors

**Solutions:**
```bash
# Wait a few seconds after starting server
sleep 5

# Test again
curl http://localhost:11434/v1/models

# Or add retry logic in your code
import time
import requests

def wait_for_server(url, max_retries=10):
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/v1/models", timeout=2)
            if response.status_code in (200, 401):
                print("Server is ready!")
                return True
        except requests.RequestException:
            pass
        
        print(f"Waiting for server... ({i+1}/{max_retries})")
        time.sleep(2)
    
    return False
```

### Debugging Steps

#### 1. Enable Debug Mode

```python
# Enable debug output to see detailed connection info
from ai_utilities.demo.validation import validate_model

# Add debug=True to see what's happening
result = validate_model(model_def, debug=True)
```

#### 2. Manual Connection Test

```bash
# Test the exact URL the library is trying
curl -v http://localhost:11434/v1/models

# Look for:
# - Connection refused (server not running)
# - Connection timeout (network issues)
# - 401 Unauthorized (server is up but needs auth)
# - 200 OK (everything working)
```

#### 3. Check Server Logs

**Ollama:**
```bash
# Check Ollama logs
ollama logs
```

**LM Studio:**
- Look at the console output in LM Studio
- Check the "Server" tab for error messages

**text-generation-webui:**
- Look at the terminal where you started the server
- Check for error messages about port conflicts

### Configuration Examples

#### Ollama Setup
```python
# .env file
AI_BASE_URL=http://localhost:11434/v1
AI_API_KEY=ollama  # Ollama doesn't need real key
AI_MODEL=llama2

# Python code
from ai_utilities import AiClient, AiSettings

settings = AiSettings(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Required but not used by Ollama
    model="llama2"
)
client = AiClient(settings)
```

#### LM Studio Setup
```python
# .env file
AI_BASE_URL=http://localhost:1234/v1
AI_API_KEY=lm-studio  # LM Studio doesn't need real key
AI_MODEL=your-model-name

# Python code
settings = AiSettings(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
    model="your-model-name"
)
client = AiClient(settings)
```

### Common Port Numbers

| Provider | Default Port | URL Format |
|----------|-------------|------------|
| Ollama | 11434 | `http://localhost:11434/v1` |
| LM Studio | 1234 | `http://localhost:1234/v1` |
| text-generation-webui | 5000 | `http://localhost:5000/v1` |
| FastChat | 8000 | `http://localhost:8000/v1` |
| OpenAI | 443 (HTTPS) | `https://api.openai.com/v1` |
| Groq | 443 (HTTPS) | `https://api.groq.com/openai/v1` |

### Quick Fix Checklist

1. ✅ **Is the server running?**
   ```bash
   ps aux | grep ollama  # or lm-studio, etc.
   ```

2. ✅ **Is it on the right port?**
   ```bash
   netstat -tulpn | grep :11434
   ```

3. ✅ **Can you connect manually?**
   ```bash
   curl http://localhost:11434/v1/models
   ```

4. ✅ **Is the URL correct in your config?**
   ```python
   print(settings.base_url)  # Should match server URL
   ```

5. ✅ **No firewall blocking?**
   ```bash
   # Temporarily disable firewall to test
   # If it works, add permanent rule for your port
   ```

### Getting Help

If you're still having trouble:

1. **Check the demo scripts:**
   ```bash
   # Run integration demo
   python examples/demo_integration.py
   
   # Test setup flow
   python examples/complete_flow_demo.py
   
   # Validate configuration
   python examples/model_validation.py
   ```
   These will show detailed status for all configured providers.

2. **Enable debug logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Test with a simple script:**
   ```python
   from ai_utilities import create_client
   try:
       client = create_client()
       response = client.ask("Hello")
       print("Success:", response)
   except Exception as e:
       print("Error:", e)
   ```

4. **Check the GitHub issues** for similar problems and solutions.

Remember: "unreachable" almost always means the server isn't running or isn't accessible at the configured URL!
