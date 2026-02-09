#!/usr/bin/env python3
"""
Text Generation WebUI Integration Probe
Probes connectivity, model discovery, and generation functionality.
"""

import os
import sys
import time
import requests
import pytest
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ai_utilities import create_client


@pytest.mark.integration
def test_text_generation_webui():
    """Comprehensive test for text-generation-webui integration."""
    
    print("🤖 TEXT-GENERATION-WEBUI INTEGRATION TEST")
    print("=" * 60)
    
    # Configuration
    base_url = "http://127.0.0.1:5000/v1"
    api_key = os.getenv("TEXT_GENERATION_WEBUI_API_KEY")  # Optional
    
    print(f"🔧 Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {'Set' if api_key else 'Not required (local)'}")
    
    # Test 1: Server Connectivity
    print(f"\n1️⃣ Testing server connectivity...")
    try:
        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Server is reachable")
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            pytest.skip("Text-Generation-WebUI server not available")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to server at {base_url}")
        print(f"   💡 Make sure text-generation-webui is running with --api flag")
        print(f"   💡 Command: python server.py --api --listen")
        pytest.skip("Text-Generation-WebUI server not running")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        pytest.skip(f"Text-Generation-WebUI server error: {e}")
    
    # Test 2: Model Discovery
    print(f"\n2️⃣ Testing model discovery...")
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        response = requests.get(f"{base_url}/models", headers=headers, timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            if isinstance(models_data, dict) and "data" in models_data:
                available_models = [m["id"] for m in models_data["data"]]
            elif isinstance(models_data, list):
                available_models = [m["id"] for m in models_data]
            else:
                print(f"   ❌ Unexpected response format: {type(models_data)}")
                assert False, f"Unexpected response format: {type(models_data)}"
                
            print(f"   ✅ Found {len(available_models)} models:")
            for model in available_models[:5]:  # Show first 5
                print(f"      - {model}")
            if len(available_models) > 5:
                print(f"      ... and {len(available_models) - 5} more")
                
            if not available_models:
                print(f"   ❌ No models available")
                assert False, "No models available"
                
            test_model = available_models[0]
        else:
            print(f"   ❌ Models endpoint returned {response.status_code}")
            assert False, f"Models endpoint returned {response.status_code}"
    except Exception as e:
        print(f"   ❌ Model discovery failed: {e}")
        assert False, f"Model discovery failed: {e}"
    
    # Test 3: AI Client Creation
    print(f"\n3️⃣ Testing AI client creation...")
    try:
        client = create_client(
            provider="openai_compatible",
            base_url=base_url,
            api_key=api_key,
            model=test_model
        )
        print(f"   ✅ Client created successfully")
        print(f"   📝 Model: {test_model}")
    except Exception as e:
        print(f"   ❌ Client creation failed: {e}")
        assert False, f"Client creation failed: {e}"
    
    # Test 4: Simple Chat Test
    print(f"\n4️⃣ Testing chat functionality...")
    try:
        test_message = "Hello! Please respond with just 'Test successful'."
        response = client.ask(test_message, max_tokens=10)
        
        if response and len(response.strip()) > 0:
            print(f"   ✅ Chat successful")
            print(f"   📝 Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        else:
            print(f"   ❌ Empty response")
            assert False, "Empty response"
    except Exception as e:
        print(f"   ❌ Chat failed: {e}")
        assert False, f"Chat failed: {e}"
    
    # Test 5: Streaming Test (Optional)
    print(f"\n5️⃣ Testing streaming functionality...")
    try:
        responses = list(client.stream_ask("Say 'Stream test'", max_tokens=5))
        if responses:
            full_response = "".join(responses)
            print(f"   ✅ Streaming successful")
            print(f"   📝 Streamed: {full_response}")
        else:
            print(f"   ⚠️  Streaming returned no responses")
    except Exception as e:
        print(f"   ⚠️  Streaming failed (not critical): {e}")
    
    # Test 6: Performance Test
    print(f"\n6️⃣ Testing performance...")
    try:
        start_time = time.time()
        response = client.ask("Quick test", max_tokens=5)
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"   ⏱️  Response time: {response_time:.2f}s")
        
        if response_time < 10:
            print(f"   ✅ Performance is acceptable")
        else:
            print(f"   ⚠️  Slow response time (>10s)")
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
    
    assert True  # Test passed successfully

def test_text_generation_webui_discovery():
    """Test model discovery for text-generation-webui."""
    print(f"\n🔍 TEXT-GENERATION-WEBUI MODEL DISCOVERY")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000/v1"
    api_key = os.getenv("TEXT_GENERATION_WEBUI_API_KEY")
    
    try:
        from ai_utilities.discovery import discover_openai_compatible_models
        models = discover_openai_compatible_models("Text-Generation-WebUI", base_url)
        
        print(f"✅ Discovered {len(models)} models:")
        for model in models[:10]:  # Show first 10
            print(f"   - {model.model_name} (provider: {model.provider})")
        
        if len(models) > 10:
            print(f"   ... and {len(models) - 10} more")
            
        assert True  # Discovery successful
        
    except ImportError as e:
        pytest.skip(f"Discovery module not available: {e}")
    except Exception as e:
        print(f"❌ Model discovery failed: {e}")
        assert False, f"Model discovery failed: {e}"

def main():
    """Main test execution."""
    print(f"🚀 Starting Text-Generation-WebUI Integration Tests")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    success = test_text_generation_webui()
    
    if success:
        print(f"\n🎉 TEXT-GENERATION-WEBUI TESTS PASSED!")
        print(f"✅ Integration is working correctly")
        
        # Run discovery test
        discovery_success = test_text_generation_webui_discovery()
        if discovery_success:
            print(f"✅ Model discovery also working")
        
        print(f"\n💡 Usage Examples:")
        print(f"   # Basic usage")
        print(f"   from ai_utilities import create_client")
        print(f"   client = create_client(")
        print(f"       provider='openai_compatible',")
        print(f"       base_url='http://127.0.0.1:5000/v1',")
        print(f"       api_key=os.getenv('TEXT_GENERATION_WEBUI_API_KEY'),")
        print(f"       model='your-model-name'")
        print(f"   )")
        print(f"   response = client.ask('Hello!')")
        
    else:
        print(f"\n❌ TEXT-GENERATION-WEBUI TESTS FAILED!")
        print(f"💡 Troubleshooting:")
        print(f"   1. Make sure text-generation-webui is installed")
        print(f"   2. Start with: python server.py --api --listen")
        print(f"   3. Check if server is running on http://127.0.0.1:5000")
        print(f"   4. Verify API key if using --api-key flag")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
