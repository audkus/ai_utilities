#!/usr/bin/env python3
"""
Text-Generation-WebUI API Detection and Setup Helper
Helps find and configure the API endpoint.
"""

import requests
import subprocess
import sys
import time

def check_webui_status():
    """Check if Text-Generation-WebUI web interface is running."""
    try:
        response = requests.get("http://127.0.0.1:7860", timeout=5)
        if response.status_code == 200:
            print("✅ Text-Generation-WebUI web interface is running on port 7860")
            return True
    except:
        pass
    print("❌ Text-Generation-WebUI web interface not found on port 7860")
    return False

def find_api_port():
    """Search for the API port."""
    common_ports = [5000, 5001, 5002, 5003, 8000, 8001, 8080, 8890]
    
    print("🔍 Searching for Text-Generation-WebUI API...")
    
    for port in common_ports:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=2)
            if response.status_code == 200:
                print(f"✅ Found API on port {port}")
                return port
        except:
            continue
    
    print("❌ API not found on common ports")
    return None

def test_api_connection(port):
    """Test the API connection and get model info."""
    try:
        response = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            
            if isinstance(models_data, dict) and "data" in models_data:
                models = models_data["data"]
            elif isinstance(models_data, list):
                models = models_data
            else:
                print("❌ Unexpected response format")
                return False
            
            print(f"✅ API is working! Found {len(models)} models:")
            for i, model in enumerate(models[:5]):  # Show first 5
                model_id = model.get("id", "Unknown")
                print(f"   {i+1}. {model_id}")
            
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more")
            
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    print("🤖 Text-Generation-WebUI API Detection Helper")
    print("=" * 60)
    
    # Check web interface
    if not check_webui_status():
        print("\n💡 To start Text-Generation-WebUI:")
        print("   cd /path/to/text-generation-webui")
        print("   python server.py")
        print("   Then open http://127.0.0.1:7860 in your browser")
        return
    
    # Find API port
    api_port = find_api_port()
    
    if not api_port:
        print("\n❌ API not found. The API server may not be started.")
        print("\n💡 To start the API server:")
        print("   cd /path/to/text-generation-webui")
        print("   python server.py --api --listen")
        print("   # If port 5000 is busy, use:")
        print("   python server.py --api --listen --api-port 5001")
        print("\n🔄 After starting the API, run this script again.")
        return
    
    # Test API connection
    print(f"\n🧪 Testing API connection on port {api_port}...")
    if test_api_connection(api_port):
        print(f"\n🎉 SUCCESS! Text-Generation-WebUI API is working!")
        print(f"\n📝 Configuration for AI Utilities:")
        print(f"   # Add to your .env file:")
        print(f"   TEXT_GENERATION_WEBUI_BASE_URL=http://127.0.0.1:{api_port}/v1")
        print(f"   # TEXT_GENERATION_WEBUI_API_KEY=your-key-here  # Optional")
        
        print(f"\n🚀 Test with AI Utilities:")
        print(f"   python tests/provider_monitoring/test_text_generation_webui.py")
        
        print(f"\n💻 Usage example:")
        print(f"   from ai_utilities import create_client")
        print(f"   client = create_client(")
        print(f"       provider='openai_compatible',")
        print(f"       base_url='http://127.0.0.1:{api_port}/v1',")
        print(f"       model='your-model-name'")
        print(f"   )")
        print(f"   response = client.ask('Hello!')")
    else:
        print(f"\n❌ API found on port {api_port} but not working properly.")

if __name__ == "__main__":
    main()
