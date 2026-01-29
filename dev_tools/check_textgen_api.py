#!/usr/bin/env python3
"""
TextGen WebUI API Checker
Checks if API is available and what models are accessible
"""

import requests
import json

def check_textgen_setup():
    base_url = "http://127.0.0.1:7860"
    
    print("🔍 Checking TextGen WebUI API setup...")
    
    # Check web interface
    try:
        response = requests.get(f"{base_url}/", timeout=2)
        if response.status_code == 200:
            print("✅ Web interface is accessible")
    except:
        print("❌ Web interface not accessible")
        return False
    
    # Check common API endpoints
    api_endpoints = [
        "/v1/models",
        "/api/v1/models", 
        "/api/models",
        "/v1/completions"
    ]
    
    api_working = False
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=3)
            if response.status_code == 200:
                print(f"✅ API endpoint working: {endpoint}")
                api_working = True
                
                if "models" in endpoint:
                    data = response.json()
                    if "data" in data and data["data"]:
                        models = [m.get("id", "unknown") for m in data["data"]]
                        print(f"🤖 Available models: {', '.join(models[:3])}")
                        return True
                break
        except:
            continue
    
    if not api_working:
        print("❌ No API endpoints found")
        print("\n💡 You may need to restart TextGen WebUI with API mode:")
        print("   python server.py --api --listen --listen-port 7860")
        return False
    
    return True

if __name__ == "__main__":
    check_textgen_setup()
