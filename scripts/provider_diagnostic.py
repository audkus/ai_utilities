#!/usr/bin/env python3
"""
Provider Diagnostic Tool

This script helps diagnose and fix "!Model provider unreachable" issues.
It tests connectivity, configuration, and provides specific fix recommendations.
"""

import sys
import os
import requests
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiSettings, create_client
from ai_utilities.demo.validation import validate_model, ModelStatus
from ai_utilities.demo.model_registry import build_catalog


def test_basic_connectivity(url: str, timeout: int = 5) -> dict:
    """Test basic connectivity to a provider URL."""
    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "error": None,
        "response_time": None
    }
    
    try:
        start_time = time.time()
        
        # Try to reach the models endpoint
        if url.endswith("/v1"):
            health_url = url.replace("/v1", "/v1/models")
        else:
            health_url = f"{url}/v1/models"
        
        response = requests.get(health_url, timeout=timeout)
        response_time = time.time() - start_time
        
        result.update({
            "reachable": True,
            "status_code": response.status_code,
            "response_time": response_time
        })
        
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused - server not running"
    except requests.exceptions.Timeout:
        result["error"] = "Connection timeout - server slow or unreachable"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request failed: {e}"
    
    return result


def diagnose_provider_issues():
    """Diagnose provider connectivity issues."""
    print("🔍 AI Utilities Provider Diagnostic Tool")
    print("=" * 50)
    
    # Get current settings
    print("\n📋 Current Configuration:")
    print("-" * 25)
    
    try:
        settings = AiSettings.from_env() if AiSettings.has_env_file() else AiSettings()
        print(f"   Base URL: {settings.base_url}")
        print(f"   Model: {settings.model}")
        print(f"   API Key: {'✅ Set' if settings.api_key else '❌ Not set'}")
        print(f"   Timeout: {settings.timeout}s")
    except Exception as e:
        print(f"   ❌ Error loading settings: {e}")
        return
    
    # Test connectivity
    print(f"\n🌐 Testing Connectivity to {settings.base_url}:")
    print("-" * 45)
    
    connectivity = test_basic_connectivity(settings.base_url)
    
    if connectivity["reachable"]:
        print(f"   ✅ Server reachable!")
        print(f"   📊 Status code: {connectivity['status_code']}")
        print(f"   ⏱️  Response time: {connectivity['response_time']:.2f}s")
        
        if connectivity["status_code"] == 401:
            print("   💡 Server is up but needs authentication")
        elif connectivity["status_code"] == 200:
            print("   💡 Server is fully accessible")
        else:
            print(f"   ⚠️  Unexpected status code: {connectivity['status_code']}")
    else:
        print(f"   ❌ Server unreachable!")
        print(f"   🚫 Error: {connectivity['error']}")
        
        # Provide specific recommendations based on error
        provide_fix_recommendations(settings.base_url, connectivity["error"])
        return
    
    # Test with actual client
    print(f"\n🤖 Testing AI Client:")
    print("-" * 20)
    
    try:
        client = create_client()
        response = client.ask("Hello", max_tokens=10)
        print("   ✅ AI client working!")
        print(f"   📝 Response: {response[:50]}...")
    except Exception as e:
        print(f"   ❌ AI client failed: {e}")
        provide_client_fix_recommendations(e)
    
    # Validate all configured models
    print(f"\n📊 Model Status Overview:")
    print("-" * 25)
    
    models = build_catalog()
    status_counts = {status.value: 0 for status in ModelStatus}
    
    for model in models:
        validation = validate_model(model)
        status_counts[validation.status.value] += 1
        
        # Show problematic models
        if validation.status != ModelStatus.READY:
            print(f"   ❌ {model.display_name}: {validation.status_detail}")
    
    # Summary
    print(f"\n📈 Summary:")
    print("-" * 10)
    for status, count in status_counts.items():
        if count > 0:
            icon = {"ready": "✅", "needs_key": "🔑", "unreachable": "🚫", 
                   "invalid_model": "❌", "error": "💥"}.get(status, "❓")
            print(f"   {icon} {status.title()}: {count}")


def provide_fix_recommendations(url: str, error: str):
    """Provide specific fix recommendations based on the error."""
    print(f"\n💡 Fix Recommendations:")
    print("-" * 20)
    
    if "Connection refused" in error:
        if "11434" in url:
            print("   🔧 Ollama server not running:")
            print("      1. Start Ollama: ollama serve")
            print("      2. Verify: curl http://localhost:11434/v1/models")
        elif "1234" in url:
            print("   🔧 LM Studio server not running:")
            print("      1. Open LM Studio")
            print("      2. Go to Server tab")
            print("      3. Click 'Start Server'")
            print("      4. Verify: curl http://localhost:1234/v1/models")
        elif "5000" in url:
            print("   🔧 text-generation-webui not running:")
            print("      1. Start with API: python server.py --api")
            print("      2. Verify: curl http://localhost:5000/v1/models")
        elif "8000" in url:
            print("   🔧 FastChat not running:")
            print("      1. Start controller: python3 -m fastchat.serve.controller")
            print("      2. Verify: curl http://localhost:8000/v1/models")
        else:
            print("   🔧 Server not running:")
            print(f"      1. Start your AI server at {url}")
            print("      2. Check if port is correct")
            print("      3. Verify firewall isn't blocking the port")
    
    elif "timeout" in error:
        print("   ⏰ Connection timeout:")
        print("      1. Server might be starting up (wait and retry)")
        print("      2. Server might be overloaded")
        print("      3. Network connectivity issues")
        print("      4. Try increasing timeout in settings")
    
    elif "Request failed" in error:
        print("   🌐 Network issue:")
        print("      1. Check internet connection")
        print("      2. Verify URL is correct")
        print("      3. Check DNS settings")
        print("      4. Try different URL format")


def provide_client_fix_recommendations(error: Exception):
    """Provide specific fix recommendations for client errors."""
    print(f"\n💡 Client Fix Recommendations:")
    print("-" * 30)
    
    error_str = str(error).lower()
    
    if "api key" in error_str or "unauthorized" in error_str:
        print("   🔑 API Key Issue:")
        print("      1. Check your API key is correct")
        print("      2. For OpenAI: get key from https://platform.openai.com/api-keys")
        print("      3. Set environment variable: export AI_API_KEY='your-key'")
        print("      4. Or add to .env file: AI_API_KEY=your-key")
    
    elif "model" in error_str:
        print("   🤖 Model Issue:")
        print("      1. Check if model exists on the server")
        print("      2. Try a different model name")
        print("      3. For Ollama: run 'ollama list' to see available models")
        print("      4. For LM Studio: load a model in the interface")
    
    elif "timeout" in error_str:
        print("   ⏰ Timeout Issue:")
        print("      1. Increase timeout in settings")
        print("      2. Server might be slow")
        print("      3. Try with a shorter prompt")
    
    else:
        print("   ❓ General Issue:")
        print("      1. Check server logs for errors")
        print("      2. Verify all settings are correct")
        print("      3. Try with a simple test case")


def test_specific_url(url: str):
    """Test connectivity to a specific URL."""
    print(f"🔍 Testing URL: {url}")
    print("-" * 30)
    
    result = test_basic_connectivity(url)
    
    if result["reachable"]:
        print(f"✅ SUCCESS: Server reachable in {result['response_time']:.2f}s")
        print(f"📊 Status: {result['status_code']}")
    else:
        print(f"❌ FAILED: {result['error']}")
        provide_fix_recommendations(url, result["error"])


def main():
    """Main diagnostic function."""
    if len(sys.argv) > 1:
        # Test specific URL
        url = sys.argv[1]
        test_specific_url(url)
    else:
        # Full diagnostic
        diagnose_provider_issues()
    
    print(f"\n📚 For more help, see: docs/provider_troubleshooting.md")
    print(f"🐛 Report issues at: https://github.com/audkus/ai_utilities/issues")


if __name__ == "__main__":
    main()
